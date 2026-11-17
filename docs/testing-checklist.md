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
| XP bar | 0%, 50%, 100%; exact fill alignment at 2x; green level readable day/night at GUI scales 1–4; horse charge/cooldown; locator track and tinted markers; no missing textures or log errors. Partial fill has a straight moving edge (vanilla limit). |
| Hotbar | Bar visible against the world; selection ring and stack counts readable; offhand on both sides |
| Buttons | Normal, hover (blue) and disabled; short buttons ("Done") and wide buttons; no seams when stretched |
| Sliders | Track, knob at 0% / 50% / 100%, hover and drag (blue), label readable over the knob |
| Tooltips | Background and frame corners clean; text readable |
| Recipe book | Tabs, search field (typing, focus edge), craftable toggle on/off, page arrows, craftable/uncraftable/multiple recipe tiles, alternatives popup |
| Food bar | Full, half and empty apples; Hunger effect (green); readable on light and dark terrain |
| Magnify add-on | With `macUI-Magnify` above macUI: selected hotbar item is bigger; scrolling between slots; blocks, flat items, compass/clock, shields, banners, heads, chests; inventory hotbar row |
| Creative | Tabs, search, destroy-item slot, thin scrollbar drags correctly |

## Respackopts (optional)
Test once **without** the mod (everything must look like the defaults), then with Respackopts and LibJF installed:
- [ ] The settings button appears next to the pack, with the labels translated.
- [ ] Each setting switches correctly after the resource reload: selection bubble, hotbar style (dock/shelf), hotbar opacity (four levels), hotbar outline, food icons, button shape (buttons and sliders), glass player area (survival and creative).
- [ ] Combinations: shelf + solid + outline, dock + frosted + bubble.
- [ ] Magnify add-on setting: 1.00 (off), 1.25, 1.38, 1.50.
- [ ] No errors in `latest.log` (use `/rpoc dump scope` if a condition misbehaves).

## Reporting
Send a screenshot per issue, with the GUI scale.

## Integrated magnification (0.24)
- [ ] Plain vanilla defaults to 1.00x; bubble visible.
- [ ] Respackopts: off filters item overrides; each magnification size selects the correct models after reload.
- [ ] Bubble on/off independently of magnification.
- [ ] Check item-definition pack conflicts and inventory hotbar behavior.

## Manrope numbers (0.25)
- [ ] XP levels, item counts, menu values and chat digits at GUI scales 1–4; no clipping or overlap.
- [ ] Letters, punctuation and symbols retain vanilla appearance.
- [ ] Check Force Unicode Font behavior separately.

## Tight selection bubble (0.26)
- [ ] Single items and stacks of 2, 16 and 64: count readable at GUI scales 1–4.
- [ ] Compare bubble on/off, empty slot and optional magnification sizes; magnified items can extend beyond the fixed bubble.

## Container rollout (0.27)
- [ ] Workstations: crafting, anvil rename/cost/error, grindstone, smithing, stonecutter, loom, cartography, crafter enabled/disabled slots and redstone.
- [ ] Furnace/blast furnace/smoker progress and fuel; brewing bubbles, fuel and progress.
- [ ] Chest/barrel/Ender chest, double chest, shulker, hopper, dispenser/dropper: all slots and title positions.
- [ ] Enchanting choices and level requirements; beacon selection/payment; villager trades, discounts, out-of-stock and XP.
- [ ] Horse/donkey/mule/llama storage and equipment; nautilus equipment and preview.
- [ ] Bundle slots/progress, status-effect panels, game-mode selector.
- [ ] GUI scales 1–4: labels, disabled/hover/selected states, no missing textures or log errors.

## Smaller tiles (0.28)
- [ ] Inventory and workstation slots: wider gutters, unchanged item/count positions.
- [ ] Loom/stonecutter normal, selected and hover recipe tiles have consistent gaps.

## Colored shulkers (0.29)
- [ ] With OptiGUI: all 16 colors and undyed; renamed boxes, relogging, title contrast, hover and item counts.
- [ ] Without OptiGUI: standard light shulker GUI, no errors.
