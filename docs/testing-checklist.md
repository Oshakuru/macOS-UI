# Testing checklist

Test in **unmodded Minecraft Java Edition 1.21.11**: a clean Prism instance with no mods. Don't claim compatibility until every item has passed in game.

## Every build
- [ ] The pack loads with no "incompatible" warning.
- [ ] No missing textures (magenta and black). If any appear, check `logs/latest.log` for the file name.
- [ ] Gameplay unchanged: shift-click, drag-split, number-key swap, recipe book toggle, item tooltips.

## Visual matrix
Check each restyled screen at **GUI scales 1, 2, 3, 4 and Auto**, in **day, night, the Nether and on snow**.

| Area | What to check |
|---|---|
| Inventory | Slots line up with items; grid is readable on the white panel; title is readable; glass player area is see-through |
| Slot hover | Blue highlight on storage, armour, offhand, crafting and result slots |
| Hotbar | Bar visible against the world; selection ring and stack counts readable; offhand on both sides |
| Buttons | Normal, hover (blue) and disabled; short buttons ("Done") and wide buttons; no seams when stretched |
| Sliders | Track, knob at 0% / 50% / 100%, hover and drag (blue), label readable over the knob |
| Tooltips | Background and frame corners clean; text readable |
| Recipe book | Tabs, search field (typing, focus edge), craftable toggle on/off, page arrows, craftable/uncraftable/multiple recipe tiles, alternatives popup |
| Food bar | Full, half and empty apples; Hunger effect (green); readable on light and dark terrain |
| Magnification | Selected hotbar item is bigger; scrolling between slots; blocks, flat items, compass/clock, shields, banners, heads, chests; inventory hotbar row |
| Creative | Tabs, search, destroy-item slot, thin scrollbar drags correctly |

## Respackopts (optional)
Test once **without** the mod (everything must look like the defaults), then with Respackopts and LibJF installed:
- [ ] The settings button appears next to the pack, with the labels translated.
- [ ] Each setting switches correctly after the resource reload: magnification slider (1.00 off, 1.10, 1.20, 1.30, 1.38, 1.50), selection bubble, hotbar style (dock/shelf), hotbar opacity (four levels), hotbar outline, food icons, button shape (buttons and sliders), glass player area (survival and creative).
- [ ] Combinations: shelf + solid + outline, dock + frosted + bubble, magnification 1.50 + bubble.
- [ ] No errors in `latest.log` (use `/rpoc dump scope` if a condition misbehaves).

## Reporting
Send a screenshot per issue, with the GUI scale.
