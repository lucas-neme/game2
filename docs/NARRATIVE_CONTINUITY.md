# Narrative continuity — V2

Every location must have a purpose in the central mystery or the human experience. Existing location purposes are now declared in the campaign dataset. Ten authored compound-choice reactions connect decisions from different cases; they require every listed choice, a minimum day and a one-hour delay. Dated meetings take precedence, dead characters do not appear, and ordinary schedules remain the fallback. Dialogue is accessible only in proximity during the relevant reaction, and the first witnessed conversation is persisted in storySeen. Reactions currently repeat during their defined daily window until the ending; they are not unique cinematics or physical evacuation mechanics.

Chapter spine: I the train raises the question; II erased people and H-17 establish human cost and logistics; III 1958, the grid and Horizonte reveal the mechanism; IV choices collide as the valley collapses; V the last signal resolves the player's accumulated commitments. Existing mystery and endings are preserved.

Design gate for future content: identify purpose, setup, payoff, prerequisite, affected actors, alternative when absent/dead, and whether the player can witness the outcome. Atmosphere-only elements must still serve a defined scene. Do not promise physical effects before implementation. Run node tests/narrative-continuity.mjs in addition to existing campaign checks. Browser playtest and art approval remain separate gates.

## V3 — One-shot causal events

Reactions now start no earlier than chapter IV (day 21), take place once at the first eligible full window after the one-hour delay, and skip overlapping authored meetings. The scheduler persists completed/cancelled outcomes even when the player is elsewhere or skips time; death before completion cancels the task. The journal displays individual event outcomes at the ending, including whether preparation was witnessed. Completed outcomes describe narrative activity, not proof of a physical rescue or power-grid change. The dedicated continuity suite is now a required CI step. No retroactive events are added after the ending timestamp.
