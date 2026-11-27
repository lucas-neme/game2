# Narrative continuity — V2

Every location must have a purpose in the central mystery or the human experience. Existing location purposes are now declared in the campaign dataset. Ten authored compound-choice reactions connect decisions from different cases; they require every listed choice, a minimum day and a one-hour delay. Dated meetings take precedence, dead characters do not appear, and ordinary schedules remain the fallback. Dialogue is accessible only in proximity during the relevant reaction, and the first witnessed conversation is persisted in storySeen. Reactions currently repeat during their defined daily window until the ending; they are not unique cinematics or physical evacuation mechanics.

Chapter spine: I the train raises the question; II erased people and H-17 establish human cost and logistics; III 1958, the grid and Horizonte reveal the mechanism; IV choices collide as the valley collapses; V the last signal resolves the player's accumulated commitments. Existing mystery and endings are preserved.

Design gate for future content: identify purpose, setup, payoff, prerequisite, affected actors, alternative when absent/dead, and whether the player can witness the outcome. Atmosphere-only elements must still serve a defined scene. Do not promise physical effects before implementation. Run node tests/narrative-continuity.mjs in addition to existing campaign checks. Browser playtest and art approval remain separate gates.

## V3 — One-shot causal events

Reactions now start no earlier than chapter IV (day 21), take place once at the first eligible full window after the one-hour delay, and skip overlapping authored meetings. The scheduler persists completed/cancelled outcomes even when the player is elsewhere or skips time; death before completion cancels the task. The journal displays individual event outcomes at the ending, including whether preparation was witnessed. Completed outcomes describe narrative activity, not proof of a physical rescue or power-grid change. The dedicated continuity suite is now a required CI step. No retroactive events are added after the ending timestamp.

## V4 — Causal NPC chains

Eleven downstream activities depend on one or more completed prior reactions, with a one-hour minimum handoff delay. Data is topologically ordered; missing or cancelled parents block descendants. Earlier same-actor narrative appointments and fixed meetings reserve their windows. The journal shows the causal chronicle; outcomes are persisted, including after time jumps. This is narrative propagation, not simulated message delivery or physical map unlocking. Existing player-driven rescue/evacuation and endings remain unchanged.

## V5 — NPC psychology

All sixteen residents have authored goals, baseline trust/fear/resolve, an important social bond and contextual personal dialogue. Sixteen existing choices produce timestamped psychological effects; completed/cancelled tasks and death of an important ally influence mood. Values are derived from saved facts, clamped and independent of frame count. Proximity dialogue records at most one observation per NPC/day, and the journal exposes last observed mood rather than hidden numeric scores. This increment changes dialogue and personal memory, not autonomous schedule decisions or physical behavior. Existing mission evidence remains obtainable.

## V6 — Bounded autonomous routines

From chapter III, residents can change otherwise unreserved schedule windows based on fear, trust and resolve. Fear redirects 08:00–10:00 to a familiar safe location when fear exceeds resolve; distrust redirects 12:00–13:00 away from public activity; determination redirects 20:00–21:00 to a character-specific useful task. Authored meetings, causal events and explicit choice rules take precedence. The browser passes actual ally mortality to schedule calculations and shows contextual dialogue. This is deterministic schedule autonomy, not a full social AI or execution of physical tasks. Evidence availability remains unchanged; archive fallback remains intact.

## V7 — Social conflict and reconciliation

Ten two-actor scenes branch on campaign choices and, for reconciliation, completed earlier social scenes. They reserve shared locations around mission-related appointments and causal tasks. Witnessed conversations appear in the journal; relationship scores derive from completed scenes and death, not repeated interaction. Both actors must survive until completion. Social scenes do not yet unlock physical tasks or independently propagate rumors. Fixed V6 chapter boundary test: day 13 is the first day of chapter III, not chapter II.

## V8 — Physical electrical escalation

Four time-dependent outage stages begin on days 17, 21, 25 and 28. West, east and project districts are evaluated independently. A choice alone no longer represents a physical intervention: after solving the power case and waiting for the choice to activate, the player must operate the substation from inside. The operation persists and changes actual exterior lamp rendering and interior tint; emergency power is limited to designated facilities. The base demo remains unaffected. Journal and weather HUD report grid state. This does not yet close establishments, block trails, simulate trains, or create new creature encounters. Dedicated automated infrastructure tests cover timing, prerequisites and save persistence; actual visual quality remains subject to browser and manual checks.

## V9 — Civil defense and staged evacuation

After the local withdrawal confirmation, six named civilians are assigned to three departures on days 24, 26 and 29, shifted forward for late confirmation. They gather at the station for an hour before departure and disappear from active schedules after leaving; death before departure prevents boarding. Departed witnesses unlock archived testimony. Story and social tasks are cancelled if a participant leaves before completion. Diary shows departure manifest, service schedules and epilogue outcomes. Service hours shorten for market, sawmill and archive, but access to investigation sites is intentionally retained. No train sprite or actual vehicle movement is introduced. Older saves with a withdrawal flag but no timestamp are not retroactively evacuated; re-confirmation migration is a remaining compatibility issue.

## V10 — Physical route obstructions and continuity roles

Three authored single-cell barriers appear according to crisis stage and forest choice. They enter the spatial collision hash and are drawn procedurally; one can be removed locally for 30 game minutes. Spawn is deferred while the protagonist occupies a cell. Alternative approaches remain intended but require route QA across all states. Five role assignments select living, non-evacuated substitutes, with one bounded work window and priority below mission commitments. Old saves with a confirmed withdrawal but missing timestamp can explicitly reconfirm without retroactive departures. Role changes are scheduled activities, not full independent physical task execution. No new authored PNG sprites in this increment.

## V11 — Regional signal and manifestations

Five optional anomalies with chapter, time and local signal requirements. Electrical intervention reduces amplification but not the source. Procedural exterior silhouettes, observation, avoidance, frequency-selection contact and scripted dispersal, persistent outcomes and NPC avoidance. No new combat arena or premium sprites. Mandatory evidence remains independent.

## V12 — Environmental mechanisms

Six optional evidence-gated control panels with dependency ordering, recoverable mistakes, time costs and persistent calibration. Counterwave calibration reduces project signal by six internal points; final preparation records completed calibrations. Existing clues and endings remain independent. Controls are in-game buttons rather than new meshes or animations; transfer authorization does not open a new physical passage.

## V13 — Resident epilogues

Sixteen individually authored outcome profiles, seven ending contexts, completed tasks, social relationships, evacuation and mortality at the final timestamp. Frozen snapshot in outcome prevents post-ending changes or false survival claims. Personal objectives are not assumed achieved when a related preparation task is completed; prose distinguishes partial progress from confirmed facts. Existing saves with endings can derive a snapshot from available historical state. Journal renders sixteen expandable entries. This is text epilogue, not an animated cinematic. Calendar and meeting settlement honor final cutoff; active social scenes exclude evacuated actors.

## V14 — Cinematic archive

Four chapter interludes, six choice branches, six possible evacuation records and seven final sequences with resident epilogues. Manual replay from journal, next/skip, procedural backdrop. No bespoke animation or adaptive music. Fixed V13 cross-realm save comparison using serialized content.

## V15 — Adaptive original soundscape

Seven procedural musical profiles with original interval patterns, regional signal and anomaly awareness, smooth drone transitions and a bounded melodic scheduler. Existing sound toggle controls all playback. Audio graph and timer are released on disable/reset; hidden-tab bus is muted. Departure cue plays near station, not globally. No external music assets. Actual audio quality and browser playback remain to be manually auditioned.
