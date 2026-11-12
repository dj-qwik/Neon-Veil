# M3: Simulation gameplay, QA record

**Build and test setup.** UE 5.8.4, NeonVeilEditor Development Win64. Every build listed here ended `Result: Succeeded`. All testing was done in PIE on the target laptop, through `UNVCheatManager` QA commands plus real keyboard presses, with results read from `Saved/Logs/NeonVeil.log`. Branch: `milestone/m3-sim`.

**Visual status.** Everything is still placeholder:
- the drone is a sphere
- the baton is a cylinder
- tracers are thin cylinders
- the vision cone uses a translucent `TEMP_` material
- guards are the template mannequin

Art arrives in M5 and VFX in M6.

## What M3 adds (Bible §4, §7, §8, §9)

| System | Classes | Notes |
|---|---|---|
| Cyberware | `UNVAbilityComponent`, `UNVAbilityData` (3 data assets) | Optical disruption (6 s, 12 s cooldown, breaks on attack). Kinetic shield (4 s full block, 10 s cooldown). Drone uplink (8 s, 14 s cooldown). Story disable/restore for M01, kept in the save (save v2). |
| Drone uplink | `ANVReconDrone` | Flies along the aim against level geometry only, hovers 4 m up (clamped under ceilings), scans every 0.5 s, and marks visible actors with health for 12 s. |
| Shock baton | `UNVMeleeComponent`, `INVStaggerable` | 0.12 s wind-up then a sweep. A hit staggers for 1.8 s; a strike on a staggered target is a takedown. Bosses can opt out. |
| Drill steps | `ANVSimulationDirector` | New step types: Volley, MarkTargets and WaitForEvent, with fail-and-retry. |
| Volley emitter | `ANVSimVolleyEmitter` | Telegraphs, then fires real line traces on the Pawn channel, so cover and the shield work as they will in combat. |
| Surveillance camera | `ANVSurveillanceCamera` | Sweeping vision cone. Detection builds over 0.45 s of line of sight; optical disruption hides the player. |
| Guards | `ANVGuardCharacter`, `ANVEnemyController` | Bible state enum; 0.25–0.5 s jittered decision cadence; navmesh patrol with a straight-line fallback; M00 acknowledgement glance. |
| HUD | `ANVHUD` | Ability bar, cloak and shield overlays, amber drone marks with range, threat text, detection meter. Button prompts switch between keyboard, PlayStation and Xbox labels. |
| Input | 4 new actions in `IMC_NV_Combat` | Baton: V / R3. Cloak: Q / D-pad Left. Shield: G / D-pad Right. Drone: T / D-pad Up. |

## The M00-O02 calibration drill (11 steps)

The Bible requirement covered: 3 moving targets, 2 shielded targets and 1 drone; weak points; two weapon classes; ADS, cover, melee and gadget prompts; optical disruption past a surveillance cone; and shield burst against a scripted volley.

| # | Step | Result | Evidence |
|---|---|---|---|
| 0–3 | Moving, ADS, shielded, Kestrel | PASS (M2) | Unchanged since the M2 run; skipped in the M3 runs. |
| 4 | Sentry drone (hovering 4.6 m, core underneath) | PASS | 3 weak-point hits from the entrance with ADS: 28, 28, 24. |
| 5 | Cover drill (crouch behind barrier) | PASS / FAIL as designed | Standing: 6 of 18 rounds landed, so the step fails and retries. Crouched: 0 of 18 landed, so it passes. |
| 6 | Shield-burst volley on an exposed pad | PASS / FAIL as designed | No shield: 14 of 14 landed, so it fails. Shield up: 14 of 14 reached the player, 112 damage blocked, so it passes. |
| 7 | Baton dummy | PASS | Gunfire does nothing (training and live rounds). Strike: 35 damage plus stagger. Second strike: TAKEDOWN. |
| 8 | Drone uplink: 3 concealed profiles behind 2 m walls | PASS | `Drone uplink marked 3 new`, step complete. |
| 9 | Surveillance cone, catwalk relay | PASS / FAIL as designed | Uncloaked: detected, reset to the ramp. Cloaked: not detected for the whole 6 s. Relay used with a 1.3 s hold: step complete. |
| 10 | Finalise | PASS | `Objective complete: M00-O02`, door opens, `CP_M00_SimExit saved`. |
| — | Checkpoint reload | PASS | Restored in 0.09 s; objectives, doors and abilities intact. |

## Abilities and baton on the test range

- **Optical disruption:** active, then broken by firing; a retry during cooldown is refused (OnCooldown).
- **Kinetic shield:** 30 test damage fully blocked; health stays 100. After expiry, 10 damage lands normally.
- **Drone uplink:** marked all 5 range targets; marks render with range readouts.
- **Story disable:** the shield shows OFFLINE and activation is refused (Disabled). This is the M01 path (QA-04).
- **Real keyboard:** Q, G, T and V in PIE triggered cloak (6.0 s), shield (4.0 s), drone (8.0 s) and baton.

## Guards (atrium)

Three non-hostile guards:
- **Loop guard:** circles the sculpture, x 4100–5600, y −650 to 650.
- **Glazing guard:** paces 3900–5300.
- **Arch guard:** paces y 358–591.

All patrol on the navmesh (dynamic generation) and pause 2–7 s at each point. Each logs `acknowledges the player` when Ghost-7 passes within 4.5 m with line of sight, then resumes. The mannequin's idle and walk animation plays.

## Bugs found and fixed in M3

- The relay terminal spawned at the world origin. Its mesh is the actor root, so a "relative" offset moved the whole actor. It is now placed by actor location.
- The sentry drone hovered just under the 3 m lane dividers, so most shots hit cover. It was raised to about 4.6 m.
- The drone uplink's flight stopped at any actor, including targets. It now traces against level geometry only, and hover height went from 3 m to 4 m so it sees over the walls.
- The baton dummy ignored Ballistic damage, but M00 pistols fire Training rounds. It now ignores both.
- Guards stood idle: the controller possessed them before the route existed. The route is now built in `PostInitializeComponents`, and Idle promotes to Patrol.
- Guards stopped about 74 cm short (stop-on-overlap). They now arrive at the point.
- New key mappings were not written to disk (the IMC package wasn't dirty). The script now marks it dirty and force-saves; verified with real key presses.
- QA tools: `NVGoTo` now uses the target's height (catwalk), `NVMelee N` chains strikes, and a skipped step retires its targets.

## Known gaps (not claimed as working)

- **Gamepad bindings:** the new ones (R3, D-pad) are untested with a controller. They need the user with the DualSense.
- **Drill difficulty and tuning:** not play-tested by a person yet. In particular the cover and shield timing, cone sweep speed and drone target speed.
- **Shooting guards:** the guards ignore all damage and don't react. The Bible doesn't say what happens if Ghost-7 fires on Directorate guards in M00, so this is an open design question.
- **Destructible light props:** the Bible's sim-suite note is not built yet (planned for M5/M6 art).
- **Optional interactables:** the news feed, trophy case and others are unchanged since M2.
- **Old saves:** v1 checkpoints from M2 are refused by the version check, so start a new game.
