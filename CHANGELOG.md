# Changelog

## 1.0.0 (2026-11-17), first official release
- **Supports Minecraft 1.21.11, 26.1.x, 26.2 and 26.3 in one zip** (`min_format` 75.0, `max_format` 97). Checked against the 26.1.2, 26.2 and 26.3 client jars: every texture macUI replaces keeps its path, size and nine-slice metadata.
- Styled the sprites added after 1.21.11: friends list buttons, cards and toast (26.2), Realms button (26.3) and the IME pre-edit box (26.1). They follow the button-shape setting. Their icons stay vanilla.
- **Removed magnification.** Its 1,505 item definitions were copies of 1.21.11's and would have overridden items Mojang changed in 26.x (beds, banners, shulker boxes, heads, shield, trident, maps). The pack is now GUI-only again.
- New title panorama: a snowy taiga captured by the owner in their own 1.21.11 world (six 1024px faces, unchanged). Provenance in `PANORAMA-SOURCE.txt`. Removed the unused third-party panorama sources from the repo.
- Owner tested the 0.27 and 0.34–0.40 changes in game on 1.21.11.

## 0.40 (2026-11-17), light prototype
- Removed the custom title panorama at the owner's request. The title screen uses the vanilla panorama again; no panorama textures or source notice are packaged. Panorama sources stay in `design/panorama/` but are not built.

## 0.39 (2026-11-17), light prototype
- Replaced the stretched single-image panorama with the selected Frozen Peaks & Cherry Valley panorama from Beautiful main interface (CC0). All six 1024px faces copied unchanged; source/license notice included. Unrelated assets from the original pack are excluded.

## 0.38 (2026-11-17), light prototype
- Added the owner-supplied mountain meadow as the rotating title panorama: six 512px cube faces projected from a mirrored photo wrap, with softened sky/ground poles. Single-image approximation, not a captured 360° landscape.

