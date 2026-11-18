<p align="center"><img src="design/logo/logo-source.png" width="160" alt="macUI logo"></p>

# macUI

Bring Apple's vibe to Minecraft's UI with a slick, minimalist style, while staying 100% vanilla.

A GUI resource pack for **Minecraft Java Edition 1.21.11 and 26.1–26.3**: roughly 60% Vanilla Minecraft, 40% Apple design. It keeps Minecraft's pixel-art identity and adds Apple's restraint: light surfaces, clear hierarchy, soft rounded geometry and restrained color accents.

> **Status:** 1.0.0, light theme. Includes light inventory and workstation screens, Liquid Glass shelf hotbar and marked XP/jump bars, Monocraft text and numbers, silver apple food icons, buttons, sliders and tooltips. The selection bubble is on by default. Shulker color matching is optional through OptiGUI or OptiFine.

## Screenshots

User-provided gameplay and menu captures. These show a modded setup; other visual effects and mods visible in the images are not included in macUI.

![Main menu](docs/images/main-menu.png)

![Survival inventory](docs/images/survival-inventory.png)

![Creative inventory](docs/images/creative-inventory.png)

![Music and sound options](docs/images/sound-options.png)

![Survival HUD and empty shelf hotbar](docs/images/survival-hotbar-empty.png)

![Survival HUD and shelf hotbar with items](docs/images/survival-hotbar-items.png)

![Shelf hotbar with diamond sword](docs/images/hotbar-diamond-sword.png)

![Shelf hotbar with enchanted golden apple](docs/images/hotbar-enchanted-apple.png)

### Shulker color preview

Generated texture preview, not an in-game capture. Color matching requires OptiGUI or OptiFine.

![All 16 shulker dye colors and undyed](docs/images/shulker-colors-0.29.png)

## Principles

- **Vanilla-compatible base.** Core styling works without mods or shaders. Respackopts adds settings; OptiGUI or OptiFine adds automatic shulker color matching.
- **Gameplay untouched.** Slot positions, hitboxes and interactions are exactly vanilla.
- **Interface focused.** GUI textures only: no item models or item definitions, so it combines cleanly with item and block packs.
- **Apple principles, not a macOS copy.** Material hierarchy, restraint, contrast and craft, translated into pixel art.
- **Performance first.** Small textures and stretched (not tiled) nine-slice centres.

## Install

