# Changelog

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