## 0.37 (2026-11-17), light prototype
- XP fill now matches the vanilla level-number green (#80FF20). Segment markers and glass track retained.

## 0.36 (2026-11-17), light prototype
- Fixed soft/broken Monocraft text by baking a binary-alpha bitmap at its native pixel size instead of using a live TrueType provider. ASCII and Latin-1 text/numbers covered; unsupported characters retain vanilla fallback. In-game confirmation pending.

## 0.35 (2026-11-17), light prototype
- Monocraft replaces both vanilla text and Manrope digits through a TrueType provider at size 8, oversample 1. Vanilla providers remain as missing-glyph fallbacks. Removed Manrope sources/license and old number-atlas generation. Monocraft OFL license included. In-game typography checks pending.

## 0.34 (2026-11-17), light prototype
- All five toast backgrounds and the popup panel now share advancement-style Liquid Glass, including tutorial cards. System warning symbol and tutorial/item icons remain intact. Popup panels use the same glass. Hardcoded text contrast remains an in-game check.

## 0.33 (2026-11-17), light prototype
- New-recipe toasts now use exactly the same Liquid Glass background as advancement toasts. Tutorial cards retain their lighter underlay. Vanilla recipe text colors remain unchanged; in-game contrast needs checking.

## 0.32 (2026-11-17), light prototype
- Notification and popup panels now use the hotbar’s 2x Liquid Glass renderer, shared radius, tint, shadow and rim-free finish. Dark-text recipe/tutorial cards use a light underlay for contrast.

## 0.31 (2026-11-17), light prototype
- Restyled advancements: light window/tabs, blue completed frames, distinct task/goal/challenge silhouettes, graphite description panels and subdued category backgrounds.
- Restyled toast/popup panels and notification badges. Kept dark surfaces behind white text, light recipe/tutorial cards, warning symbols and recognizable tutorial icons. Original dimensions and metadata preserved; in-game text/state checks pending.

## 0.30 (2026-11-17), light prototype
- Added OptiFine properties for all 16 shulker dye colors and an undyed fallback alongside existing OptiGUI support. No name filter: renamed and ordinary boxes use the same clear-title panel. No third-party artwork or shader code copied. Runtime compatibility remains untested.

## 0.29 (2026-11-17), light prototype
- Added optional OptiGUI shulker color matching: 16 dye colors plus undyed, using soft panel/slot tints and the smaller 0.28 tiles. Vanilla fallback stays light. Includes OptiGUI 2 INI and 3 JSON rules.

## 0.28 (2026-11-17), light prototype
- Reduced standard slot tiles from 16x16 to 14x14 within the same slot spacing. Inset loom/stonecutter recipe states and slot hover highlights to give grids more breathing room. Item rendering, stack counts and hit areas are unchanged.

## 0.27 (2026-11-17), light prototype
- Extended the inventory material to all remaining container backgrounds and container sprites, preserving texture sizes, UVs and metadata. Workstations, storage, trading, mounts, progress/error states and slot hints included. In-game verification pending.

## 0.26 (2026-11-17), light prototype
- Tightened the selection bubble to 20x20 logical pixels inside its unchanged 24x23 sprite, with a smaller radius and room for stack counts. Bubble toggle unchanged.

## 0.25 (2026-11-17), light prototype
- Manrope semibold for ASCII digits 0–9 only. Letters and symbols retain vanilla fonts. Applies to XP, item counts and other default-font numbers. Includes Manrope OFL license.

## 0.24 (2026-11-17), light prototype
- Magnification returns to the main pack at the owner’s request, off by default. Respackopts offers 1.25×, 1.38× and 1.50×; no separate add-on is built. The main pack now includes item definitions and GUI wrappers, which can conflict with other item-definition packs.
- Restored the glass selection bubble by default in the main pack; the existing setting can still hide it.
- Horse jump bar restores vanilla segment boundaries as fine inset markers; the final two charge sections are red instead of orange. Cooldown stays grey.
- XP and horse jump bars use the existing shelf glass material at 2x, with green XP, blue jump charge and grey cooldown. Fine inset segment markers on both XP and horse jump bars.
- Locator track matches the glass; vanilla tinted markers and animated arrows are preserved.
- Vanilla clips partial fills with a straight right edge; rounded moving caps require rendering changes outside resource-pack scope.
- In-game verification pending.

## 0.23 (2026-11-17), initial XP prototype
- Initial glass XP, jump and locator tracks. Iterative 0.23 downloads were superseded by the consolidated 0.24 build.

## 0.22 (2026-11-17), light prototype
- **The main pack is GUI-only.** Magnification moves to a separate opt-in pack, **`macUI-Magnify`**, placed above macUI. It holds the 1,505 item definitions, the magnified models and its own Respackopts size setting. `macUI-Light` now contains no item or model files, so it no longer conflicts with 3D item packs.
- The selected slot has no marker in the main pack (user decision). The glass bubble stays available as a Respackopts setting.

## 0.21 (2026-11-17), light prototype
- **Renamed to macUI.** The repo is now [Oshakuru/macUI](https://github.com/Oshakuru/macUI). The pack builds as `macUI-Light-<version>.zip` and shows as "macUI — Light" in game. The internal namespace is now `macui`, and the Respackopts pack ID is `macUi`, so saved Respackopts settings from earlier prototypes reset to the defaults once.

## 0.20 (2026-11-17), light prototype
- **Slider handle in Liquid Glass** (HD, 4×): a clear glass knob with a specular rim and soft shadow, which turns **Apple-blue glass** while hovered or dragged. The track is unchanged (graphite pill).

## 0.19 (2026-11-17), light prototype
- Respackopts: magnification is a simple choice of **1.00× (off), 1.25×, 1.38× (default) or 1.50×**, replacing the 0.18 slider, which could only snap between pre-built sizes.

## 0.18 (2026-11-17), light prototype
- Respackopts: **magnification is a slider from 1.00 to 1.50** (default 1.38; 1.00 turns it off). Sizes are pre-built, so the slider snaps to 1.10, 1.20, 1.30, 1.38 or 1.50. Values above 1.50 are no longer offered.
- The magnified model tree is nested one folder per alternative size (`magnified/m/m/m/…`), because a folder rule takes a single fallback.

## 0.17 (2026-11-17), light prototype
- **The Liquid Glass shelf is now the default hotbar** (and offhand), also on plain vanilla. The Dock-style glass bar moves to the optional settings (Hotbar style → Dock).

## 0.16 (2026-11-17), light prototype
- Shelf hotbar: the white line along the back edge is replaced by a very soft glow that fades into the glass (α 36, 2.5-px feather), so the shelf reads as one seamless surface. The optional outline setting is unchanged.

## 0.15 (2026-11-17), light prototype
- **More Respackopts settings** (optional; vanilla still uses the defaults):
  - Magnification size: off, 1.25×, 1.38× (default), 1.5× or 1.75×.
  - Glass selection bubble toggle.
  - Hotbar opacity: clear, frosted, dark or solid.
  - **Hotbar style: Dock (glass bar) or Shelf**, a Liquid Glass ledge the items sit on, with a bright top lip and soft shadow, in the classic 3D Dock shape.
- Style × opacity × outline combinations are generated as separate files (16 per sprite) and chosen with a multi-file fallback chain. Magnification sizes use three nested folder rules, because a folder rule can have only one fallback.

## 0.14 (2026-11-17), light prototype
- **Optional in-game settings with Respackopts** (bonus for players who use the mod; vanilla behaviour unchanged): magnification on/off, glass outline on the hotbar, silver-apple or vanilla food icons, pill or rounded-rectangle buttons and sliders, and glass or opaque player area. Menu labels are in English and Spanish (Mexico).

## 0.13 (2026-11-17), light prototype
- **Sliders restyled:** the track is the same graphite pill as the buttons, with a blue edge on hover or focus. The handle is a rounded grey knob, inset so it stays inside the pill at 0% and 100%, and turns Apple blue on hover. Nine-slice borders follow the pill rule (top + bottom < height).

## 0.12 (2026-11-17), light prototype
- Hunger-effect food icons are now **blue** (Apple-blue family) instead of green.

## 0.11 (2026-11-17), light prototype
- **Food bar:** the drumsticks are replaced by silver apples. They're hand-drawn at 9×9 after the layout of Minecraft's golden apple and coloured in the logo's cool silver. All six sprites: full, half (left half), empty (dark silhouette) and green Hunger versions.

## 0.10 (2026-11-17), light prototype
- Magnification reduced from 1.5× to **1.38×**.
- Hotbar and offhand: the white specular outline and inner band are removed. The bar is now plain translucent glass with its soft shadow.

## 0.9 (2026-11-17), light prototype
- Selection bubble removed: the selected hotbar slot is shown only by magnification. `hotbar_selection.png` is now transparent.
- Magnification increased from 1.25× to **1.5×**.
- New pack icon: the macOS UI logo, recovered to its native 20×24 pixel grid; it fills the in-game icon (`pack.png` 130×130, ×5 nearest neighbour).
- The zip name now includes the version (`macOS-UI-Light-0.9.zip`), set once by `VERSION` in `tools/build.py`.

## 0.8.1 (2026-11-17), light prototype
- Fix: the 4× hotbar (728×88) showed the missing texture in game. The hotbar is now 2× (364×44). The selection bubble and offhand stay at 4×; both worked in game, as did magnification.

## 0.8 (2026-11-17), light prototype
- **Hotbar magnification:** the selected item draws 1.25× larger, like the Dock. Done with vanilla item model definitions: each `items/*.json` is wrapped in a `minecraft:selected` + `display_context: gui` condition that points to a child model with a larger GUI transform, plus `oversized_in_gui`. 1,505 item definitions and 1,940 small wrapper models are generated.
- **HD Liquid Glass hotbar:** the hotbar, selected-slot bubble and offhand are rendered at 4× texel density with smooth anti-aliased curves, a 0.75-px specular rim, an inner band and a soft shadow. Layout and size in game are unchanged.
- **Recipe book restyled:**
  - Light panel with a dark graphite recipe area (the page counter is white).
  - Vertical tabs; the "craftable only" toggle is a blue pill with a white check when on.
  - Chevron page arrows; recipe buttons as inset tiles, with red-edged dark tiles for uncraftable recipes and a stacked tile for multiple recipes.
  - Popup panel and buttons.
- **Text fields** (recipe search and every other text box): a dark rounded field, with a blue edge when focused.
- **Creative scrollbar:** a thin 4-px rail and a 6-px thumb. The click area is unchanged.

## Unreleased
- Renamed to **macOS UI**. The pack builds as `macOS-UI-Light.zip` and shows as "macOS UI — Light" in game.

## 0.7 (2026-11-17), light prototype
- **Creative inventory restyled:**
  - All three backgrounds (item tabs, search, survival inventory), using the same tiles, glass player area and panel as the survival inventory.
  - The search field is dark, because vanilla draws its text in white.
  - The destroy-item slot is a red-tinted tile with a red ×.
  - The scroll track is a tile; the scroller is a grey pill.
  - All 28 tab images: the selected tab merges into the panel, unselected tabs are a darker grey, and the first and last tabs keep the panel's outer edge.
- **Recipe book button:** panel-coloured, rounded, with a blue accent edge on hover. The vanilla book art is kept, with its greens recoloured to the accent blue.
- `tools/build.py`: the inventory restyle is now a generic `repaint_container()` that works on any vanilla container background.

## 0.6 (2026-11-17), light prototype
- **Pill buttons chosen.** The rounded-rectangle variant is dropped, and the build now produces a single pack, `VanillaAppleUI-Light`.

## 0.5 (2026-11-17), light prototype
- **Liquid Glass** (Apple, 2025) replaces the dark Dock material and the old glass well. It's one shared material: a clear body with a light tint; a specular rim brightest at the top-left with a weaker glint at the bottom-right; a softer inner band so the edge reads as thick glass; and a floating shadow.
- Hotbar (Dock) and offhand: Liquid Glass with a faint dark underlay so white stack counts stay readable, and 9-px corners.
- Selected slot: a raised glass bubble (full 24×23, 1 px above the bar, brighter, with its own shadow) instead of the indicator dot. A resource pack can't enlarge the item itself.
- Player area: Liquid Glass on the light panel, with a `#C7C7CC` edge and α 52 at the top fading to α 20.

## 0.4 (2026-11-17), light prototype
- Hotbar restyled as a macOS Dock: a dark translucent bar with a thin light rim and 7-px corners, and no boxes around slots. The selected slot gets a soft highlight and a white "running app" dot below it. The offhand slots match.
- Glass player area made more see-through (α 72 → 32, was 120 → 60).
- Confirmed in game (0.3): the glass player area renders transparency, and buttons load correctly.

## 0.3 (2026-11-17), light prototype
- The player preview area is now translucent "glass": real transparency fading from α 120 to α 60, a light edge, a bright top/left rim and a faint bottom/right rim. No blur is possible in vanilla.

## 0.2 (2026-11-17), light prototype
- Slots redrawn as flat 16×16 rounded tiles with a 2-px gap between them, to reduce clutter.
- Fixed stray grey dots at slot corners.
- Pill buttons: nine-slice border changed from 10 to left/right 10, top/bottom 9. A border of 10 on a 20-px sprite failed to load in game.

## 0.1 (2026-11-17), light prototype
- First generated pack: survival inventory, hotbar, selection ring, offhand, slot highlight, buttons (rounded and pill variants) and tooltip.