1. Download `macUI-Light-<version>.zip` from [Releases](https://github.com/Oshakuru/macUI/releases).
2. Put it in your `resourcepacks` folder without unzipping it (Prism Launcher: right-click the instance → Folder → `resourcepacks`).
3. Enable **macUI — Light** in Options → Resource Packs.

One zip covers Minecraft 1.21.11, 26.1.x, 26.2 and 26.3. Screens added after 1.21.11 (the 26.2 friends list, the 26.3 Realms button and the IME text box) are styled to match.

To build it yourself, see [Build from source](#build-from-source).

## Optional: in-game settings (Respackopts)

The pack works on plain vanilla Minecraft. Players who also install the [Respackopts](https://modrinth.com/mod/respackopts) mod (Fabric/NeoForge, plus its LibJF dependency) get a settings button next to the pack in the resource pack screen:

| Setting | Default | Options |
|---|---|---|
| Glass bubble on selected slot | On | On / off |
| Hotbar style | Shelf (glass ledge) | Shelf (glass ledge the items sit on) / Dock (glass bar) |
| Hotbar opacity | Clear | Clear / frosted / dark / solid |
| Glass outline on hotbar | Off | On / off |
| Food icons | Silver apples | Silver apples / vanilla |
| Button shape | Pill | Pill / rounded rectangle (buttons and sliders) |
| Glass behind player model | On | On / off (opaque tile) |

Without the mod, Minecraft ignores `respackopts.json5` and the `.rpo` files, and the defaults above apply. Alternative textures live in `assets/macui/alt/`, which vanilla never loads.

## Build from source

Requires Python 3.10+, Pillow with FreeType support, and NumPy (`pip install pillow numpy`).

```bash
# 1. Extract the vanilla reference assets from your own Minecraft jar (one time)
python3 tools/extract_vanilla.py path/to/minecraft-1.21.11-client.jar

# 2. Build the pack into dist/
python3 tools/build.py
```

Prism Launcher keeps the jar at `<Prism data>/libraries/com/mojang/minecraft/1.21.11/minecraft-1.21.11-client.jar`.

All colours and radii live in [`design/tokens.json`](design/tokens.json). Change a token and rebuild; no texture is edited by hand.

## Repository layout

```
design/tokens.json        Design tokens: every colour and corner radius
design/logo/              Pack logo: original artwork (logo-source.png) and the native-pixel icon (logo-icon.png)
tools/extract_vanilla.py  Pulls vanilla GUI reference assets out of the client jar
tools/build.py            Generates the pack from tokens + vanilla geometry
docs/                     Feasibility study, theme plan, decisions log, testing checklist
docs/images/              Gameplay screenshots and generated shulker preview
reference/   (ignored)    Extracted Mojang assets: local only, never committed
dist/        (ignored)    Built test packs: local only
```

## Development history

Prototype milestones, oldest first. These are development iterations, not individually published releases.

| Prototype | What changed |
|---|---|
| 0.1 | First inventory, hotbar, buttons, hover highlights and tooltips. |
| 0.2 | Flat rounded slot tiles; fixed slot corner dots and pill button borders. |
| 0.3 | Translucent player preview with glass edges. |
| 0.4 | Dock hotbar, offhand styling and selected-slot indicator dot. |
| 0.5 | Shared Liquid Glass material; raised selection bubble and glass player well. |
| 0.6 | Pill buttons chosen as the main style. |
| 0.7 | Creative inventory, tabs, scrollbar and blue recipe-book button. |
| 0.8 | Recipe book, search fields, HD glass and 1.25× selected-item magnification. |
| 0.8.1 | Hotbar reduced to 2× to fix missing textures. |
| 0.9 | New logo; 1.50× magnification; bubble removed; versioned ZIP names. |
| 0.10 | Magnification reduced to 1.38×; softer glass without the white rim. |
| 0.11 | Silver apple food icons. |
| 0.12 | Blue Hunger-effect food icons. |
| 0.13 | Graphite sliders with rounded handles and blue hover state. |
| 0.14 | Optional Respackopts settings; English and Spanish labels. |
| 0.15 | Shelf/Dock styles, opacity choices, bubble toggle and magnification sizes. |
| 0.16 | Softer shelf lip and front-edge lighting. |
| 0.17 | Shelf becomes the default hotbar and offhand style. |
| 0.18 | Magnification slider experiment with prebuilt sizes. |
| 0.19 | Magnification simplified to fixed size choices. |
| 0.20 | HD Liquid Glass slider handles. |
| 0.21 | Project renamed to macUI; new pack namespace and settings ID. |
| 0.22 | Magnification moved into a separate add-on; main pack became GUI-only. |
| 0.23 | Initial glass XP, horse jump and locator tracks. Early ZIPs were revised during development; superseded by 0.24. |
| 0.24 | Marked XP/jump bars; final two jump segments red; bubble restored; Magnify reintegrated and off by default. |
| 0.25 | Manrope semibold digits 0–9; vanilla letters and symbols retained. |
| 0.26 | Tighter selection bubble with room for stack counts. |
| 0.27 | Inventory styling across remaining containers, workstations, mount inventories and related controls. |
| 0.28 | Smaller slot tiles and inset loom/stonecutter recipe selections. |
| 0.29 | Optional OptiGUI shulker colors: all 16 dyes plus undyed, with vanilla fallback. |
| 0.30 | Added OptiFine color rules; custom names use the same clear title area. |
| 0.31 | Advancements, toast/popup panels and notification badges match the pack. |
| 0.32 | Notification and popup panels use hotbar-style Liquid Glass. |
| 0.33 | Recipe toasts use the same glass background as advancement toasts. |
| 0.34 | All toast backgrounds share advancement-style Liquid Glass. |
| 0.35 | Monocraft text and numbers; removed Manrope font assets. |
| 0.36 | Crisp bitmap Monocraft fixes the soft TrueType rendering. |
| 0.37 | XP fill matches the level-number green. |
| 0.38 | Mountain meadow title panorama, adapted from the supplied image. |
| 0.39 | Replaced the single-image wrap with a CC0 six-face Frozen Peaks & Cherry Valley panorama. |
| 0.40 | Removed the custom panorama; the vanilla title panorama is back. |
| 1.0.0 | First official release: snowy taiga title panorama, support for 26.1–26.3, magnification removed. |

See [CHANGELOG.md](CHANGELOG.md) for details.

## Documentation

- [Feasibility, concepts and plan](docs/01-feasibility-and-concepts.md)
- [Light and dark themes](docs/02-light-and-dark-themes.md)
- [Decisions log](docs/decisions-log.md)
- [Testing checklist](docs/testing-checklist.md)
- [Vanilla 1.21.11 GUI sprite list](docs/vanilla-1.21.11-gui-sprites.tsv)
- [Changelog](CHANGELOG.md)

## License

Code and original artwork in this repository: [GPL-3.0](LICENSE).
Minecraft is a trademark of Mojang/Microsoft. Extracted vanilla reference assets and generated packs are not committed. Screenshots show Minecraft gameplay; generated previews show the pack styling. Not affiliated with Apple or Mojang.

Text and numbers use Monocraft, with vanilla fallback for unsupported characters. Monocraft is distributed under the SIL Open Font License; see `design/fonts/Monocraft-OFL.txt`.

## Optional: colored shulker inventories

With OptiGUI or OptiFine installed, shulker inventories automatically use soft tints matching all 16 dye colors plus undyed purple. Included in the main pack; no extra resource pack needed. Without either mod, shulkers keep the standard light panel. Rules are included for OptiGUI 2 (INI), 3 (JSON), and OptiFine (properties). Renamed and unnamed boxes share the same unobstructed title area; live compatibility testing is pending.

## Title panorama

A snowy taiga captured by the macUI owner in their own Minecraft 1.21.11 world. It's original work, covered by the macUI license; see `design/panorama/snowy-taiga/SOURCE.txt`.
