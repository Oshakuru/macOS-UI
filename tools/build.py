"""Build the macOS UI resource pack from design tokens + the vanilla reference.

Usage:
    python3 tools/extract_vanilla.py path/to/minecraft-1.21.11-client.jar   # once
    python3 tools/build.py                                                  # -> dist/

Optional: python3 tools/build.py <vanilla_reference_root> <out_dir>
Produces the pack as a folder and a zip in dist/.
Every colour and radius comes from design/tokens.json.
"""
import json, math, os, shutil, sys, zipfile
from collections import Counter, deque
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOK = json.load(open(os.path.join(REPO, 'design', 'tokens.json')))
REF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'reference', 'vanilla-1.21.11')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, 'dist')
VAN = os.path.join(REF, 'assets', 'minecraft', 'textures', 'gui')
if not os.path.isdir(VAN):
    sys.exit(f'Vanilla reference not found at {REF}. Run tools/extract_vanilla.py first.')


def col(name):
    h = TOK[name].lstrip('#')
    a = int(h[6:8], 16) if len(h) == 8 else 255
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def inset(r, k):
    return round(r - math.sqrt(r * r - (r - k - 0.5) ** 2))


def rrect(im, x, y, w, h, r, c, mode='set'):
    """Pixel rounded rectangle (curved staircase corners)."""
    for i in range(h):
        k = min(i, h - 1 - i)
        ins = inset(r, k) if k < r else 0
        for j in range(x + ins, x + w - ins):
            if 0 <= j < im.width and 0 <= y + i < im.height:
                im.putpixel((j, y + i), c if mode == 'set' else (0, 0, 0, 0))


def hline(im, x, y, w, c, r=0, h=None):
    """Horizontal line that respects the rounded shape of a box of radius r."""
    im_w = im.width
    for j in range(x, x + w):
        if 0 <= j < im_w:
            im.putpixel((j, y), c)


def panel_box(im, x, y, w, h):
    r = TOK['radius.panel']
    rrect(im, x, y, w, h, r, col('panel.edge'))
    rrect(im, x + 1, y + 1, w - 2, h - 2, r - 1, col('panel.fill'))
    hline(im, x + r, y + 1, w - 2 * r, col('panel.highlight'))
    hline(im, x + r, y + h - 2, w - 2 * r, col('panel.shade'))


def well(im, x, y, w, h, r=None):
    """Recessed slot/well. (x,y,w,h) is the full frame box incl. 1px edge."""
    r = TOK['radius.slot'] if r is None else r
    if TOK.get('slot.style') == 'tile':
        # flat tile filling only the item area; the 1px frame ring becomes panel gutter
        rrect(im, x + 1, y + 1, w - 2, h - 2, r, col('slot.tile'))
        return
    rrect(im, x, y, w, h, r, col('slot.edge'))
    rrect(im, x + 1, y + 1, w - 2, h - 2, max(r - 1, 0), col('slot.fill'))
    hline(im, x + 2, y + 1, w - 4, col('slot.inner_shadow'))


# ---------------------------------------------------------------- inventory.png
def components(im, rgb, alpha=255):
    w, h = im.size
    seen = set(); comps = []
    px = im.load()
    for yy in range(h):
        for xx in range(w):
            if (xx, yy) in seen: continue
            p = px[xx, yy]
            if p[:3] != rgb or p[3] != alpha: continue
            q = deque([(xx, yy)]); seen.add((xx, yy)); pts = []
            while q:
                a, b = q.popleft(); pts.append((a, b))
                for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (a + da, b + db)
                    if 0 <= n[0] < w and 0 <= n[1] < h and n not in seen and px[n][:3] == rgb and px[n][3] == alpha:
                        seen.add(n); q.append(n)
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            comps.append((min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, len(pts), pts))
    return comps


def is_framed(im, x, y, w, h):
    """True if the box is ringed by vanilla slot frame colours (#373737 top/left, #FFFFFF bottom/right)."""
    px = im.load()
    try:
        top = all(px[i, y - 1][:3] == (0x37, 0x37, 0x37) for i in range(x, x + w))
        left = all(px[x - 1, j][:3] == (0x37, 0x37, 0x37) for j in range(y, y + h))
        bot = all(px[i, y + h][:3] == (0xFF, 0xFF, 0xFF) for i in range(x, x + w))
        right = all(px[x + w, j][:3] == (0xFF, 0xFF, 0xFF) for j in range(y, y + h))
    except IndexError:
        return False
    return top and left and bot and right


