# Decisions log

## 2026-11-17: direction
- **Concept B (Balanced Hybrid)** is the working direction.
- **Light theme first**; dark later as a recolour pass plus manual adjustments.
- **Visual refinements (v2):**
  - Whiter panel (`#F5F5F7`, edge `#C7C7CC`).
  - Rounder geometry: 5-px panel and hotbar corners (curved staircase), 2-px slot corners, rounded selection ring.
  - Buttons: graphite `#1D1D1F`; hover in Apple blue `#0071E3` (white text ≈ 4.7:1); disabled `#48484A`.
  - Tooltip and hotbar stay dark, because vanilla draws white text on them.
- **Button shape:** both variants are kept for in-game testing, rounded rectangle (5 px) and full pill (10 px).

## Phase 0: verified from the 1.21.11 client jar
- `version.json`: resource pack format **75.0**.
- 523 GUI PNGs; the full list is in [vanilla-1.21.11-gui-sprites.tsv](vanilla-1.21.11-gui-sprites.tsv).
- `container/inventory.png`: 256×256 canvas, panel 176×166 at (0,0). 46 slot frames plus the 51×72 player preview at (25,7). Each slot frame's top-right and bottom-left corner pixels are `#8B8B8B`.
- `hotbar` 182×22, `hotbar_selection` 24×23, offhand 29×24 (22×22 box).
- `slot_highlight_back/front`: 24×24, 16×16 content at (4,4), nine-slice border 4.
- `widget/button`: 200×20, nine-slice border 3. `button_disabled`: border 1.
- `tooltip/background`: 100×100, border 9. `tooltip/frame`: border 10 with `stretch_inner`.

## Prototype 0.1: in-game results
- Rounded variant loaded fine. Feedback: the slot grid felt cluttered.
- **Pill variant showed missing textures.** Cause: nine-slice border 10 on a 20-px sprite. **Rule: top + bottom borders must stay below the sprite height.**
- Stray grey dots at slot corners. The hotbar is hard to see against dark terrain at night.

## Prototype 0.2
- Slots are flat 16×16 `#E5E5EA` rounded tiles with a 2-px gap between them.
- Corner dots fixed. Pill border changed to left/right 10, top/bottom 9 (awaiting in-game confirmation).

## Prototype 0.3
- Glass player area: real transparency (α 120 at the top, fading to α 60), a `#D1D1D6` edge and a specular rim. Vanilla can't blur, so the glass tints the world rather than frosting it.
- To verify in game: partial transparency renders as expected.

## Open
- Hotbar contrast at night.
- Pill buttons in game.
