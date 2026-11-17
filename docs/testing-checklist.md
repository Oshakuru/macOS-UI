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
| Tooltips | Background and frame corners clean; text readable |

## Reporting
Send a screenshot per issue, with the GUI scale and the variant (rounded or pill).
