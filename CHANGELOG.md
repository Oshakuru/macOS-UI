# Changelog

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
