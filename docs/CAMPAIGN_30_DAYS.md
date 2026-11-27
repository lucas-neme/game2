# Campaign V1 — Os Segredos do Vale

## Implementation and narrative contract
The original demo is preserved as a separate mode. The title screen offers a new 30-day campaign. Chapter I's existing train cinematic can continue into the campaign instead of ending the save. Calendar progression is independent from the player's presence; chapters II–V require evidence and deductions, with a calendar unlock and a hard deadline at day 30. Waiting is voluntary, never an automatic skip of unfinished missions.

- 28×14 exterior grid (392 cells, versus 196); 23 investigation locations, including 12 expansion landmarks, nine new connected-to-world rooms (37 room layouts total).
- 16 named residents, 480 day records, 2,880 baseline appointment slots, 30 dated meetings, 30 calendar events, 36 individual choice rules, 5 coordinated-meeting redirects.
- 10 additional cases after the train: missing patient, H-17 cargo, forest, history, power, Horizon, rescue, evacuation, counterwave, last signal. Three independent source slots each (30 total).
- Recorded choices take effect after one in-game hour. Scheduled meetings are resolved offscreen, can change venue and lose deceased participants. Evidence is not randomized. A preserved archive source becomes available when a witness dies or after the relevant chapter's initial two-day grace period.
- New room clues are collected inside the building. Indoor NPCs have deterministic walkable positions, depth rendering, proximity dialogue and local collision. Exterior residents use the existing route/animation renderer. Offscreen travel may be abstracted.
- Six deliberate endings (physical shutdown, Horizon, counterwave, contact, truth, sacrifice) and one deadline ending; actual rescue and evacuation require further local interactions after the relevant choice. Saves persist campaign and location.
- The first five days retain specific legacy personal-story event overrides, not the old repeated base schedule.

## Source of truth
- `content/campaign/valley-v1.json`: narrative, calendar, sources, decisions, rules, appointments.
- `src/campaign/core.js`: deterministic simulation, no DOM.
- `src/campaign/browser.js`: integration with existing Canvas runtime.
- `node scripts/sync-campaign.mjs`: embed these sources into standalone `index.html`; `--check` detects drift.
- `FZ_CAMPAIGN()`: inspect active chapter, residents, locations, decisions and state.
- `FZ_AGENDA(id, day)`: inspect planned slots and meetings for a named NPC.

## Release gates
1. Run `node scripts/sync-campaign.mjs --check`.
2. Run `node tests/demo-smoke.mjs` and `node tests/campaign-smoke.mjs`.
3. Run the two Playwright suites (`tests/browser-smoke.mjs`, `tests/campaign-browser.mjs`).
4. Verify a full manual campaign from day 1 to day 30, including alternate witness/archive routes and deaths, time jumps, interrupted meetings, and every ending.
5. Check all indoor and exterior transitions, FPS on target machine, and actual published SHA. Do not bypass Wampa deployment gates.

The previous 657 assertions and new 17,661 campaign checks passed in a simulated DOM / JS environment. The new suite includes reachability across 270 sampled day/time combinations and 63 distinct indoor occupancy patterns. Real Chromium and deployment are not confirmed here.

## Artistic and gameplay scope still outstanding
The larger exterior is procedurally textured and reuses existing production atlas entries as temporary representations of new buildings; the approved Valley expansion PNGs and premium interior package are not all present on GitHub. Import and individually approve the original art, replace temporary actor sprites and buildings, calibrate assets and collisions. Do not claim new dedicated animations or premium visual parity from this code. The current chapters use evidence collection, dialogue, deduced cases and local actions. Additional bespoke physical puzzles, enemy AI/encounters, cinematic scenes, train simulation, authored day-specific incidental conversations, quest-specific animations, door transit animation, and audiovisual escalation require further implementation. In particular, the event calendar records narrative developments and schedule changes; it does not yet simulate all planned blackouts, evacuations and creature attacks as physical events. Full pacing (10–15 hours) is a target, not measured. Validate actual FPS and publication rather than relying on static tests.

## Next increments, in order
1. Import approved premium art and build production manifests with no silent fallbacks; use the existing review/production gates.
2. Finish bespoke gameplay for each mission, including H-17 machinery, observatory calibration, rescue and evacuation, with peaceful/stealth/combat alternatives.
3. Implement physical world escalation, train traffic, weather/power-state lighting, faction behavior and additional personal NPC side quests.
4. Add cinematics and branching epilogues, localization, audio, accessibility and performance profiling.
5. Run full campaign human playtests, balance the calendar and deadline, then publish the verified SHA.
