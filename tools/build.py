"""Build the Vanilla x Apple UI resource packs from design tokens + the vanilla reference.

Usage:
    python3 tools/extract_vanilla.py path/to/minecraft-1.21.11-client.jar   # once
    python3 tools/build.py                                                  # -> dist/

Optional: python3 tools/build.py <vanilla_reference_root> <out_dir>
Produces the pack as a folder and a zip in dist/.
Every colour and radius comes from design/tokens.json.
"""
import json, math, os, shutil, sys, zipfile
from collections import deque
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


def build_inventory():
    src = Image.open(os.path.join(VAN, 'container', 'inventory.png')).convert('RGBA')
    out = Image.new('RGBA', src.size, (0, 0, 0, 0))
    panel_box(out, 0, 0, 176, 166)
    report = {'slots': [], 'wells': [], 'glyph_pixels': 0}
    # slots and other framed wells (fill #8B8B8B) + player preview (opaque black)
    for rgb in ((0x8B, 0x8B, 0x8B), (0, 0, 0)):
        for x, y, w, h, n, pts in components(src, rgb):
            if n == w * h and is_framed(src, x, y, w, h):
                fx, fy, fw, fh = x - 1, y - 1, w + 2, h + 2
                if rgb == (0, 0, 0):
                    liquid_glass(out, fx, fy, fw, fh, TOK['radius.glass'], tint='liquid.well_tint_top', tint_bottom='liquid.well_tint_bottom', edge='liquid.edge_on_light', shadow=False); report['wells'].append((fx, fy, fw, fh))
                else:
                    well(out, fx, fy, fw, fh); report['slots'].append((fx, fy, fw, fh))
            elif rgb == (0x8B, 0x8B, 0x8B) and n >= 10:
                # (tiny components are vanilla bevel corner pixels of slot frames: dropped)
                # unframed grey shapes = glyphs (crafting arrow)
                for p in pts:
                    out.putpixel(p, col('glyph')); report['glyph_pixels'] += 1
    return out, report


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


# ---------------------------------------------------------------- HUD (Liquid Glass Dock)
def build_hotbar():
    # No per-slot boxes: items float on the glass like Dock icons. Last row = floating shadow.
    im = Image.new('RGBA', (182, 22), (0, 0, 0, 0))
    liquid_glass(im, 0, 0, 182, 22, TOK['radius.dock'], underlay='liquid.underlay_hud')
    return im


def build_selection():
    # 24x23 sprite drawn at (slotX-1, hotbarY-1). Items can't be scaled by a resource pack, so the
    # "magnified" Dock slot is expressed as a raised glass bubble: full sprite size (1px above the bar),
    # brighter tint, and its own floating shadow on the bar's bottom row.
    im = Image.new('RGBA', (24, 23), (0, 0, 0, 0))
    liquid_glass(im, 0, 0, 24, 23, TOK['radius.lens'], tint='liquid.lens_tint')
    return im


def build_offhand(side):
    im = Image.new('RGBA', (29, 24), (0, 0, 0, 0))
    liquid_glass(im, 0 if side == 'left' else 7, 1, 22, 23, TOK['radius.dock'], underlay='liquid.underlay_hud')
    return im


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
    im = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    rrect(im, 2, 2, 60, 60, 12, col('panel.edge'))
    rrect(im, 3, 3, 58, 58, 11, col('panel.fill'))
    for i in range(3):
        for j in range(3):
            well(im, 11 + i * 15, 9 + j * 13, 13, 11, r=2)
    rrect(im, 8, 49, 48, 9, 4, (0x1D, 0x1D, 0x1F, 255))
    rrect(im, 10, 51, 10, 5, 2, (0xF5, 0xF5, 0xF7, 255))
    return im.resize((128, 128), Image.NEAREST)


# ---------------------------------------------------------------- assemble
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
    bg, fr = build_tooltip()
    save(bg, root, 'sprites/tooltip/background.png', nine(100, 100, 9))
    fmeta = nine(100, 100, 10); fmeta['gui']['scaling']['stretch_inner'] = True
    save(fr, root, 'sprites/tooltip/frame.png', fmeta)
    z = os.path.join(OUT, name + '.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for d, _, fs in os.walk(root):
            for f in fs:
                full = os.path.join(d, f); zf.write(full, os.path.relpath(full, root))
    return report


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    rep = build_pack('VanillaAppleUI-Light', '§fVanilla × Apple UI §7— Light\n§8Prototype 0.6', TOK['radius.button'])
    print(json.dumps({k: (v if k == 'glyph_pixels' else len(v)) for k, v in rep.items()}))
    print('slots', rep['slots']); print('wells', rep['wells'])
