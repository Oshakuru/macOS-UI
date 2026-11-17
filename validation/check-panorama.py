"""Verify the selected panorama is packaged unchanged."""
from pathlib import Path
from PIL import Image
root = Path(__file__).resolve().parents[1]
VERSION = __import__('re').search(r"VERSION = '([^']+)'", (root / 'tools/build.py').read_text()).group(1)
source = root / 'design/panorama/snowy-taiga'
folder = root / f'dist/macUI-Light-{VERSION}/assets/minecraft/textures/gui/title/background'
for i in range(6):
    name = f'panorama_{i}.png'
    assert (folder / name).read_bytes() == (source / name).read_bytes()
    assert Image.open(folder / name).size == (1024, 1024)
assert (root / f'dist/macUI-Light-{VERSION}' / 'PANORAMA-SOURCE.txt').is_file()
print('PASS: six original 1024px panorama faces and source/license notice')
