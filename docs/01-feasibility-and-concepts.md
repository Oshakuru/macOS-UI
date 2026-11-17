# Feasibility, concepts and plan

Phase 1 study for Minecraft Java 1.21.11, written 2026-11-17.

> **Note:** this document records the original research and the concept choice. Tokens and geometry have changed since, so the current values live in [`design/tokens.json`](../design/tokens.json) and the [decisions log](decisions-log.md). The open questions in §0 were answered in Phase 0 (see the decisions log).

## 0. Research basis

- 1.21.11 ("Mounts of Mayhem") uses **resource pack format 75.0**, confirmed from the jar's `version.json`.
- Since 1.21.9, `pack.mcmeta` requires `min_format` and `max_format`. `pack_format` is only needed to support formats below 65.
- GUI sprites live in the `gui` atlas under `textures/gui/sprites/…`. Each can have a `.mcmeta` with `gui.scaling`: `stretch` (default), `tile`, or `nine_slice` (`width`, `height`, `border`, `stretch_inner`).
- **Apple Design skill** ([emilkowalski/skills › apple-design](https://github.com/emilkowalski/skills/tree/main/skills/apple-design)): the full `SKILL.md` couldn't be fetched during research, so this study worked from its published summaries.

## 1. Apple Design: what transfers to static pixel textures

| Skill principle | Transferable? | Translation for this pack |
|---|---|---|
| Material weight signals hierarchy; never stack light translucent surfaces | **Yes** | Three levels: panel → slot → accent (selection/hover). One translucent surface at most. |
| Response: highlight on press, continuous feedback | **Partly** | Only *normal / highlighted / disabled* states exist (no pressed state). The hover state must be unmistakable. |
| Reduced transparency / increased contrast | **Yes** | Contrast first; translucency used sparingly. |
| Spatial consistency | **Yes** | One pixel grid, one radius scale, one light direction. |
| Tracking/optical sizing varies with size | **Barely** | The bitmap font has one size. Leave the font alone in v1. |
| Springs, momentum, gestures, backdrop blur | **No** | Not reproducible in a vanilla pack. Excluded. |

## 2. 1.21.11 GUI architecture

### 2.1 Pack metadata
```json
{ "pack": { "description": "Vanilla × Apple UI", "min_format": [75, 0], "max_format": [75, 0] } }
```

### 2.2 Four texture systems
1. **Full container backgrounds**: `textures/gui/container/*.png`. Fixed UVs on a 256×256 canvas, no nine-slice. **Slot frames are painted into these images**, so every container is redrawn and positions are fixed.
2. **GUI sprite atlas**: `textures/gui/sprites/**`. Widgets, HUD, slot highlights, tooltips, toasts, recipe book, advancements, bundle.
3. **Menu backgrounds**: `menu_background`, in-world variants and separators. Blur strength is a player option.
4. **Fonts**: `font/default.json` bitmap providers. Glyphs can be replaced; the size is fixed.

### 2.3 Can / can't / excluded

| Can redesign | Can't change | Excluded by project rules |
|---|---|---|
| Container backgrounds and the slot look | Layout, positions, sizes, hitboxes | Core shader overrides |
| Slot hover sprites | Text colours and shadows (hardcoded) | |
| Hotbar, selection, offhand, HUD icons, bars | Pressed states, transitions, easing | |
| Buttons, sliders, fields, checkboxes, scrollers | Blur, anti-aliasing | |
| Tooltip background and frame | Per-GUI-scale assets | |
| Toasts, menu backgrounds, title logo, font glyphs | OS cursor; drag-highlight sprite (MC-279870) | |

### 2.4 Engine quirks
- **MC-277202**: empty-slot icons layer inconsistently with the highlight sprites.
- **MC-299417**: highlight sprites draw over the inventory title. Keep highlights inside the 16×16 item area.
- **MC-269154**: extreme nine-slice borders bleed the atlas. In practice, **top + bottom borders must stay below the sprite height** (confirmed in prototype 0.1).
- **MC-269152**: tiny tiled nine-slice pieces cost performance. Prefer `stretch_inner: true`.

## 3. The decisive constraint: text colour dictates surface colour

Vanilla hardcodes dark grey container titles and white button, tooltip and stack-count text. So:
- **Container panels must be light.**
- **Buttons, tooltips and the HUD must be dark.**

## 4. The three concepts

| | A · Vanilla refined | B · Balanced hybrid ★ | C · Apple-forward |
|---|---|---|---|
| Idea | Vanilla greys, tidied | Light neutral panels, graphite controls, one blue accent, rounded geometry | Dark graphite everywhere |
| Pros | Safest | Premium yet unmistakably Minecraft; respects hardcoded text | Most "Apple" |
| Cons | Too timid | Many container files to redraw | Titles unreadable on dark panels |
| Feasibility | High | High | Low for containers |

**Chosen: Concept B.** It's the only ambitious option that respects the hardcoded text colours.

## 5. Roadmap
0. Ground truth: extract the jar, inventory the sprites. ✅
1. Prototype: inventory, hotbar, selection, slot highlights, buttons, tooltip. *In progress.*
2. Remaining widgets: sliders, text fields, checkboxes, scrollers, tabs.
3. Common containers: chests, shulker, crafting, furnace family, dispenser/dropper, hopper.
4. Workstations: anvil, smithing, enchanting, brewing, beacon, loom, stonecutter, cartography, grindstone, crafter, villager, mounts.
5. HUD: hearts, food, armour, air, XP, boss bars, toasts.
6. Menus: title, options, world/server lists, separators.
7. Recipe book, creative tabs, advancements, bundle, statistics.
8. Dark theme pass (see [02-light-and-dark-themes.md](02-light-and-dark-themes.md)).

## 6. Validation
See the [testing checklist](testing-checklist.md). No compatibility claim until it passes in unmodded 1.21.11.