def repaint_container(path, glass=True):
    """Generic container restyle: keeps the vanilla canvas, panel bounds and every slot position.
    - panel bounds -> rounded light panel
    - framed #8B8B8B areas (slots, scroll tracks) -> flat tiles
    - framed black areas (player preview) -> Liquid Glass
    - large unframed #8B8B8B areas (creative search field, white text) -> dark field
    - small unframed #8B8B8B shapes (arrows) -> glyph colour
    - creative "destroy item" slot (#AB7F7F) -> red-tinted tile with an X
    """
    src = Image.open(path).convert('RGBA')
    out = Image.new('RGBA', src.size, (0, 0, 0, 0))
    bx0, by0, bx1, by1 = src.getchannel('A').getbbox()
    panel_box(out, bx0, by0, bx1 - bx0, by1 - by0)
    report = {'slots': [], 'wells': [], 'fields': [], 'glyph_pixels': 0}
    for rgb in ((0x8B, 0x8B, 0x8B), (0, 0, 0), (0xAB, 0x7F, 0x7F)):
        for x, y, w, h, n, pts in components(src, rgb):
            framed = is_framed(src, x, y, w, h)
            if rgb == (0xAB, 0x7F, 0x7F):
                if n < 50: continue
                rrect(out, x, y, w, h, TOK['radius.slot'], col('danger.tile'))
                g = col('danger.glyph')
                for i in range(4, w - 4):
                    for d in (0, 1):
                        out.putpixel((x + i, y + min(i + d - 1, h - 1)), g)
                        out.putpixel((x + w - 1 - i, y + min(i + d - 1, h - 1)), g)
                report['slots'].append((x, y, w, h))
            elif n == w * h and framed:
                fx, fy, fw, fh = x - 1, y - 1, w + 2, h + 2
                if rgb == (0, 0, 0):
                    if not glass:
                        well(out, fx, fy, fw, fh, r=TOK['radius.glass'])
                    else:
                        liquid_glass(out, fx, fy, fw, fh, TOK['radius.glass'], tint='liquid.well_tint_top',
                                     tint_bottom='liquid.well_tint_bottom', edge='liquid.edge_on_light', shadow=False)
                    report['wells'].append((fx, fy, fw, fh))
                elif max(w, h) > 40:
                    # scroll track: thin centred rail; the vanilla hit area is unchanged
                    tw = TOK['scroll.track_width']
                    rrect(out, fx + (fw - tw) // 2, fy + 1, tw, fh - 2, tw // 2, col('scroll.track'))
                    report['slots'].append((fx, fy, fw, fh))
                else:
                    well(out, fx, fy, fw, fh); report['slots'].append((fx, fy, fw, fh))
            elif rgb == (0x8B, 0x8B, 0x8B) and n >= 200:
                rrect(out, x, y, w, h, 3, col('control.fill')); report['fields'].append((x, y, w, h))
            elif rgb == (0x8B, 0x8B, 0x8B) and n >= 10:
                # (tiny components are vanilla bevel corner pixels of slot frames: dropped)
                for p in pts:
                    out.putpixel(p, col('glyph')); report['glyph_pixels'] += 1
    return out, report


def build_inventory(glass=True):
    return repaint_container(os.path.join(VAN, 'container', 'inventory.png'), glass)


# ---------------------------------------------------------------- creative tabs + scroller
def build_tab(pos, selected, top, index):
    """26x32 creative tab. Selected tabs overlap the panel by 4px and merge into it (no edge there);
    tab 1 keeps the panel's left edge, tab 7 its right edge. Unselected tabs sit 2px further out."""
    im = Image.new('RGBA', (26, 32), (0, 0, 0, 0))
    r = TOK['radius.tab']
    fill = col('panel.fill') if selected else col('tab.unselected')
    edge = col('panel.edge')
    h = 32 if selected else 30
    oy = 0 if (selected or not top) else 2
    # draw a box with rounded corners only on the outer side, then flip for bottom tabs
    box = Image.new('RGBA', (26, h + r), (0, 0, 0, 0))
    rrect(box, 0, 0, 26, h + r, r, edge)
    rrect(box, 1, 1, 24, h + r - 2, r - 1, fill)
    if selected:
        hline(box, r, 1, 26 - 2 * r, col('panel.highlight'))
    box = box.crop((0, 0, 26, h))
    if selected:
        merge = 3
        for yy in range(h - merge, h):
            for xx in range(26):
                box.putpixel((xx, yy), fill)
            if index == 1: box.putpixel((0, yy), edge)
            if index == 7: box.putpixel((25, yy), edge)
    if not top:
        box = box.transpose(Image.FLIP_TOP_BOTTOM)
    im.alpha_composite(box, (0, oy))
    return im


def build_recipe_button(highlighted):
    """20x18 recipe-book toggle: panel-coloured rounded button; hover = accent edge.
    The vanilla book artwork is kept and its greens are remapped to the accent blue ramp."""
    src = Image.open(os.path.join(VAN, 'sprites', 'recipe_book', 'button.png')).convert('RGBA')
    im = Image.new('RGBA', (20, 18), (0, 0, 0, 0))
    r = TOK['radius.icon_button']
    rrect(im, 0, 0, 20, 18, r, col('accent.fill') if highlighted else col('panel.edge'))
    rrect(im, 1, 1, 18, 16, r - 1, col('panel.fill'))
    hline(im, r, 1, 20 - 2 * r, col('panel.highlight'))
    remap = {tuple(int(k[i:i + 2], 16) for i in (1, 3, 5)): v for k, v in TOK['book.map'].items()}
    for yy in range(2, 16):
        for xx in range(2, 18):
            p = src.getpixel((xx, yy))
            if p[3] == 0 or p[:3] == (0xC6, 0xC6, 0xC6):
                continue
            if p[:3] in remap:
                h = remap[p[:3]]
                p = (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255)
            im.putpixel((xx, yy), p)
    return im


# ---------------------------------------------------------------- recipe book
def icon_pixels(src, bg_colours, margin=2):
    """Pixels of the vanilla artwork that are neither background nor the bevel/outline frame."""
    w, h = src.size
    out = []
    for yy in range(margin, h - margin):
        for xx in range(margin, w - margin):
            p = src.getpixel((xx, yy))
            if p[3] and p[:3] not in bg_colours:
                out.append(((xx, yy), p))
    return out


def build_recipe_book_panel():
    """recipe_book.png: light panel; the recipe area stays dark (vanilla draws the page counter in
    white) as a graphite rounded well; the blue magnifier glyph is kept."""
    src = Image.open(os.path.join(VAN, 'recipe_book.png')).convert('RGBA')
    out = Image.new('RGBA', src.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = src.getchannel('A').getbbox()
    panel_box(out, x0, y0, x1 - x0, y1 - y0)
    comp = max(components(src, (0x37, 0x37, 0x37)), key=lambda c: c[4])
    cx, cy, cw, ch = comp[:4]
    rrect(out, cx, cy, cw, ch, TOK['radius.glass'], col('recipe.area'))
    neutral = {(0x37, 0x37, 0x37), (0xC6, 0xC6, 0xC6), (0, 0, 0), (0xFF, 0xFF, 0xFF), (0x55, 0x55, 0x55), (0x8B, 0x8B, 0x8B)}
    for (xy, p) in icon_pixels(src.crop((cx, cy, cx + cw, cy + ch)), neutral, margin=0):
        out.putpixel((xy[0] + cx, xy[1] + cy), p)
    return out


def build_recipe_tab(selected):
    """35x27 vertical tab on the left of the recipe book; the selected tab merges into the panel."""
    w = 35 if selected else 30
    im = Image.new('RGBA', (35, 27), (0, 0, 0, 0))
    r = TOK['radius.tab']
    fill = col('panel.fill') if selected else col('tab.unselected')
    box = Image.new('RGBA', (w + r, 26), (0, 0, 0, 0))
    rrect(box, 0, 0, w + r, 26, r, col('panel.edge'))
    rrect(box, 1, 1, w + r - 2, 24, r - 1, fill)
    box = box.crop((0, 0, w, 26))
    if selected:
        for yy in range(1, 25):
            for xx in range(w - 3, w):
                box.putpixel((xx, yy), fill)
    im.alpha_composite(box, (0, 0))
    return im


def build_filter(path, enabled, highlighted):
    """26x16 'craftable only' toggle: on = accent pill with a white check, off = light tile.
    The vanilla icon (crafting table / furnace) is kept."""
    src = Image.open(path).convert('RGBA')
    bg = Counter(src.get_flattened_data()).most_common(1)[0][0][:3]
    im = Image.new('RGBA', src.size, (0, 0, 0, 0))
    r = 4
    edge = col('accent.edge') if (enabled or highlighted) else col('panel.edge')
    if highlighted and not enabled:
        edge = col('accent.fill')
    rrect(im, 0, 0, 26, 16, r, edge)
    rrect(im, 1, 1, 24, 14, r - 1, col('accent.fill') if enabled else col('slot.tile'))
    skip = {bg, (0, 0, 0), (0xFF, 0xFF, 0xFF), (0x8B, 0x8B, 0x8B), (0x88, 0x92, 0xC9), (0x44, 0x49, 0x64), (0x0E, 0x27, 0x25), (0x21, 0x87, 0x56)}
    for (xy, p) in icon_pixels(src, skip):
        if enabled and p[1] > p[0] + 30 and p[1] > p[2] + 20:   # green check -> white
            p = (255, 255, 255, 255)
        im.putpixel(xy, p)
    return im


def build_chevron(forward, highlighted):
    im = Image.new('RGBA', (12, 17), (0, 0, 0, 0))
    c = col('accent.fill') if highlighted else col('chevron')
    pts = [(3 + i, 3 + i) for i in range(6)] + [(8 - i, 9 + i) for i in range(5)]
    for (xx, yy) in pts:
        for d in (0, 1):
            x2 = xx + d if forward else 11 - xx - d
            im.putpixel((x2, yy), c)
    return im


def build_recipe_slot(craftable, many):
    """25x25 recipe button on the dark recipe area. Buttons sit on a 25-px pitch, so the tile is
    inset to 21x21 to leave a gap; 'many' recipes show a second tile peeking out behind."""
    im = Image.new('RGBA', (25, 25), (0, 0, 0, 0))
    r = 3
    x, y, w, h = 2, 2, 21, 21
    if many:
        rrect(im, 4, 4, 20, 20, r, col('recipe.stack'))
        x, y, w, h = 1, 1, 20, 20
    if craftable:
        rrect(im, x, y, w, h, r, col('slot.tile'))
    else:
        rrect(im, x, y, w, h, r, col('danger.glyph'))
        rrect(im, x + 1, y + 1, w - 2, h - 2, r - 1, col('recipe.uncraftable'))
    return im


def build_overlay_button(state):
    """24x24 buttons inside the recipe alternatives popup."""
    im = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
    if state == 'highlighted':
        rrect(im, 0, 0, 24, 24, 3, col('accent.fill')); rrect(im, 1, 1, 22, 22, 2, col('slot.tile'))
    elif state == 'disabled':
        rrect(im, 0, 0, 24, 24, 3, col('danger.tile'))
    elif state == 'disabled_highlighted':
        rrect(im, 0, 0, 24, 24, 3, col('accent.fill')); rrect(im, 1, 1, 22, 22, 2, col('danger.tile'))
    else:
        rrect(im, 0, 0, 24, 24, 3, col('slot.tile'))
    return im


def build_popup():
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    rrect(im, 0, 0, 32, 32, 4, col('panel.edge')); rrect(im, 1, 1, 30, 30, 3, col('panel.fill'))
    return im


def build_text_field(focused):
    """Dark field (vanilla draws field text in white); focus = accent edge."""
    im = Image.new('RGBA', (200, 20), (0, 0, 0, 0))
    rrect(im, 0, 0, 200, 20, 3, col('accent.fill') if focused else col('field.edge'))
    rrect(im, 1, 1, 198, 18, 2, col('control.fill'))
    return im


def build_scroller(disabled):
    """12x15 scroller sprite: a thin centred pill (the game still uses the full 12px for dragging)."""
    im = Image.new('RGBA', (12, 15), (0, 0, 0, 0))
    tw = TOK['scroll.thumb_width']
    rrect(im, (12 - tw) // 2, 0, tw, 15, tw // 2, col('scroller.disabled' if disabled else 'scroller.fill'))
    return im


# ---------------------------------------------------------------- Liquid Glass material
def shape_mask(w, h, r):
    m = set()
    for i in range(h):
        k = min(i, h - 1 - i)
        ins = inset(r, k) if k < r else 0
        for j in range(ins, w - ins):
            m.add((j, i))
    return m


def over(im, xy, c):
    """Alpha-composite one RGBA colour onto a pixel."""
    if not (0 <= xy[0] < im.width and 0 <= xy[1] < im.height) or c[3] == 0:
        return
    br, bg, bb, ba = im.getpixel(xy)
    a = c[3] / 255; oa = a + ba / 255 * (1 - a)
    if oa == 0:
        return
    mix = lambda f, b: round((f * a + b * (ba / 255) * (1 - a)) / oa)
    im.putpixel(xy, (mix(c[0], br), mix(c[1], bg), mix(c[2], bb), round(oa * 255)))


def liquid_glass(im, x, y, w, h, r, underlay=None, tint=None, tint_bottom=None, edge=None, shadow=True):
    """Apple Liquid Glass, translated to static pixels (no blur or refraction exists in vanilla):
    - clear body: very light tint over real transparency (optional dark underlay keeps white HUD text legible)
    - specular rim: brightest where light hits (top-left), secondary glint at bottom-right, dim on the sides
    - lensing band: a softer second ring inside the rim, so the edge reads as thick glass
    - floating shadow: one soft dark row under the shape
    """
    if shadow:
        h -= 1
    outer = shape_mask(w, h, r)
    inner = shape_mask(w - 2, h - 2, max(r - 1, 0))
    inner2 = shape_mask(w - 4, h - 4, max(r - 2, 0))
    rim = {p for p in outer if (p[0] - 1, p[1] - 1) not in inner}
    band = {(p[0] + 1, p[1] + 1) for p in inner if (p[0] - 1, p[1] - 1) not in inner2}
    body = {(p[0] + 2, p[1] + 2) for p in inner2}
    for (px, py) in outer:   # glass replaces whatever was painted underneath (e.g. the opaque panel)
        if 0 <= x + px < im.width and 0 <= y + py < im.height:
            im.putpixel((x + px, y + py), (0, 0, 0, 0))
    if shadow:
        sh = col('liquid.shadow')
        for (px, py) in outer:
            if (px, py + 1) not in outer:
                over(im, (x + px, y + py + 1), sh)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    lo, hi = TOK['liquid.rim_min'], TOK['liquid.rim_max']

    def spec(px, py):
        nx, ny = (px - cx) / max(cx, 1), (py - cy) / max(cy, 1)
        n = math.hypot(nx, ny) or 1
        nx, ny = nx / n, ny / n
        key = max(0.0, -0.707 * nx - 0.707 * ny)          # light from top-left
        echo = 0.55 * max(0.0, 0.707 * nx + 0.707 * ny)   # glint on the opposite corner
        return lo + (hi - lo) * max(key, echo) ** 1.6

    t_top = col(tint) if tint else col('liquid.tint')
    t_bot = col(tint_bottom) if tint_bottom else t_top
    for (px, py) in band | body:
        if underlay:
            over(im, (x + px, y + py), col(underlay))
        f = py / max(h - 1, 1)
        a = round(t_top[3] + (t_bot[3] - t_top[3]) * f)
        over(im, (x + px, y + py), (255, 255, 255, a))
    for (px, py) in band:
        over(im, (x + px, y + py), (255, 255, 255, round(spec(px, py) * TOK['liquid.band'])))
    for (px, py) in rim:
        if edge:
            im.putpixel((x + px, y + py), col(edge))
        if underlay:
            over(im, (x + px, y + py), col(underlay))
        over(im, (x + px, y + py), (255, 255, 255, round(spec(px, py))))


# ---------------------------------------------------------------- HD Liquid Glass (HUD)
# GUI sprites are drawn at a fixed logical size, so a texture with more texels per logical pixel
# renders smoothly (anti-aliased curves, sub-pixel rims) without changing layout. The HUD uses
# hd.scale texels per logical pixel.
import numpy as np


def _rgba(name):
    return np.array(col(name), dtype=np.float64) / 255.0


def _over(dst, rgb, a):
    """Vectorised 'source over' of a colour with per-pixel alpha onto an RGBA float image."""
    a = np.clip(a, 0, 1)[..., None]
    da = dst[..., 3:4]
    oa = a + da * (1 - a)
    out_rgb = np.where(oa > 0, (np.asarray(rgb)[None, None, :3] * a + dst[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-9), 0)
    dst[..., :3] = out_rgb
    dst[..., 3:4] = oa


def _sdf(px, py, cx, cy, hw, hh, r):
    qx = np.abs(px - cx) - (hw - r)
    qy = np.abs(py - cy) - (hh - r)
    ox, oy = np.maximum(qx, 0), np.maximum(qy, 0)
    d = np.hypot(ox, oy) + np.minimum(np.maximum(qx, qy), 0) - r
    # outward normal
    nx = np.where(qx > qy, np.sign(px - cx), 0.0)
    ny = np.where(qy >= qx, np.sign(py - cy), 0.0)
    corner = (qx > 0) & (qy > 0)
    ln = np.maximum(np.hypot(ox, oy), 1e-9)
    nx = np.where(corner, np.sign(px - cx) * ox / ln, nx)
    ny = np.where(corner, np.sign(py - cy) * oy / ln, ny)
    return d, nx, ny


def liquid_glass_hd(W, H, x, y, w, h, r, underlay=None, tint=None, shadow=True, scale=None, rim=True):
    """Liquid Glass rendered with an SDF at hd.scale: clear body, angle-dependent specular rim,
    inner lensing band and a soft floating shadow. Returns a PIL image of W*s x H*s texels."""
    s = scale or TOK['hd.scale']
    ys, xs = np.mgrid[0:H * s, 0:W * s]
    px, py = (xs + 0.5) / s, (ys + 0.5) / s                      # logical coordinates
    img = np.zeros((H * s, W * s, 4))
    if shadow:
        h -= TOK['liquid.shadow_offset']
    cx, cy, hw, hh = x + w / 2, y + h / 2, w / 2, h / 2
    d, nx, ny = _sdf(px, py, cx, cy, hw, hh, r)
    cov = np.clip(0.5 - d * s, 0, 1)                             # anti-aliased coverage
    if shadow:
        ds, _, _ = _sdf(px, py, cx, cy + TOK['liquid.shadow_offset'], hw, hh, r)
        sh = _rgba('liquid.shadow')
        _over(img, sh, sh[3] * np.clip(1 - (ds + 0.6) / 1.2, 0, 1) * (1 - cov))
    rim_w, band_w = TOK['liquid.rim_width'], TOK['liquid.band_width']
    if underlay:
        u = _rgba(underlay) if underlay in TOK else np.array(_hexc(underlay), dtype=np.float64) / 255.0
        _over(img, u, u[3] * cov)
    t = _rgba(tint or 'liquid.tint'); _over(img, t, t[3] * cov)
    key = np.maximum(0, -0.707 * nx - 0.707 * ny)
    echo = 0.55 * np.maximum(0, 0.707 * nx + 0.707 * ny)
    lo, hi = TOK['liquid.rim_min'] / 255, TOK['liquid.rim_max'] / 255
    spec = lo + (hi - lo) * np.maximum(key, echo) ** 1.6
    band = np.clip((d + rim_w + band_w) * s, 0, 1) * np.clip((-d - rim_w) * s + 1, 0, 1) * cov
    band *= np.clip((d + rim_w + band_w) / band_w, 0, 1)          # fade inward
    if rim:   # white specular outline + inner band (off for the hotbar since 0.10)
        _over(img, (1, 1, 1), spec * TOK['liquid.band'] * band)
        edge = np.clip((d + rim_w) * s + 0.5, 0, 1) * cov
        _over(img, (1, 1, 1), spec * edge)
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')


def liquid_shelf_hd(W, H, x, w, underlay, rim=False, scale=None):
    """Liquid Glass *shelf* (classic 3D-Dock look): a glass platform the items sit on instead of a
    box around them. Trapezoid narrowing towards the back (perspective), bright top lip, faint front
    edge, translucent surface with a light-to-clear gradient, soft shadow row underneath."""
    from PIL import ImageDraw
    s = scale or TOK['hd.scale']
    ss = 4                                             # supersampling for anti-aliased edges
    top, bot, ins = TOK['shelf.top'], H - 1, TOK['shelf.inset']
    poly = [(x + ins, top), (x + w - ins, top), (x + w, bot), (x, bot)]
    big = Image.new('L', (W * s * ss, H * s * ss), 0)
    ImageDraw.Draw(big).polygon([(px * s * ss, py * s * ss) for px, py in poly], fill=255)
    cov = np.asarray(big.resize((W * s, H * s), Image.BOX), dtype=np.float64) / 255.0
    ys, xs = np.mgrid[0:H * s, 0:W * s]
    py = (ys + 0.5) / s
    img = np.zeros((H * s, W * s, 4))
    # shadow: the shape shifted down by one logical pixel, outside the shelf only
    sh_mask = np.zeros_like(cov); sh_mask[s:, :] = cov[:-s, :]
    sh = _rgba('liquid.shadow'); _over(img, sh, sh[3] * sh_mask * (1 - cov))
    u = _rgba(underlay) if underlay in TOK else np.array(_hexc(underlay), dtype=np.float64) / 255.0
    _over(img, u, u[3] * cov)
    t0, t1 = _rgba('shelf.surface_top'), _rgba('shelf.surface_bottom')
    f = np.clip((py - top) / max(bot - top, 1), 0, 1)
    _over(img, (1, 1, 1), (t0[3] + (t1[3] - t0[3]) * f) * cov)
    # top lip: bright 0.75-px band along the back edge; faint band along the front edge
    lip = _rgba('shelf.lip'); front = _rgba('shelf.front')
    _over(img, (1, 1, 1), lip[3] * cov * np.clip(1 - (py - top) / 0.75, 0, 1))
    _over(img, (1, 1, 1), front[3] * cov * np.clip(1 - (bot - py) / 0.75, 0, 1))
    if rim:  # optional outline around the whole shelf
        edge = cov - np.asarray(big.filter(__import__('PIL.ImageFilter', fromlist=['MinFilter']).MinFilter(2 * ss + 1))
                                .resize((W * s, H * s), Image.BOX), dtype=np.float64) / 255.0
        _over(img, (1, 1, 1), np.clip(edge, 0, 1) * (TOK['liquid.rim_max'] / 255) * 0.8)
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')


def build_hotbar_shelf(rim=False, underlay='liquid.underlay_hud'):
    return liquid_shelf_hd(182, 22, 0, 182, underlay, rim=rim, scale=TOK['hd.scale_hotbar'])


def build_offhand_shelf(side, rim=False, underlay='liquid.underlay_hud'):
    return liquid_shelf_hd(29, 24, 0 if side == 'left' else 7, 22, underlay, rim=rim)


def build_hotbar(rim=False, underlay='liquid.underlay_hud'):
    # Items float on the glass like Dock icons; no per-slot boxes.
    # 0.8 test: a 4x hotbar (728x88) showed the missing texture in game while the 4x selection and
    # offhand worked; the hotbar is the only HUD sprite wider than 512 texels, so it uses 2x (364x44).
    return liquid_glass_hd(182, 22, 0, 0, 182, 22, TOK['radius.dock'], underlay=underlay,
                           scale=TOK['hd.scale_hotbar'], rim=rim)


def build_selection():
    # No selection frame: the selected slot is shown purely by Dock-style magnification of the
    # item (see build_magnification). The sprite must still exist, so it is fully transparent.
    return Image.new('RGBA', (24, 23), (0, 0, 0, 0))


def build_selection_bubble():
    """Optional raised glass bubble for the selected slot (Respackopts setting)."""
    return liquid_glass_hd(24, 23, 0, 0, 24, 23, TOK['radius.lens'], tint='liquid.lens_tint')


def build_offhand(side, rim=False, underlay='liquid.underlay_hud'):
    return liquid_glass_hd(29, 24, 0 if side == 'left' else 7, 1, 22, 23, TOK['radius.dock'], underlay=underlay,
                           rim=rim)


def build_highlight(which):
    im = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
    rrect(im, 4, 4, 16, 16, TOK['radius.slot'], col('highlight.' + which))
    return im


# ---------------------------------------------------------------- widgets
def build_button(state, r):
    im = Image.new('RGBA', (200, 20), (0, 0, 0, 0))
    pre = {'normal': 'control', 'highlighted': 'accent', 'disabled': 'disabled'}[state]
    rrect(im, 0, 0, 200, 20, r, col(pre + '.edge'))
    rrect(im, 1, 1, 198, 18, max(r - 1, 0), col(pre + '.fill'))
    hline(im, r, 1, 200 - 2 * r, col(pre + '.top'))
    return im


def build_slider_track(highlighted, r=None):
    """200x20 slider track: same graphite pill as the buttons (vanilla draws the label in white).
    Hover/focus adds an accent edge instead of a blue fill, so the label stays calm."""
    r = r or TOK['radius.button']
    im = Image.new('RGBA', (200, 20), (0, 0, 0, 0))
    rrect(im, 0, 0, 200, 20, r, col('accent.fill') if highlighted else col('control.edge'))
    rrect(im, 1, 1, 198, 18, max(r - 1, 0), col('control.fill'))
    hline(im, r, 1, 200 - 2 * r, col('control.top'))
    return im


def build_slider_knob(highlighted):
    """8x20 slider handle: a 6x14 rounded knob inset inside the pill track (so at 0% / 100% it
    stays inside the track's rounded ends); grey at rest, Apple blue on hover/drag."""
    r = TOK['radius.knob'] - 1
    im = Image.new('RGBA', (8, 20), (0, 0, 0, 0))
    x, y, w, h = 1, 3, 6, 14
    edge, fill, top = (('accent.edge', 'accent.fill', 'accent.top') if highlighted
                       else ('knob.edge', 'knob.fill', 'knob.highlight'))
    rrect(im, x, y, w, h, r, col(edge)); rrect(im, x + 1, y + 1, w - 2, h - 2, r - 1, col(fill))
    hline(im, x + 2, y + 1, w - 4, col(top))
    return im


def nine(w, h, border):
    return {"gui": {"scaling": {"type": "nine_slice", "width": w, "height": h, "border": border}}}


def build_tooltip():
    r = TOK['radius.tooltip']
    bg = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    rrect(bg, 8, 8, 84, 84, r, col('tooltip.fill'))
    fr = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    rrect(fr, 8, 8, 84, 84, r, col('tooltip.frame'))
    rrect(fr, 9, 9, 82, 82, max(r - 1, 0), None, mode='clear')
    return bg, fr


def build_icon():
    """pack.png: the macOS UI logo filling the icon (design/logo/logo-icon.png: native pixels with a
    1px margin), scaled by the largest whole factor that keeps it at least 128px."""
    logo = Image.open(os.path.join(REPO, 'design', 'logo', 'logo-icon.png')).convert('RGBA')
    k = max(1, -(-128 // logo.width))
    return logo.resize((logo.width * k, logo.height * k), Image.NEAREST)


# ---------------------------------------------------------------- food bar (silver apples)
# 9x9 apple, redrawn by hand after the layout of Minecraft's golden apple (stem on top, highlight
# top-left, shade bottom-right) and coloured silver. The game draws food_empty behind every slot
# and food_full / food_half on top of it.
APPLE = [
    "....s....",
    "..oosoo..",
    ".oHllmmo.",
    "oHllmmmdo",
    "olmmmmmdo",
    "ommmmmddo",
    ".ommmddo.",
    "..odddo..",
    "...ooo...",
]


def _hexc(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) if len(h) == 8 else 255)


def build_food(kind, palette):
    im = Image.new('RGBA', (9, 9), (0, 0, 0, 0))
    pal = {k: _hexc(v) for k, v in TOK[palette].items()}
    for y, row in enumerate(APPLE):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            if kind == 'empty':
                c = pal['o'] if ch in 'os' else pal['f']
            else:
                if kind == 'half' and x > 4:   # half icon = left half of the apple
                    continue
                c = pal[ch]
            im.putpixel((x, y), c)
    return im


# ---------------------------------------------------------------- hotbar magnification
# Dock-style magnification of the selected hotbar item, done entirely with vanilla item model
# definitions (1.21.4+): every assets/minecraft/items/*.json is wrapped in
#   condition minecraft:selected -> select minecraft:display_context == gui -> magnified model
# where each magnified model is a one-line child of the original model with a larger "gui"
# display transform. oversized_in_gui lets the bigger item draw past its 16x16 slot (1.21.6+).
MODELS = os.path.join(REF, 'assets', 'minecraft', 'models')
ITEMS = os.path.join(REF, 'assets', 'minecraft', 'items')
NS = 'macos_ui'
MAG_WRAPPERS = {}
VERSION = '0.15'   # single source for the pack title and the zip name


def _model_json(mid):
    ns, path = (mid.split(':', 1) + [None])[:2] if ':' in mid else ('minecraft', mid)
    if ns != 'minecraft':
        return None
    f = os.path.join(MODELS, path + '.json')
    return json.load(open(f)) if os.path.exists(f) else None


def _gui_transform(mid, depth=0):
    m = _model_json(mid)
    if m is None or depth > 20:
        return None
    if 'display' in m and 'gui' in m['display']:
        return m['display']['gui']
    return _gui_transform(m['parent'], depth + 1) if 'parent' in m else None


def _magnified_id(mid, wrappers):
    full = mid if ':' in mid else 'minecraft:' + mid
    ns, path = full.split(':', 1)
    wid = f'{NS}:magnified/{ns}/{path}'
    if wid not in wrappers:
        wrappers[wid] = (full, _gui_transform(full) or {})
    return wid


def write_magnified_models(root, wrappers, k, base=None):
    """Write every wrapper model with gui scale multiplied by k under base (default: the real path)."""
    for wid, (parent, g) in wrappers.items():
        path = wid.split(':', 1)[1]                       # magnified/<ns>/<path>
        scale = [round(v * k, 4) for v in g.get('scale', [1, 1, 1])]
        gui = {'rotation': g.get('rotation', [0, 0, 0]), 'translation': g.get('translation', [0, 0, 0]), 'scale': scale}
        rel = (base + path.split('/', 1)[1]) if base else os.path.join('assets', NS, 'models', path)
        dest = os.path.join(root, rel + '.json')
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        json.dump({'parent': parent, 'display': {'gui': gui}}, open(dest, 'w'), separators=(',', ':'))


def _magnify_tree(node, wrappers):
    if isinstance(node, list):
        return [_magnify_tree(n, wrappers) for n in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k in ('model', 'base') and isinstance(v, str):
            out[k] = _magnified_id(v, wrappers)
        else:
            out[k] = _magnify_tree(v, wrappers)
    return out


def build_magnification(root):
    wrappers = {}
    n = 0
    for f in sorted(os.listdir(ITEMS)):
        if not f.endswith('.json'):
            continue
        d = json.load(open(os.path.join(ITEMS, f)))
        orig = d['model']
        d['model'] = {
            'type': 'minecraft:condition', 'property': 'minecraft:selected',
            'on_false': orig,
            'on_true': {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                        'cases': [{'when': 'gui', 'model': _magnify_tree(orig, wrappers)}],
                        'fallback': orig},
        }
        d['oversized_in_gui'] = True
        dest = os.path.join(root, 'assets', 'minecraft', 'items', f)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        json.dump(d, open(dest, 'w'), separators=(',', ':'))
        n += 1
    write_magnified_models(root, wrappers, TOK['magnify.sizes']['normal'])
    MAG_WRAPPERS.update(wrappers)
    return n, len(wrappers)


# ---------------------------------------------------------------- optional in-game settings (Respackopts)
# Bonus for players who install the Respackopts mod. Without the mod Minecraft ignores
# respackopts.json5 and every .rpo file, so the pack behaves exactly as the defaults below.
# Alternative files live in assets/macos_ui/alt/, which no vanilla loader reads.
RPO_CONF = {
    'id': 'macosUi', 'version': 13, 'capabilities': ['FileFilter', 'DirFilter', 'DirFilterAdditive'],
    'conf': {
        'hud': {
            'magnification': {'type': 'enum', 'default': 'normal', 'values': ['off', 'small', 'normal', 'large', 'extraLarge']},
            'selectionBubble': False,
            'hotbarStyle': {'type': 'enum', 'default': 'dock', 'values': ['dock', 'shelf']},
            'hotbarOpacity': {'type': 'enum', 'default': 'clear', 'values': ['clear', 'frosted', 'dark', 'solid']},
            'hotbarOutline': False,
            'foodIcons': {'type': 'enum', 'default': 'silverApples', 'values': ['silverApples', 'vanilla']},
        },
        'widgets': {'buttonShape': {'type': 'enum', 'default': 'pill', 'values': ['pill', 'rounded']}},
        'inventory': {'glassPlayerArea': True},
    },
}
_L = {
    'en_us': {
        '': 'macOS UI', 'hud': 'Hotbar and HUD',
        'hud.magnification': 'Magnify selected item', 'hud.magnification.off': 'Off',
        'hud.magnification.small': 'Small (1.25×)', 'hud.magnification.normal': 'Normal (1.38×)',
        'hud.magnification.large': 'Large (1.5×)', 'hud.magnification.extraLarge': 'Extra large (1.75×)',
        'hud.selectionBubble': 'Glass bubble on selected slot',
        'hud.hotbarStyle': 'Hotbar style', 'hud.hotbarStyle.dock': 'Dock (glass bar)', 'hud.hotbarStyle.shelf': 'Shelf (glass ledge)',
        'hud.hotbarOpacity': 'Hotbar opacity', 'hud.hotbarOpacity.clear': 'Clear',
        'hud.hotbarOpacity.frosted': 'Frosted', 'hud.hotbarOpacity.dark': 'Dark', 'hud.hotbarOpacity.solid': 'Solid',
        'hud.hotbarOutline': 'Glass outline on hotbar',
        'hud.foodIcons': 'Food icons', 'hud.foodIcons.silverApples': 'Silver apples', 'hud.foodIcons.vanilla': 'Vanilla',
        'widgets': 'Buttons and sliders', 'widgets.buttonShape': 'Button shape',
        'widgets.buttonShape.pill': 'Pill', 'widgets.buttonShape.rounded': 'Rounded rectangle',
        'inventory': 'Inventory', 'inventory.glassPlayerArea': 'Glass behind player model',
    },
    'es_mx': {
        '': 'macOS UI', 'hud': 'Barra rápida y HUD',
        'hud.magnification': 'Ampliar objeto seleccionado', 'hud.magnification.off': 'Desactivado',
        'hud.magnification.small': 'Pequeño (1.25×)', 'hud.magnification.normal': 'Normal (1.38×)',
        'hud.magnification.large': 'Grande (1.5×)', 'hud.magnification.extraLarge': 'Muy grande (1.75×)',
        'hud.selectionBubble': 'Burbuja de cristal en la ranura seleccionada',
        'hud.hotbarStyle': 'Estilo de la barra', 'hud.hotbarStyle.dock': 'Dock (barra de cristal)', 'hud.hotbarStyle.shelf': 'Repisa (cornisa de cristal)',
        'hud.hotbarOpacity': 'Opacidad de la barra', 'hud.hotbarOpacity.clear': 'Transparente',
        'hud.hotbarOpacity.frosted': 'Esmerilada', 'hud.hotbarOpacity.dark': 'Oscura', 'hud.hotbarOpacity.solid': 'Sólida',
        'hud.hotbarOutline': 'Borde de cristal en la barra',
        'hud.foodIcons': 'Iconos de comida', 'hud.foodIcons.silverApples': 'Manzanas plateadas', 'hud.foodIcons.vanilla': 'Vanilla',
        'widgets': 'Botones y deslizadores', 'widgets.buttonShape': 'Forma de botones',
        'widgets.buttonShape.pill': 'Píldora', 'widgets.buttonShape.rounded': 'Rectángulo redondeado',
        'inventory': 'Inventario', 'inventory.glassPlayerArea': 'Cristal detrás del jugador',
    },
}
RPO_LANG = {lang: {('rpo.macosUi' + ('.' + k if k else '')): v for k, v in d.items()} for lang, d in _L.items()}


def _write_json(root, rel, data):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def _rpo(root, rel, condition, fallback=None):
    """Write <rel>.rpo (or <dir>/.rpo when rel ends with '/')."""
    data = {'condition': condition}
    if fallback:
        data['fallback'] = fallback
    _write_json(root, rel + '.rpo' if not rel.endswith('/') else rel + '.rpo', data)


def build_options(root):
    gui = 'assets/minecraft/textures/gui/'
    alt = 'assets/macos_ui/alt/'
    _write_json(root, 'respackopts.json5', RPO_CONF)
    for lang, entries in RPO_LANG.items():
        _write_json(root, f'assets/macos_ui/lang/{lang}.json', entries)
    n = 0

    # hud.magnification ----------------------------------------------------------------------
    # off: drop the whole items/ override. Sizes: folders accept a single fallback, so the
    # magnified model tree is nested three levels deep, one size per level:
    #   magnified/                 -> large       (fallback when large)
    #   magnified/minecraft/       -> small       (fallback when small)
    #   magnified/minecraft/<sub>/ -> extraLarge  (fallback when extraLarge)
    _rpo(root, 'assets/minecraft/items/', '!hud.magnification.off'); n += 1
    sizes = TOK['magnify.sizes']
    mdir = f'assets/{NS}/models/magnified/'
    write_magnified_models(root, MAG_WRAPPERS, sizes['large'], alt + 'magnify/large/')
    _write_json(root, mdir + '.rpo', {'condition': '!hud.magnification.large', 'fallback': alt + 'magnify/large/'}); n += 1
    write_magnified_models(root, MAG_WRAPPERS, sizes['small'], alt + 'magnify/small/')
    _write_json(root, mdir + 'minecraft/.rpo', {'condition': '!hud.magnification.small', 'fallback': alt + 'magnify/small/minecraft/'}); n += 1
    write_magnified_models(root, MAG_WRAPPERS, sizes['extraLarge'], alt + 'magnify/xl/')
    for sub in sorted(os.listdir(os.path.join(root, mdir, 'minecraft'))):
        if os.path.isdir(os.path.join(root, mdir, 'minecraft', sub)):
            _write_json(root, mdir + f'minecraft/{sub}/.rpo',
                        {'condition': '!hud.magnification.extraLarge', 'fallback': alt + f'magnify/xl/minecraft/{sub}/'}); n += 1

    # hud.selectionBubble ---------------------------------------------------------------------
    save_at(build_selection_bubble(), root, alt + 'bubble/hotbar_selection.png')
    _write_json(root, gui + 'sprites/hud/hotbar_selection.png.rpo',
                {'condition': '!hud.selectionBubble', 'fallbacks': [alt + 'bubble/hotbar_selection.png']}); n += 1

    # hud.hotbarStyle x hud.hotbarOpacity x hud.hotbarOutline -> one file per combination -------
    combos = [(st, o, rim) for st in ('dock', 'shelf') for o in TOK['hotbar.opacity'] for rim in (False, True)]
    makers = {
        'sprites/hud/hotbar.png': {'dock': lambda u, r: build_hotbar(rim=r, underlay=u),
                                   'shelf': lambda u, r: build_hotbar_shelf(rim=r, underlay=u)},
        'sprites/hud/hotbar_offhand_left.png': {'dock': lambda u, r: build_offhand('left', rim=r, underlay=u),
                                                'shelf': lambda u, r: build_offhand_shelf('left', rim=r, underlay=u)},
        'sprites/hud/hotbar_offhand_right.png': {'dock': lambda u, r: build_offhand('right', rim=r, underlay=u),
                                                 'shelf': lambda u, r: build_offhand_shelf('right', rim=r, underlay=u)},
    }
    for rel, make in makers.items():
        fallbacks = []
        for st, o, rim in combos:
            cond = f"hud.hotbarStyle.{st} & hud.hotbarOpacity.{o} & {'' if rim else '!'}hud.hotbarOutline"
            if (st, o, rim) == ('dock', 'clear', False):
                main_cond = cond
                continue
            path = alt + f"hotbar/{st}_{o}{'_outline' if rim else ''}/" + rel
            save_at(make[st](TOK['hotbar.opacity'][o], rim), root, path)
            _write_json(root, path + '.rpo', {'condition': cond}); n += 1
            fallbacks.append(path)
        _write_json(root, gui + rel + '.rpo', {'condition': main_cond, 'fallbacks': fallbacks}); n += 1

    # hud.foodIcons: remove our food sprites to fall back to vanilla --------------------------------
    for kind in ('full', 'half', 'empty'):
        for suf in ('', '_hunger'):
            _rpo(root, gui + f'sprites/hud/food_{kind}{suf}.png', 'hud.foodIcons.silverApples'); n += 1

    # widgets.buttonShape: rounded-rectangle alternatives (texture + nine-slice metadata) -------------
    rr = 5
    for st, fn in (('normal', 'button'), ('highlighted', 'button_highlighted'), ('disabled', 'button_disabled')):
        save_at(build_button(st, rr), root, alt + f'rounded/sprites/widget/{fn}.png', nine(200, 20, rr))
    save_at(build_slider_track(False, rr), root, alt + 'rounded/sprites/widget/slider.png', nine(200, 20, rr))
    save_at(build_slider_track(True, rr), root, alt + 'rounded/sprites/widget/slider_highlighted.png', nine(200, 20, rr))
    for fn in ('button', 'button_highlighted', 'button_disabled', 'slider', 'slider_highlighted'):
        for ext in ('.png', '.png.mcmeta'):
            rel = f'sprites/widget/{fn}{ext}'
            _rpo(root, gui + rel, 'widgets.buttonShape.pill', alt + 'rounded/' + rel); n += 1

    # inventory.glassPlayerArea: opaque tile instead of glass when off ---------------------------
    inv, _ = build_inventory(glass=False)
    tab, _ = repaint_container(os.path.join(VAN, 'container', 'creative_inventory', 'tab_inventory.png'), glass=False)
    for rel, im in (('container/inventory.png', inv), ('container/creative_inventory/tab_inventory.png', tab)):
        save_at(im, root, alt + 'opaque/' + rel)
        _rpo(root, gui + rel, 'inventory.glassPlayerArea', alt + 'opaque/' + rel); n += 1
    return n


# ---------------------------------------------------------------- assemble
def save_at(im, root, rel, meta=None):
    """Save to an explicit path relative to the pack root (used for alternative files)."""
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p)
    if meta is not None:
        json.dump(meta, open(p + '.mcmeta', 'w'), indent=2)


def save(im, root, rel, meta=None):
    p = os.path.join(root, 'assets', 'minecraft', 'textures', 'gui', rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p)
    if meta is not None:
        json.dump(meta, open(p + '.mcmeta', 'w'), indent=2)


def build_pack(name, desc, btn_r):
    root = os.path.join(OUT, name)
    shutil.rmtree(root, ignore_errors=True); os.makedirs(root)
    json.dump({"pack": {"description": desc, "min_format": [75, 0], "max_format": [75, 0]}},
              open(os.path.join(root, 'pack.mcmeta'), 'w'), indent=2, ensure_ascii=False)
    build_icon().save(os.path.join(root, 'pack.png'))
    inv, report = build_inventory()
    save(inv, root, 'container/inventory.png')
    for tab in ('tab_items', 'tab_item_search', 'tab_inventory'):
        im, rep = repaint_container(os.path.join(VAN, 'container', 'creative_inventory', tab + '.png'))
        save(im, root, f'container/creative_inventory/{tab}.png')
        report[tab] = {k: len(v) if isinstance(v, list) else v for k, v in rep.items()}
    for top in (True, False):
        for sel in (True, False):
            for i in range(1, 8):
                tab_file = f"tab_{'top' if top else 'bottom'}_{'selected' if sel else 'unselected'}_{i}.png"
                save(build_tab(i, sel, top, i), root, "sprites/container/creative_inventory/" + tab_file)
    save(build_recipe_book_panel(), root, 'recipe_book.png')
    save(build_recipe_tab(False), root, 'sprites/recipe_book/tab.png')
    save(build_recipe_tab(True), root, 'sprites/recipe_book/tab_selected.png')
    for fam in ('filter', 'furnace_filter'):
        for en in ('enabled', 'disabled'):
            for hl in ('', '_highlighted'):
                n = f'{fam}_{en}{hl}'
                save(build_filter(os.path.join(VAN, 'sprites', 'recipe_book', n + '.png'), en == 'enabled', bool(hl)),
                     root, f'sprites/recipe_book/{n}.png')
    for fw in (True, False):
        for hl in (False, True):
            save(build_chevron(fw, hl), root, f"sprites/recipe_book/page_{'forward' if fw else 'backward'}{'_highlighted' if hl else ''}.png")
    for cr in (True, False):
        for many in (False, True):
            save(build_recipe_slot(cr, many), root, f"sprites/recipe_book/slot_{'many_' if many else ''}{'craftable' if cr else 'uncraftable'}.png")
    for fam in ('crafting_overlay', 'furnace_overlay'):
        for st, suf in (('normal', ''), ('highlighted', '_highlighted'), ('disabled', '_disabled'), ('disabled_highlighted', '_disabled_highlighted')):
            save(build_overlay_button(st), root, f'sprites/recipe_book/{fam}{suf}.png')
    save(build_popup(), root, 'sprites/recipe_book/overlay_recipe.png', nine(32, 32, 4))
    save(build_text_field(False), root, 'sprites/widget/text_field.png', nine(200, 20, 3))
    save(build_text_field(True), root, 'sprites/widget/text_field_highlighted.png', nine(200, 20, 3))
    save(build_recipe_button(False), root, 'sprites/recipe_book/button.png')
    save(build_recipe_button(True), root, 'sprites/recipe_book/button_highlighted.png')
    save(build_scroller(False), root, 'sprites/container/creative_inventory/scroller.png')
    save(build_scroller(True), root, 'sprites/container/creative_inventory/scroller_disabled.png')
    for kind in ('full', 'half', 'empty'):
        save(build_food(kind, 'food.empty' if kind == 'empty' else 'food.silver'), root, f'sprites/hud/food_{kind}.png')
        save(build_food(kind, 'food.empty_hunger' if kind == 'empty' else 'food.hunger'), root, f'sprites/hud/food_{kind}_hunger.png')
    save(build_hotbar(), root, 'sprites/hud/hotbar.png')
    save(build_selection(), root, 'sprites/hud/hotbar_selection.png')
    save(build_offhand('left'), root, 'sprites/hud/hotbar_offhand_left.png')
    save(build_offhand('right'), root, 'sprites/hud/hotbar_offhand_right.png')
    save(build_highlight('back'), root, 'sprites/container/slot_highlight_back.png', nine(24, 24, 4))
    save(build_highlight('front'), root, 'sprites/container/slot_highlight_front.png', nine(24, 24, 4))
    # Nine-slice borders must leave a stretchable centre: top+bottom == height failed to load in game
    # (pill test 0.1 showed missing textures), so cap vertical border at 9 for 20px-tall sprites.
    border = btn_r if btn_r < 10 else {"left": btn_r, "right": btn_r, "top": 9, "bottom": 9}
    for st, fn in (('normal', 'button'), ('highlighted', 'button_highlighted'), ('disabled', 'button_disabled')):
        save(build_button(st, btn_r), root, f'sprites/widget/{fn}.png', nine(200, 20, border))
    pill = {"left": TOK['radius.button'], "right": TOK['radius.button'], "top": 9, "bottom": 9}
    save(build_slider_track(False), root, 'sprites/widget/slider.png', nine(200, 20, pill))
    save(build_slider_track(True), root, 'sprites/widget/slider_highlighted.png', nine(200, 20, pill))
    knob_border = {"left": 3, "right": 3, "top": 3, "bottom": 3}
    save(build_slider_knob(False), root, 'sprites/widget/slider_handle.png', nine(8, 20, knob_border))
    save(build_slider_knob(True), root, 'sprites/widget/slider_handle_highlighted.png', nine(8, 20, knob_border))
    bg, fr = build_tooltip()
    save(bg, root, 'sprites/tooltip/background.png', nine(100, 100, 9))
    fmeta = nine(100, 100, 10); fmeta['gui']['scaling']['stretch_inner'] = True
    save(fr, root, 'sprites/tooltip/frame.png', fmeta)
    report['magnification'] = dict(zip(('item_definitions', 'wrapper_models'), build_magnification(root)))
    report['rpo_files'] = build_options(root)
    z = os.path.join(OUT, name + '.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for d, _, fs in os.walk(root):
            for f in fs:
                full = os.path.join(d, f); zf.write(full, os.path.relpath(full, root))
    return report


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    rep = build_pack(f'macOS-UI-Light-{VERSION}', f'§fmacOS UI §7— Light\n§8Prototype {VERSION}', TOK['radius.button'])
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in rep.items()}))
