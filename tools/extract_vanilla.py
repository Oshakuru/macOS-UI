"""Extract the vanilla GUI reference assets from a Minecraft client jar.

Usage:
    python3 tools/extract_vanilla.py path/to/minecraft-1.21.11-client.jar

Writes to reference/vanilla-<version>/ (git-ignored: Mojang assets are never committed)
and regenerates docs/vanilla-<version>-gui-sprites.tsv (path, size, .mcmeta) for review.

Prism Launcher keeps the jar at:
    <Prism data>/libraries/com/mojang/minecraft/<version>/minecraft-<version>-client.jar
"""
import json, os, sys, zipfile
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIXES = ('assets/minecraft/textures/gui/', 'assets/minecraft/font/', 'assets/minecraft/lang/en_us.json',
            'assets/minecraft/items/', 'assets/minecraft/models/')


def main(jar):
    with zipfile.ZipFile(jar) as zf:
        info = json.loads(zf.read('version.json'))
        version = info['id']
        fmt = info['pack_version']
        out = os.path.join(REPO, 'reference', f'vanilla-{version}')
        n = 0
        for name in zf.namelist():
            if name.startswith(PREFIXES) and not name.endswith('/'):
                dest = os.path.join(out, name)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, 'wb') as fh:
                    fh.write(zf.read(name))
                n += 1
    print(f'{version}: resource pack format {fmt["resource_major"]}.{fmt["resource_minor"]}, {n} files -> {out}')

    gui = os.path.join(out, 'assets', 'minecraft', 'textures', 'gui')
    rows = []
    for d, _, fs in os.walk(gui):
        for f in sorted(fs):
            if f.endswith('.png'):
                p = os.path.join(d, f)
                meta = ''
                if os.path.exists(p + '.mcmeta'):
                    meta = json.dumps(json.load(open(p + '.mcmeta')), separators=(',', ':'))
                w, h = Image.open(p).size
                rows.append(f'{os.path.relpath(p, gui)}\t{w}x{h}\t{meta}')
    tsv = os.path.join(REPO, 'docs', f'vanilla-{version}-gui-sprites.tsv')
    with open(tsv, 'w') as fh:
        fh.write('\n'.join(sorted(rows)) + '\n')
    print(f'{len(rows)} GUI images listed in {os.path.relpath(tsv, REPO)}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
