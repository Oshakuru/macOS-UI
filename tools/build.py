"""Build the macUI resource pack from design tokens + the vanilla reference.

Usage:
    python3 tools/extract_vanilla.py path/to/minecraft-1.21.11-client.jar   # once
    python3 tools/build.py                                                  # -> dist/

Optional: python3 tools/build.py <vanilla_reference_root> <out_dir>
Produces the pack as a folder and a zip in dist/.
Every colour and radius comes from design/tokens.json.
"""
import json, math, os, shutil, sys, zipfile
from collections import Counter, deque
from PIL import Image, ImageDraw, ImageFont

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
        pad = TOK['slot.tile_inset']
        rrect(im, x + pad, y + pad, w - 2 * pad, h - 2 * pad, r, col('slot.tile'))
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


def container_palette(src, accent=False, danger=False):
    """Keep each sprite's UVs, alpha and artwork; replace its vanilla UI material."""
    pixels = np.array(src.convert('RGBA'))
    rgb = pixels[:, :, :3].copy()
    neutral = (rgb.max(axis=2).astype(int) - rgb.min(axis=2).astype(int)) < 12
    shades = ((55, 'glyph'), (139, 'glyph'), (198, 'panel.fill'),
              (255, 'panel.highlight'))
    value = rgb.mean(axis=2)
    # Assign from the untouched source so replacements cannot cascade.
    distances = np.stack([np.abs(value - shade) for shade, _ in shades])
    nearest = distances.argmin(axis=0)
    for index, (_, token) in enumerate(shades):
        pixels[:, :, :3][neutral & (nearest == index)] = col(token)[:3]
    for source, token in (((33, 33, 33), 'control.fill'),
                          ((81, 73, 58), 'recipe.area'),
                          ((160, 145, 114), 'slot.tile'),
                          ((255, 0, 0), 'control.fill')):
        pixels[:, :, :3][np.all(rgb == source, axis=2)] = col(token)[:3]
    if accent or danger:
        pixels[:, :, :3] = col('danger.glyph' if danger else 'accent.fill')[:3]
    return Image.fromarray(pixels, 'RGBA')


def build_container_screen(path):
    src = Image.open(path).convert('RGBA')
    out = container_palette(src)
    # Round only the panel perimeter. Interior artwork and transparent UV regions stay intact.
    x0, y0, x1, y1 = src.getchannel('A').getbbox()
    mask = Image.new('RGBA', src.size)
    panel_box(mask, x0, y0, x1 - x0, y1 - y0)
    out.putalpha(Image.fromarray(np.minimum(np.array(src.getchannel('A')),
                                           np.array(mask.getchannel('A')))))
    slots = []
    for x, y, w, h, n, _ in components(src, (139, 139, 139)):
        if n == w * h and is_framed(src, x, y, w, h) and max(w, h) <= 40:
            # Remove the old bevel before drawing the inventory's inset slot tile.
            ImageDraw.Draw(out).rectangle((x - 1, y - 1, x + w, y + h), fill=col('panel.fill'))
            well(out, x - 1, y - 1, w + 2, h + 2)
            slots.append((x, y, w, h))
    if os.path.basename(path) == 'crafter.png':
        # The crafter uses a different bevel, so it cannot share vanilla slot detection.
        for x, y, w, h in TOK['container.crafter_slots']:
            ImageDraw.Draw(out).rectangle((x, y, x + w - 1, y + h - 1), fill=col('panel.fill'))
            well(out, x, y, w, h)
            slots.append((x + 1, y + 1, w - 2, h - 2))
    for x, y, w, h, n, _ in components(src, (0, 0, 0)):
        if n == w * h and min(w, h) > 30:
            liquid_glass(out, x, y, w, h, TOK['radius.glass'],
                         tint='liquid.well_tint_top', tint_bottom='liquid.well_tint_bottom',
                         edge='liquid.edge_on_light', shadow=False)
    return out, slots


