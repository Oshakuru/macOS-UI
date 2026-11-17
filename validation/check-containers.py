"""Check complete container coverage and unchanged canvas/metadata contracts."""
import json
from pathlib import Path
from PIL import Image
root = Path(__file__).resolve().parents[1]
source = root / 'reference/vanilla-1.21.11/assets/minecraft/textures/gui'
pack = root / 'dist/macUI-Light-0.39/assets/minecraft/textures/gui'
count = 0
for folder in ('container', 'sprites/container'):
    for path in (source / folder).rglob('*.png'):
        rel = path.relative_to(source)
        dest = pack / rel
        assert dest.is_file(), rel
        before, after = Image.open(path), Image.open(dest)
        # Existing creative/hover sprites intentionally use HD textures.
        if 'creative_inventory' not in str(rel) and 'slot_highlight' not in str(rel):
            assert before.size == after.size, rel
        meta = Path(str(path) + '.mcmeta')
        if meta.exists() and 'creative_inventory' not in str(rel) and 'slot_highlight' not in str(rel):
            assert json.loads(meta.read_text()) == json.loads(Path(str(dest) + '.mcmeta').read_text()), rel
        count += 1
for name, coords in {'crafting_table':[(30,17),(48,17),(66,17),(124,35)],
                     'anvil':[(27,47),(76,47),(134,47)]}.items():
    im = Image.open(pack / ('container/' + name + '.png'))
    for x,y in coords:
        assert im.getpixel((x+8,y+8))[:3] == (229,229,234), (name,x,y)
print(f'PASS: {count} container assets present, dimensions/metadata preserved, crafting/anvil slots aligned')

import configparser
pack_root = pack.parents[3]
base = Image.open(pack / 'container/shulker_box.png').convert('RGBA')
rules = list((pack_root / 'assets/macui/optigui/gui/shulker').glob('*.json'))
assert len(rules) == 17
blocks = set()
for path in rules:
    rule = json.loads(path.read_text())
    assert rule['containers'] not in blocks
    blocks.add(rule['containers'])
    replacement = rule['textures']['minecraft:textures/gui/container/shulker_box.png']
    ns, rel = replacement.split(':', 1)
    variant = Image.open(pack_root / 'assets' / ns / rel).convert('RGBA')
    assert variant.size == base.size
    assert variant.getchannel('A').tobytes() == base.getchannel('A').tobytes()
    ini = configparser.ConfigParser()
    ini.read(pack_root / 'assets/optigui/gui/macui_shulker' / (path.stem + '.ini'))
    assert ini[rule['containers'].split(':')[1]]['replacement'] == replacement
print('PASS: 17 unique color rules, matching INI/JSON paths and unchanged alpha/layout')

properties_dir = pack_root / 'assets/minecraft/optifine/gui/container/macui_shulker'
assert len(list(properties_dir.glob('*.properties'))) == 17
for path in properties_dir.glob('*.properties'):
    values = dict(line.split('=', 1) for line in path.read_text().splitlines() if line)
    assert values['container'] == 'shulker_box'
    assert 'name' not in values  # Both original and custom names must match.
    ns, rel = values['texture'].split(':', 1)
    assert (pack_root / 'assets' / ns / rel).is_file()
    if path.stem != 'z_undyed':
        assert values['colors'] == path.stem
    else:
        assert 'colors' not in values
print('PASS: 17 OptiFine rules, texture targets and unrestricted custom names')
