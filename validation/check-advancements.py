"""Verify advancement/notification coverage, layout and semantic shapes."""
import json
from pathlib import Path
from PIL import Image
root = Path(__file__).resolve().parents[1]
VERSION = __import__('re').search(r"VERSION = '([^']+)'", (root / 'tools/build.py').read_text()).group(1)
source = root / 'reference/vanilla-1.21.11/assets/minecraft/textures/gui'
pack = root / f'dist/macUI-Light-{VERSION}/assets/minecraft/textures/gui'
count = 0
for group in ('advancements', 'sprites/advancements', 'sprites/toast', 'sprites/notification', 'sprites/popup'):
    for path in (source / group).rglob('*.png'):
        rel = path.relative_to(source)
        before, after = Image.open(path).convert('RGBA'), Image.open(pack / rel).convert('RGBA')
        glass = (group == 'sprites/toast' and before.width >= 100) or group == 'sprites/popup'
        expected = (before.width * 2, before.height * 2) if glass else before.size
        assert after.size == expected, rel
        if not (group == 'sprites/toast' and before.width == 20):
            assert before.tobytes() != after.tobytes(), rel
        meta = Path(str(path) + '.mcmeta')
        if meta.exists():
            assert json.loads(meta.read_text()) == json.loads(Path(str(pack / rel) + '.mcmeta').read_text()), rel
        if '_frame_' in path.name or group == 'sprites/notification' or rel.as_posix() == 'advancements/window.png':
            assert before.getchannel('A').tobytes() == after.getchannel('A').tobytes(), rel
        count += 1
assert count == 58
for state in ('obtained', 'unobtained'):
    silhouettes = {Image.open(pack / f'sprites/advancements/{shape}_frame_{state}.png').getchannel('A').tobytes()
                   for shape in ('task', 'goal', 'challenge')}
    assert len(silhouettes) == 3
for name in ('advancement', 'now_playing', 'system', 'recipe', 'tutorial'):
    image = Image.open(pack / f'sprites/toast/{name}.png')
    assert 0 < image.getpixel((160, 32))[3] < 255
print('PASS: 58 assets, 2x glass panels, preserved logical metadata and translucent bodies')

recipe = Image.open(pack / 'sprites/toast/recipe.png').convert('RGBA')
advancement = Image.open(pack / 'sprites/toast/advancement.png').convert('RGBA')
assert recipe.tobytes() == advancement.tobytes()
print('PASS: recipe and advancement toast glass match exactly')

for name in ('tutorial', 'now_playing'):
    assert Image.open(pack / f'sprites/toast/{name}.png').convert('RGBA').tobytes() == advancement.tobytes()
system = Image.open(pack / 'sprites/toast/system.png').convert('RGBA')
assert system.getpixel((160, 32)) == advancement.getpixel((160, 32))
assert system.getpixel((160, 64))[3] < 255
print('PASS: all five toast backgrounds and popup panel share advancement glass; system warning preserved')