def build_remaining_containers(root):
    report = {}
    directory = os.path.join(VAN, 'container')
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith('.png') or filename == 'inventory.png':
            continue
        image, slots = build_container_screen(os.path.join(directory, filename))
        save(image, root, 'container/' + filename)
        report[filename] = len(slots)
    sprite_dir = os.path.join(VAN, 'sprites', 'container')
    for directory, _, filenames in os.walk(sprite_dir):
        for filename in sorted(filenames):
            if not filename.endswith('.png'):
                continue
            path = os.path.join(directory, filename)
            rel = os.path.relpath(path, VAN)
            dest = os.path.join(root, 'assets/minecraft/textures/gui', rel)
            if os.path.exists(dest):
                continue  # Keep the existing creative and hover treatments.
            src = Image.open(path).convert('RGBA')
            name = filename[:-4]
            danger = name in ('error', 'out_of_stock', 'trade_arrow_out_of_stock', 'cancel')
            accent = name in ('burn_progress', 'brew_progress', 'fuel_length',
                              'experience_bar_current', 'experience_bar_result', 'confirm')
            image = container_palette(src, accent=accent, danger=danger)
            if name in ('button', 'button_disabled', 'button_highlighted', 'button_selected',
                        'recipe', 'recipe_selected', 'recipe_highlighted', 'pattern',
                        'pattern_selected', 'pattern_highlighted', 'enchantment_slot',
                        'enchantment_slot_disabled', 'enchantment_slot_highlighted'):
                image = Image.new('RGBA', src.size)
                token = ('accent.fill' if name.endswith(('highlighted', 'selected')) else
                         'disabled.fill' if name.endswith('disabled') else
                         'control.fill' if name.startswith('enchantment') else 'slot.tile')
                radius = min(TOK['radius.slot'], (min(src.size) - 1) // 2)
                pad = TOK['recipe.tile_inset'] if name.startswith(('recipe', 'pattern')) else 0
                rrect(image, pad, pad, src.width - 2 * pad, src.height - 2 * pad, radius, col(token))
            if name in ('text_field', 'text_field_disabled'):
                # Anvil labels are white: keep the rename field dark enough to read.
                a = np.array(image)
                a[:, :, :3] = col('control.fill' if name == 'text_field' else 'disabled.fill')[:3]
                image = Image.fromarray(a, 'RGBA')
            if rel == 'sprites/container/horse/chest_slots.png':
                image, _ = build_container_screen(path)
            meta_path = path + '.mcmeta'
            meta = json.load(open(meta_path)) if os.path.exists(meta_path) else None
            save(image, root, rel, meta)
    return report


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
    box around them. Trapezoid narrowing towards the back (perspective), soft back-edge glow, faint front
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
    # back edge: a very soft glow fading into the surface (no hard line)
    _over(img, (1, 1, 1), lip[3] * cov * np.clip(1 - (py - top) / TOK['shelf.lip_feather'], 0, 1) ** 2)
    _over(img, (1, 1, 1), front[3] * cov * np.clip(1 - (bot - py) / 0.75, 0, 1))
    if rim:  # optional outline around the whole shelf
        edge = cov - np.asarray(big.filter(__import__('PIL.ImageFilter', fromlist=['MinFilter']).MinFilter(2 * ss + 1))
                                .resize((W * s, H * s), Image.BOX), dtype=np.float64) / 255.0
        _over(img, (1, 1, 1), np.clip(edge, 0, 1) * (TOK['liquid.rim_max'] / 255) * 0.8)
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')


def build_xp_bar(progress=False, fill='xp.fill', width=None, markers=True):
    """Match the shelf glass at 2x while retaining vanilla's logical dimensions."""
    w, h, scale = width or TOK['xp.width'], TOK['xp.height'], TOK['xp.scale']
    if not progress:
        im = liquid_glass_hd(w, h, 0, 0, w, h, TOK['xp.radius'],
                             underlay='xp.track', tint='xp.tint', scale=scale, rim=False)
        return bar_markers(im, TOK['xp.markers'], True) if markers else im
    ys, xs = np.mgrid[0:h * scale, 0:w * scale]
    d, _, _ = _sdf((xs + 0.5) / scale, (ys + 0.5) / scale,
                    w / 2, h / 2, w / 2, h / 2, TOK['xp.radius'])
    rgba = np.empty((h * scale, w * scale, 4), dtype=np.uint8)
    rgba[:] = col(fill)
    rgba[:, :, 3] = (np.clip(0.5 - d * scale, 0, 1) * col(fill)[3]).round().astype(np.uint8)
    # Vanilla crops this fixed sprite: intermediate values necessarily have a straight right edge.
    im = Image.fromarray(rgba, 'RGBA')
    return bar_markers(im, TOK['xp.markers'], False) if markers else im


def bar_markers(im, positions, background):
    pixels = np.array(im)
    scale = TOK['xp.scale']
    y0 = round(TOK['jump.marker_inset'] * scale)
    y1 = im.height - y0
    width = max(1, round(TOK['jump.marker_width'] * scale))
    marker = np.array(col('jump.marker_track' if background else 'jump.marker'))
    alpha = marker[3] / 255
    for x in positions:
        region = pixels[y0:y1, x * scale:x * scale + width, :3]
        region[:] = (region * (1 - alpha) + marker[:3] * alpha).round().astype(np.uint8)
    return Image.fromarray(pixels, 'RGBA')


def build_jump_bar(state='background'):
    im = build_xp_bar(state != 'background',
                      'jump.cooldown' if state == 'cooldown' else 'jump.fill', markers=False)
    scale = TOK['xp.scale']
    pixels = np.array(im)
    if state == 'progress':
        pixels[:, TOK['jump.limit_start'] * scale:, :3] = col('jump.limit_fill')[:3]
    return bar_markers(Image.fromarray(pixels, 'RGBA'), TOK['jump.markers'], state == 'background')



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
    return build_selection_bubble()



def build_selection_bubble():
    """Inset the glass around a 16px item, retaining lower-right room for stack counts."""
    return liquid_glass_hd(24, 23, TOK['selection.x'], TOK['selection.y'],
                           TOK['selection.width'], TOK['selection.height'],
                           TOK['selection.radius'], tint='liquid.lens_tint')


def build_offhand(side, rim=False, underlay='liquid.underlay_hud'):
    return liquid_glass_hd(29, 24, 0 if side == 'left' else 7, 1, 22, 23, TOK['radius.dock'], underlay=underlay,
                           rim=rim)


def build_highlight(which):
    im = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
    pad = 3 + TOK['slot.tile_inset']
    rrect(im, pad, pad, 24 - 2 * pad, 24 - 2 * pad, TOK['radius.slot'], col('highlight.' + which))
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
    """8x20 slider handle in Liquid Glass (HD): clear glass knob with specular rim at rest,
    Apple-blue glass while hovered/dragged. Inset 1px so it stays inside the pill's rounded ends."""
    if highlighted:
        return liquid_glass_hd(8, 20, 1, 2, 6, 17, 3, underlay=TOK['knob.glass_active'], shadow=True)
    return liquid_glass_hd(8, 20, 1, 2, 6, 17, 3, tint='knob.glass_tint', shadow=True)


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
    """pack.png: the macUI logo filling the icon (design/logo/logo-icon.png: native pixels with a
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


NS = 'macui'
VERSION = '1.0.0'   # single source for the pack title and the zip name
FORMATS = ([75, 0], 97)   # min 1.21.11; max 26.3.x (any 97 minor)


# ---------------------------------------------------------------- optional in-game settings (Respackopts)
# Bonus for players who install the Respackopts mod. Without the mod Minecraft ignores
# respackopts.json5 and every .rpo file, so the pack behaves exactly as the defaults below.
# Alternative files live in assets/macui/alt/, which no vanilla loader reads.
RPO_CONF = {
    'id': 'macUi', 'version': 13, 'capabilities': ['FileFilter', 'DirFilter', 'DirFilterAdditive'],
    'conf': {
        'hud': {
            'selectionBubble': True,
            'hotbarStyle': {'type': 'enum', 'default': 'shelf', 'values': ['shelf', 'dock']},
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
        '': 'macUI', 'hud': 'Hotbar and HUD',
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
        '': 'macUI', 'hud': 'Barra rápida y HUD',
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
RPO_LANG = {lang: {('rpo.macUi' + ('.' + k if k else '')): v for k, v in d.items()} for lang, d in _L.items()}


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
    alt = f'assets/{NS}/alt/'
    _write_json(root, 'respackopts.json5', RPO_CONF)
    for lang, entries in RPO_LANG.items():
        _write_json(root, f'assets/{NS}/lang/{lang}.json', entries)
    n = 0

    # hud.selectionBubble ---------------------------------------------------------------------
    save_at(Image.new('RGBA', build_selection().size, (0, 0, 0, 0)),
            root, alt + 'bubble/hotbar_selection.png')
    _write_json(root, gui + 'sprites/hud/hotbar_selection.png.rpo',
                {'condition': 'hud.selectionBubble', 'fallbacks': [alt + 'bubble/hotbar_selection.png']}); n += 1

    # hud.hotbarStyle x hud.hotbarOpacity x hud.hotbarOutline -> one file per combination -------
    combos = [(st, o, rim) for st in ('shelf', 'dock') for o in TOK['hotbar.opacity'] for rim in (False, True)]
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
            if (st, o, rim) == ('shelf', 'clear', False):   # the pack's default look
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
    # 26.2+ friends list and 26.3+ Realms buttons follow the same shape option.
    for folder, prefix in NEWER_BUTTONS:
        for st, suf in (('normal', ''), ('highlighted', '_highlighted'), ('disabled', '_disabled')):
            rel = f'sprites/{folder}/{prefix}{suf}.png'
            save_at(build_button(st, rr), root, alt + 'rounded/' + rel, nine(200, 20, rr))
            for ext in ('', '.mcmeta'):
                _rpo(root, gui + rel + ext, 'widgets.buttonShape.pill', alt + 'rounded/' + rel + ext); n += 1

    # inventory.glassPlayerArea: opaque tile instead of glass when off ---------------------------
    inv, _ = build_inventory(glass=False)
    tab, _ = repaint_container(os.path.join(VAN, 'container', 'creative_inventory', 'tab_inventory.png'), glass=False)
    for rel, im in (('container/inventory.png', inv), ('container/creative_inventory/tab_inventory.png', tab)):
        save_at(im, root, alt + 'opaque/' + rel)
        _rpo(root, gui + rel, 'inventory.glassPlayerArea', alt + 'opaque/' + rel); n += 1
    return n


# ---------------------------------------------------------------- sprites added after 1.21.11
# Minecraft 26.x only adds GUI sprites (no 1.21.11 sprite was renamed or resized), so these live in
# the base pack: older versions simply never read the new paths. Icons stay vanilla, as elsewhere.
NEWER_BUTTONS = (('friends', 'button'), ('widget', 'realms_button'))   # 26.2 friends list, 26.3 Realms


def build_card(dark):
    """236x34 friends-list row (white text): graphite card; the dark variant has a black edge."""
    im = Image.new('RGBA', (236, 34), (0, 0, 0, 0))
    r = TOK['notification.radius']
    rrect(im, 0, 0, 236, 34, r, col('control.edge' if dark else 'field.edge'))
    rrect(im, 1, 1, 234, 32, r - 1, col('control.fill'))
    if not dark:
        hline(im, r, 1, 236 - 2 * r, col('control.top'))
    return im


def build_preedit():
    """26.1+ IME composition box (dark text on white): white field with the accent focus edge."""
    im = Image.new('RGBA', (200, 20), (0, 0, 0, 0))
    rrect(im, 0, 0, 200, 20, 3, col('accent.fill'))
    rrect(im, 1, 1, 198, 18, 2, col('panel.highlight'))
    return im


def build_newer_version_sprites(root, border):
    n = 0
    for folder, prefix in NEWER_BUTTONS:
        for st, suf in (('normal', ''), ('highlighted', '_highlighted'), ('disabled', '_disabled')):
            save(build_button(st, TOK['radius.button']), root, f'sprites/{folder}/{prefix}{suf}.png',
                 nine(200, 20, border)); n += 1
    save(build_card(False), root, 'sprites/friends/background.png', nine(236, 34, 8)); n += 1
    save(build_card(True), root, 'sprites/friends/background_dark.png', nine(236, 34, 6)); n += 1
    toast = liquid_glass_hd(160, 32, 0, 0, 160, 32, TOK['radius.dock'], underlay='liquid.underlay_hud',
                            scale=TOK['hd.scale_hotbar'], rim=False)
    save(toast, root, 'sprites/friends/toast_background.png', nine(160, 32, 10)); n += 1   # border >= glass radius
    save(build_preedit(), root, 'sprites/widget/preedit.png', nine(200, 20, 3)); n += 1
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


def build_advancements_notifications(root):
    """Keep all canvases, distinct advancement silhouettes and nine-slice metadata."""
    groups = ('advancements', 'sprites/advancements', 'sprites/toast',
              'sprites/notification', 'sprites/popup')
    count = 0
    for group in groups:
        for directory, _, filenames in os.walk(os.path.join(VAN, group)):
            for filename in sorted(filenames):
                if not filename.endswith('.png'):
                    continue
                path = os.path.join(directory, filename)
                rel = os.path.relpath(path, VAN)
                src = Image.open(path).convert('RGBA')
                stem = filename[:-4]
                image = container_palette(src)
                if group == 'advancements' and 'backgrounds' in rel:
                    pixels = np.array(src)
                    luminance = pixels[:, :, :3].mean(axis=2)
                    tint = np.array(_hexc(TOK['advancement.backgrounds'][stem])[:3])
                    variation = (luminance - luminance.mean()) * TOK['advancement.texture_strength']
                    pixels[:, :, :3] = np.clip(tint + variation[:, :, None], 0, 255).astype(np.uint8)
                    image = Image.fromarray(pixels, 'RGBA')
                elif group == 'sprites/advancements':
                    if stem.startswith('box_') or stem == 'title_box':
                        # Advancement descriptions are white; retain a graphite surface.
                        image = Image.new('RGBA', src.size)
                        r = TOK['notification.radius']
                        edge = 'accent.fill' if stem == 'box_obtained' else 'control.top'
                        rrect(image, 0, 0, *src.size, r, col(edge))
                        rrect(image, 1, 1, src.width - 2, src.height - 2, r - 1, col('control.fill'))
                    elif '_frame_' in stem:
                        pixels = np.array(image)
                        original = np.array(src)
                        opaque = original[:, :, 3] > 0
                        # Preserve task/goal/challenge shapes so status is not color-only.
                        edge = (original[:, :, :3].mean(axis=2) < 90) & opaque
                        obtained = stem.endswith('_obtained')
                        pixels[:, :, :3][opaque] = col('accent.fill' if obtained else 'slot.tile')[:3]
                        pixels[:, :, :3][edge] = col('accent.edge' if obtained else 'panel.edge')[:3]
                        image = Image.fromarray(pixels, 'RGBA')
                    elif stem.startswith('tab_'):
                        pixels = np.array(image)
                        original = np.array(src)
                        body = (original[:, :, :3].mean(axis=2) > 100) & (original[:, :, 3] > 0)
                        pixels[:, :, :3][body] = col('panel.fill' if stem.endswith('_selected') else 'tab.unselected')[:3]
                        image = Image.fromarray(pixels, 'RGBA')
                elif (group == 'sprites/toast' and src.width >= 100) or group == 'sprites/popup':
                    image = liquid_glass_hd(src.width, src.height, 0, 0, src.width, src.height,
                                            TOK['radius.dock'],
                                            underlay='liquid.underlay_hud',
                                            scale=TOK['hd.scale_hotbar'], rim=False)
                    if stem == 'system':
                        # Retain the warning symbol at its original UV position.
                        pixels = np.array(src.resize(image.size, Image.Resampling.NEAREST))
                        symbol = (pixels[:, :, 0] > 180) & (pixels[:, :, 1] > 150) & (pixels[:, :, 2] < 120)
                        target = np.array(image)
                        target[symbol] = pixels[symbol]
                        image = Image.fromarray(target, 'RGBA')
                elif group == 'sprites/notification':
                    pixels = np.array(src)
                    red = (pixels[:, :, 0] > pixels[:, :, 1].astype(int) * 1.5) & (pixels[:, :, 3] > 0)
                    pixels[:, :, :3][red] = col('notification.badge')[:3]
                    image = Image.fromarray(pixels, 'RGBA')
                elif group == 'sprites/toast':
                    # Keep recognizable tutorial/item art; only restyle neutral UI pixels.
                    pixels = np.array(image)
                    original = np.array(src)
                    colorful = (original[:, :, :3].max(axis=2).astype(int) - original[:, :, :3].min(axis=2)) >= 12
                    pixels[colorful] = original[colorful]
                    image = Image.fromarray(pixels, 'RGBA')
                meta_path = path + '.mcmeta'
                save(image, root, rel, json.load(open(meta_path)) if os.path.exists(meta_path) else None)
                count += 1
    return count


def build_shulker_colors(root):
    """Optional OptiGUI/OptiFine variants; vanilla keeps the untinted texture."""
    base = Image.open(os.path.join(root, 'assets/minecraft/textures/gui/container/shulker_box.png')).convert('RGBA')
    source = np.array(base)
    for color, hex_color in TOK['shulker.colors'].items():
        pixels = source.copy()
        tint = np.array(_hexc(hex_color)[:3])
        for token in ('panel.fill', 'panel.edge', 'panel.highlight', 'panel.shade', 'slot.tile'):
            mask = np.all(source[:, :, :3] == col(token)[:3], axis=2) & (source[:, :, 3] > 0)
            amount = TOK['shulker.slot_tint' if token == 'slot.tile' else 'shulker.panel_tint']
            pixels[:, :, :3][mask] = np.round(np.array(col(token)[:3]) * (1 - amount) + tint * amount).astype(np.uint8)
        texture = f'assets/{NS}/textures/gui/shulker/{color}.png'
        save_at(Image.fromarray(pixels, 'RGBA'), root, texture)
        block = 'shulker_box' if color == 'undyed' else color + '_shulker_box'
        replacement = f'{NS}:textures/gui/shulker/{color}.png'
        _write_json(root, f'assets/{NS}/optigui/gui/shulker/{color}.json',
                    {'containers': 'minecraft:' + block,
                     'textures': {'minecraft:textures/gui/container/shulker_box.png': replacement}})
        # No name filter: ordinary and renamed boxes share the clear title area.
        # The undyed fallback sorts after every explicit dye rule.
        filename = 'z_undyed' if color == 'undyed' else color
        properties = os.path.join(root, 'assets/minecraft/optifine/gui/container/macui_shulker',
                                  filename + '.properties')
        os.makedirs(os.path.dirname(properties), exist_ok=True)
        with open(properties, 'w', encoding='utf-8') as stream:
            stream.write(f'container=shulker_box\ntexture={replacement}\n')
            if color != 'undyed':
                stream.write(f'colors={color}\n')
        # OptiGUI 2 uses INI; OptiGUI 3 uses the JSON resources above.
        rel = f'assets/optigui/gui/macui_shulker/{color}.ini'
        dest = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'w', encoding='utf-8') as stream:
            stream.write(f'[{block}]\nreplacement = {replacement}\n')


def build_panorama(root):
    """Install the owner-captured snowy taiga panorama unchanged."""
    source = os.path.join(REPO, 'design', 'panorama', 'snowy-taiga')
    for index in range(6):
        filename = f'panorama_{index}.png'
        dest = os.path.join(root, 'assets/minecraft/textures/gui/title/background', filename)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(os.path.join(source, filename), dest)
    shutil.copyfile(os.path.join(source, 'SOURCE.txt'), os.path.join(root, 'PANORAMA-SOURCE.txt'))


def build_text_font(root):
    """Bake Monocraft at its pixel size instead of Minecraft's smoothed TTF provider."""
    font_dir = os.path.join(REPO, 'design', 'fonts')
    font = ImageFont.truetype(os.path.join(font_dir, 'Monocraft.ttf'), TOK['font.text.size'])
    characters = ''.join(chr(code) for code in range(33, 256)
                         if not 127 <= code <= 160 and code != 173)
    columns, cell = TOK['font.text.columns'], TOK['font.text.cell']
    rows = [characters[i:i + columns].ljust(columns, '\0') for i in range(0, len(characters), columns)]
    atlas = Image.new('RGBA', (columns * cell, len(rows) * cell))
    for row, chars in enumerate(rows):
        for column, char in enumerate(chars):
            if char == '\0':
                continue
            glyph = Image.new('L', (cell, cell))
            draw = ImageDraw.Draw(glyph)
            draw.fontmode = '1'
            draw.text((0, TOK['font.text.ascent']), char, font=font, fill=255, anchor='ls')
            # Binary alpha keeps glyphs crisp at every integer GUI scale.
            glyph = glyph.point(lambda alpha: 255 if alpha >= 128 else 0)
            colored = Image.new('RGBA', glyph.size, 'white')
            colored.putalpha(glyph)
            atlas.alpha_composite(colored, (column * cell, row * cell))
    save_at(atlas, root, f'assets/{NS}/textures/font/monocraft.png')
    default = json.load(open(os.path.join(REF, 'assets', 'minecraft', 'font', 'default.json')))
    default['providers'].insert(0, {'type': 'bitmap', 'file': f'{NS}:font/monocraft.png',
                                   'height': cell, 'ascent': TOK['font.text.ascent'], 'chars': rows})
    _write_json(root, 'assets/minecraft/font/default.json', default)
    shutil.copyfile(os.path.join(font_dir, 'Monocraft-OFL.txt'), os.path.join(root, 'Monocraft-OFL.txt'))


def build_pack(name, desc, btn_r):
    root = os.path.join(OUT, name)
    shutil.rmtree(root, ignore_errors=True); os.makedirs(root)
    json.dump({"pack": {"description": desc, "min_format": FORMATS[0], "max_format": FORMATS[1]}},
              open(os.path.join(root, 'pack.mcmeta'), 'w'), indent=2, ensure_ascii=False)
    build_icon().save(os.path.join(root, 'pack.png'))
    build_text_font(root)
    build_panorama(root)
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
    for progress, suffix in ((False, 'background'), (True, 'progress')):
        save(build_xp_bar(progress), root, f'sprites/hud/experience_bar_{suffix}.png')
    for state in ('background', 'progress', 'cooldown'):
        save(build_jump_bar(state), root, f'sprites/hud/jump_bar_{state}.png')
    locator_meta = json.load(open(os.path.join(VAN, 'sprites/hud/locator_bar_background.png.mcmeta')))
    save(build_xp_bar(width=TOK['locator.width'], markers=False), root,
         'sprites/hud/locator_bar_background.png', locator_meta)
    # Keep vanilla's player tinting, arrow animation and marker silhouettes intact.
    save(build_hotbar_shelf(), root, 'sprites/hud/hotbar.png')          # default: Liquid Glass shelf
    save(build_selection(), root, 'sprites/hud/hotbar_selection.png')   # glass selection bubble by default
    save(build_offhand_shelf('left'), root, 'sprites/hud/hotbar_offhand_left.png')
    save(build_offhand_shelf('right'), root, 'sprites/hud/hotbar_offhand_right.png')
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
    report['containers'] = build_remaining_containers(root)
    build_shulker_colors(root)
    report['advancements_notifications'] = build_advancements_notifications(root)
    report['newer_versions'] = build_newer_version_sprites(root, border)
    report['rpo_files'] = build_options(root)
    z = os.path.join(OUT, name + '.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for d, _, fs in os.walk(root):
            for f in fs:
                full = os.path.join(d, f); zf.write(full, os.path.relpath(full, root))
    return report


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    rep = build_pack(f'macUI-Light-{VERSION}', f'§fmacUI §7— Light\n§8v{VERSION}', TOK['radius.button'])
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in rep.items()}))
