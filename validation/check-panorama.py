"""Verify the selected panorama is packaged unchanged."""
from pathlib import Path
from PIL import Image
root = Path(__file__).resolve().parents[1]
source = root / 'design/panorama/snowy-taiga'
folder = root / 'dist/macUI-Light-1.0.0/assets/minecraft/textures/gui/title/background'
for i in range(6):
    name = f'panorama_{i}.png'
    assert (folder / name).read_bytes() == (source / name).read_bytes()
    assert Image.open(folder / name).size == (1024, 1024)
assert (root / 'dist/macUI-Light-1.0.0' / 'PANORAMA-SOURCE.txt').is_file()
print('PASS: six original 1024px panorama faces and source/license notice')
