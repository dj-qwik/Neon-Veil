# Milestone 1 — Combat core: change log and QA

Date: 11 Nov 2026. Engine: UE 5.8.4. Toolchain: MSVC 14.44.35207, Windows SDK 10.0.22621.0. Test map: `/Game/NeonVeil/Maps/Tests/L_Test_CombatCore` (graybox, TEMP visuals).

## What was built

- `ANVPlayerCharacter`: first-person camera (95° default, 80–110 setting), walk 450 / sprint 650 / crouch 250 cm/s, slide, trace-based vault (0.5–1.2 m), toggle/hold settings, input lock for scripted moments, full-body shadow mesh, procedural viewmodel (hip/ADS offsets, sway, bob, kick, sprint/reload pose).
- `UNVWeaponComponent` + `UNVWeaponData`: data-driven hitscan weapons (damage, fire rate, magazine, reserve, reload, spread/bloom, recoil + recovery, ADS time/FOV/sensitivity, presentation slots for meshes, VFX, sound, montages). Data assets: VX-9, Kestrel, Harrow.
- `UNVHealthComponent`: health, armor, shield (absorbs before health; optional weak-point bypass), weak-point multiplier, immunity tags, "cannot die" flag, delegates.
- `UNVInteractionComponent` + `INVInteractable` + `ANVInteractableActor`: 2.5 m sphere trace focus, press and hold-to-use, custom-depth focus highlight, completion event tags.
- `UNVObjectiveSubsystem` + `UNVMissionData`: Bible §11 objective contract (ID, text, prerequisites, completion tag, optional flag, checkpoint policy); one-shot mission completion and next-map travel in `ANVGameMode`.
- `ANVHUD`: canvas HUD per Bible §10 (health lower left, ammo lower right, objectives top right, prompt centre right, spread-accurate reticle with permanent centre dot, hit markers, notices, subtitles with speaker label and background).
- `ANVTrainingTarget`: static/patrolling simulation targets with weak point and optional shield.
- `UNVCheatManager`: QA console commands (see README).

## Results (verified from `LogNeonVeil` output in PIE)

| Check | Expected | Result |
| --- | --- | --- |
| Clean compile | 0 errors, 0 warnings | Pass (6 builds) |
| Body hits, VX-9 | 24 dmg, 60 HP target cleared in 3 | Pass (24/24/12, cleared) |
| Shield | Body hits absorbed by shield first | Pass (60 → 36 → 12 shield, health 60) |
| Weak point | Bypasses shield, ×2 damage | Pass (48 applied) |
| Kestrel SMG | 14 dmg, auto, 30-round mag | Pass |
| Ammo / reload | Mag and reserve update; reload fills from reserve | Pass (12/48 → 9/48 → 12/45) |
| ADS time (VX-9) | 0.15–0.25 s, no snap | Pass (alpha 1.0 and FOV 78° at ≈0.18–0.20 s, smoothstep) |
| Walk / sprint / crouch | 450 / 650 / 250 cm/s | Pass |
| Slide | Starts from sprint, stays grounded, ends at crouch speed | Pass after fix |
| Vault 90 cm, 120 cm | Vault over | Pass ("ledge 88/118 cm, vault over") |
| Vault 160 cm | Refused | Pass ("outside band") |
| Interaction | Prompt at 2.5 m, hold progress, single use | Pass ("Hold [E] Run diagnostics") |
| Objectives | O1 → O2 → mission complete once | Pass |
| HUD | Health, ammo, objective, prompt, notice, low-health colour | Pass (visual check) |

## Bugs found and fixed during QA

- Python `unreal.Rotator(a, b, c)` is (roll, pitch, yaw): sun pointed upward and targets spawned upside down. Spawns now use named arguments.
- Camera FOV lagged the ADS blend by ~0.15 s (extra smoothing). FOV now follows the weapon's ADS alpha directly.
- Slide ended immediately (launch made the character airborne; crouch speed cap clamped it). Velocity is now set directly and the cap is lifted during the slide.
- Patrolling targets passed through the range walls. Patrol offsets shortened.
- Vault minimum lowered from 60 to 50 cm (60 cm cover measured 58 cm), and slide braking eased from 350 to 200. **Code changed, not yet compiled or re-tested.**

## Not yet verified (needs the next session or the user)

- Controller play-through (Enhanced Input mappings exist for gamepad; needs a physical pad test).
- 10-minute crash-free session (QA-gate for M1).
- Packaged Development build launch.
- Real weapon meshes, first-person arms and animation (asset milestone; current viewmodel is a TEMP block).
