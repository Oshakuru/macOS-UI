"""Run after tools/build.py: validate HUD sizes, metadata and GUI-only scope."""
import json
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
pack = root / 'dist/macUI-Light-0.29'
hud = pack / 'assets/minecraft/textures/gui/sprites/hud'
for name in ('experience_bar_background', 'experience_bar_progress', 'jump_bar_background',
             'jump_bar_progress', 'jump_bar_cooldown'):
    im = Image.open(hud / (name + '.png'))
    assert im.size == (364, 10), (name, im.size)
    assert im.mode == 'RGBA'
    assert im.getpixel((0, 0))[3] == 0
    assert im.getbbox() is not None
fill = Image.open(hud / 'experience_bar_progress.png')
for logical_width in (0, 1, 91, 182):
    crop = fill.crop((0, 0, logical_width * 2, 10))
    assert crop.width == logical_width * 2
    if logical_width:
        assert crop.getpixel((crop.width - 1, 5))[3] > 0
assert Image.open(hud / 'locator_bar_background.png').size == (24, 10)
meta = json.loads((hud / 'locator_bar_background.png.mcmeta').read_text())
assert meta['gui']['scaling']['width'] == 12
assert meta['gui']['scaling']['height'] == 5
assert (pack / 'assets/minecraft/items').is_dir()
assert json.loads((pack / 'pack.mcmeta').read_text())['pack']['min_format'] == [75, 0]
print('PASS: HUD sizes, alpha, 2x crop coordinates, locator metadata, format and integrated item scope')

progress = Image.open(hud / 'jump_bar_progress.png')
cooldown = Image.open(hud / 'jump_bar_cooldown.png')
assert progress.getpixel((160 * 2, 5))[:3] == (0, 113, 227)
assert progress.getpixel((162 * 2, 5))[:3] == (255, 59, 48)
assert progress.getpixel((172 * 2, 5))[:3] == (255, 59, 48)
assert progress.getpixel((20 * 2, 5))[:3] != progress.getpixel((21 * 2, 5))[:3]
assert cooldown.getpixel((172 * 2, 5))[:3] == (142, 142, 147)
print('PASS: jump markers, final two red sections and grey cooldown')

for name in ('experience_bar_background', 'experience_bar_progress'):
    im = Image.open(hud / (name + '.png'))
    assert im.getpixel((20 * 2, 5)) != im.getpixel((21 * 2, 5))
assert fill.getpixel((172 * 2, 5))[:3] == (52, 199, 89)
print('PASS: XP markers on track and fill; XP remains green')

selection = Image.open(hud / 'hotbar_selection.png')
assert selection.size == (96, 92)
assert selection.getbbox() is not None
assert Image.open(pack / 'assets/macui/alt/bubble/hotbar_selection.png').getbbox() is None
conf = json.loads((pack / 'respackopts.json5').read_text())
assert conf['conf']['hud']['selectionBubble'] is True
rule = json.loads((hud / 'hotbar_selection.png.rpo').read_text())
assert rule['condition'] == 'hud.selectionBubble'
print('PASS: default glass bubble and optional hidden selection')

assert conf['conf']['hud']['magnification']['default'] == 'off'
items_rule = json.loads((pack / 'assets/minecraft/items/.rpo').read_text())
assert items_rule['condition'] == '!hud.magnification.off'
models = list((pack / 'assets/macui/models/magnified').rglob('*.json'))
assert models
for model in models:
    wrapper = json.loads(model.read_text())
    # Off uses the original inherited GUI scale, rather than a magnification multiplier.
    assert 'gui' in wrapper['display']
for sub, key in (('', 'large'), ('m/', 'normal'), ('m/m/', 'small')):
    rule = json.loads((pack / ('assets/macui/models/magnified/' + sub + '.rpo')).read_text())
    assert rule['condition'] == '!hud.magnification.' + key
    assert (pack / rule['fallback']).is_dir()
print('PASS: integrated magnification defaults off and all size alternatives exist')

providers = json.loads((pack / 'assets/minecraft/font/default.json').read_text())['providers']
assert providers[0]['chars'] == ['0123456789']
vanilla = root / 'reference/vanilla-1.21.11/assets/minecraft/font/default.json'
assert providers[1:] == json.loads(vanilla.read_text())['providers']
atlas = Image.open(pack / 'assets/macui/textures/font/numbers.png')
assert atlas.size == (160, 16)
for i in range(10):
    glyph = atlas.crop((i * 16, 0, (i + 1) * 16, 16))
    assert glyph.getbbox() is not None
    assert glyph.getbbox()[2] < 16 and glyph.getbbox()[3] < 16
assert (pack / 'Manrope-OFL.txt').is_file()
print('PASS: ten Manrope digits, unclipped atlas, vanilla fallback and bundled license')

box = selection.getbbox()
assert box[0] >= 6 and box[1] >= 6, box
assert box[2] <= 90 and box[3] <= 90, box
assert selection.getpixel((20 * 4, 18 * 4))[3] > 0
print('PASS: tighter inset bubble and lower-right stack-count area')
