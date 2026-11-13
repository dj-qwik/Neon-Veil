# M8 — Performance & packaging QA (M00 "The Glass Crown")

Hardware: RTX 4050 Laptop (6 GB), 14C/20T CPU, 16 GB RAM. UE 5.8.4, Win64 **Development** package.
Settings: fullscreen 1920×1080, TSR upscaling from 67% (r.ScreenPercentage 67), Epic scalability, vsync off.

## How to measure
- `Scripts/NV_Package.bat` cooks and stages to `Saved/StagedBuilds/Windows`. It skips the archive copy, which saves about 2.7 GB of disk. An incremental run takes about 2.5 min.
- `Scripts/NV_BenchmarkPackaged.bat` runs the packaged game with `-nvbench`, using `UNVBenchmarkSubsystem`.
  - It rides the C00 tram, then makes a 360° pan through a fixed viewpoint in each room.
  - Output: per-room stats in `…/Saved/NV_Benchmark.txt`, a CSV profile in `…/Saved/Profiling/CSV`, and `stat dumphitches` call stacks for frames over 250 ms in the log.
  - The game quits by itself when done.
- `Scripts/NV_Benchmark.bat` is the same tour in the editor binary (`-game`).
- F10 quits the game in any build. This is an interim measure until a pause menu exists.

## Final packaged result (12 Nov 2026, with bundled PSO cache)
| Stop | avg fps | p95 frame | GPU | max frame |
|---|---|---|---|---|
| C00 tram ride | 73.8 | 15.2 ms | 13.0 ms | 71 ms |
| A skybridge | 75.0 | 14.9 ms | 12.8 ms | 16 ms |
| B atrium | 82.5 | 14.1 ms | 11.6 ms | 17 ms |
| C sim suite | 83.9 | 13.3 ms | 11.4 ms | 20 ms |
| D gallery | 78.7 | 14.2 ms | 12.2 ms | 16 ms |
| E antechamber | 81.2 | 13.6 ms | 11.8 ms | 21 ms |

- **Target 60 fps at 1080p with upscaling: met everywhere.** No gameplay frame was over 250 ms, and there were 0 PSO waits.
- **Load frame:** 1.8 s while the level first appears. It happens before the tram moves.
- **VRAM:** peaked at 4.43 GB of a 5.15 GB budget in packaged runs.
- **Tram ride wall time:** 14.01 s.
- **Top GPU passes:** TSR about 2.0 ms, shadow depths 1.2–1.7, Lumen reflections 1.2–2.6, lights 0.8–2.0, volumetric fog about 0.5.

## Fixes made in M8
1. **Skyline physics bodies.**
   - The 46 City Sample towers are packed-level Blueprints and carried about 508,000 collision bodies.
   - That caused a 4–9 s load stall and 7–10 s Chaos `CreateExternalAccelerationStructure` stalls while the tram's colliding parts moved.
   - Collision was stripped in the five tower Blueprint templates (`nv_m8_skyline_bp.py`; local Fab content, gitignored). Overlap and navigation relevance were turned off on the visual-only atmosphere meshes (`nv_m8_perf.py`).
   - Verified: 0 skyline bodies. Load stall 9.4 s → 1.8 s; tram stall 10.3 s → gone.
   - No visual change: the towers are 160 m to 1 km away and unreachable.
2. **Bundled PSO cache.**
   - `NV_PSO_Pipeline.bat` does four things:
     - Cooks with shader stable keys, with `bShareMaterialShaderCode` on.
     - Records pipelines during the `-nvbench` tour (`-logPSO`).
     - Expands them with the SM6 `.shk` keys into `Build/Windows/PipelineCaches/PSO_NeonVeil_PCD3D_SM6.spc` (261 stable PSOs).
     - Repackages.
   - The game precompiles 127 pipelines at startup in 0.02 s. The 0.38 s first-sight hitch is gone.
   - `NV_PSO_Finish.bat` redoes only the expand and repackage steps.
   - Gotcha: pass only the `*PCD3D_SM6.shk` files. Mixing the SM5 keys asserts in the cook (`OutTargetPlatform == ShaderKey->TargetPlatform`).
   - Re-record after adding new materials or areas.
3. **Tram timing.** The tram parks out on the line and waits for steady frames, then glides on wall-clock time, so start-up hitches no longer stretch or skip the ride.

## Open
- **Load frame (1.8 s):** a loading screen or fade would hide it. It needs a UI pass.
- **Disk:** keep at least 15 GB free on C:. Cooking, the DDC and the staged build need it; an earlier package failed with a full disk.
- **Shipping config** (no cheats or benchmark) and an installer or zip are not produced yet.

## Update — skybridge lighting pass and pause menu (12 Nov 2026)
- **Skybridge (Bible §14 Crown: high-key pools against dark windows):** `nv_m9_skybridge.py`.
  - Ceiling changed to pale ceramic.
  - Seven soft 3.6 m rect-light panels at 900 cd and 6200 K, unshadowed, replace four point lights.
  - Cyan floor-edge lines run along both glazing lines.
- **Removed the M2 graybox skyline** (folder `Skyline`, 25 boxes and window cards; `nv_m9_remove_old_skyline.py`). Its window cards showed as a flat tan panel beyond the glass, and the boxes hid the real City Sample towers.
- **Swapped 9 `BPP_NYG_Ref` towers for `CHE_B01` towers** (`nv_m9_skyline_swap.py`). The ref towers were suspected first; the swap is harmless.
- **Pause menu:** Esc or gamepad Options; P in the editor. Resume / Restart Mission / Quit to Desktop, with keyboard, mouse and gamepad navigation. All three were tested in play.
- **Start-of-level fade from black:** it holds until frames are steady, then fades over 1.6 s, which hides the load hitch.
- **PSO cache re-recorded** (125 pipelines). Packaged benchmark:

| Stop | avg fps | p95 frame | max frame |
|---|---|---|---|
| Tram ride | 79.1 | 14.0 ms | 20 ms |
| Skybridge | 78.1 | 14.6 ms | 21 ms |
| Atrium | 83.9 | 13.6 ms | 129 ms (one streaming frame after teleport) |
| Sim suite | 86.0 | 12.9 ms | 16 ms |
| Gallery | 80.1 | 13.8 ms | 15 ms |
| Antechamber | 82.9 | 13.5 ms | 22 ms |

## Update — rain, Director MetaHuman and reflection (12 Nov 2026)

- **Rain:** 8 instanced streak fields (30,000 streaks) replace the old repeating sheets. Each streak has its own speed, length and phase. Tested falling in play.
- **Director:** a MetaHuman (Walter preset, rigged and textured through Epic's cloud, Optimized/Medium build). He wears the free MetaOutfits Casual Male outfit, tinted charcoal; we have no Bible-accurate outfit yet. Textures are capped at 2048 for face and head and 1024 for everything else.
- **Reflection desync:** a mirrored Director stands behind the antechamber glass. When the player looks at the reflection for 0.6 s, it stops for 0.35 s and then catches up. Tested in play, including in the packaged build log.
- **PSO cache re-recorded** with the Director (179 pipelines). New-PSO events appear only during the black load fade.
- **Packaged benchmark** at 1080p (TSR from 67%):

| Stop | avg fps | p95 frame | max frame | VRAM peak |
|---|---|---|---|---|
| Tram ride | 76.8 | 14.4 ms | 16 ms | 4.91 GB (load spike, under the fade) |
| Skybridge | 77.1 | 14.6 ms | 20 ms | 4.18 GB |
| Atrium | 83.0 | 14.1 ms | 18 ms | 4.22 GB |
| Sim suite | 84.2 | 13.3 ms | 21 ms | 4.36 GB |
| Gallery | 78.5 | 14.4 ms | 16 ms | 4.43 GB |
| Antechamber (Director) | 79.2 | 14.4 ms | 22 ms | 4.46 GB |

VRAM budget is 5.15 GB on the RTX 4050. The editor's "video memory exhausted" warning comes from the editor's own overhead and does not appear in the packaged build.

## Update — MetaHuman guards (12 Nov 2026)

- **The three atrium guards are now MetaHuman troopers.** All three share one character build: the Mateo preset wearing the free *Tactical Soldier Outfit for MetaHuman* (RMDavid) and the *Sci Fi Helmet P05* (Davlet, paid Standard licence).
  - **Directorate recolour:** the outfit's base colour is desaturated and tinted carbon. The helmet's red trims are desaturated to white and grey, and its optics glow cyan. The outfit's backpack serves as the Bible's "exposed battery pack" tell.
  - **How they're driven:** `ANVGuardCharacter` gained an `AppearanceClass` slot, which holds the assembled MetaHuman as a child actor. A hidden UE5 Manny running `ABP_Unarmed` keeps driving the patrols. The MetaHuman body follows the Manny's pose, and the clothing follows the body. Tested in play: the guards patrol with a walking stride, and none fall back to the default A-pose.
  - **Earlier attempt, kept in code but unused:** the free Waveforce mercenary as modular parts. It was too stylised next to the MetaHuman Director.
- **Textures:** 39 guard textures were capped, 29 of them 4K. Outfit and helmet are now 1024; the face, which sits under the helmet, is 512.
- **Packaged benchmark:** 1080p, TSR from a 67% screen percentage, PSO cache re-recorded.

| Stop | avg fps | p95 frame | VRAM peak |
|---|---|---|---|
| Tram ride | 73.4 | 15.1 ms | 4.35 GB |
| Skybridge | 74.3 | 15.3 ms | 4.42 GB |
| Atrium (3 guards) | 77.9 | 15.5 ms | 4.43 GB |
| Sim suite | 80.3 | 13.9 ms | 4.50 GB |
| Gallery | 76.3 | 14.8 ms | 4.56 GB |
| Antechamber (Director) | 77.7 | 14.6 ms | 4.60 GB |

Before the texture caps, VRAM peaked at 5.19 GB, over the 5.15 GB budget. The load spike (4.96 GB) happens under the black fade.
- **Open:** the guards' hair grooms are still selected under the helmets. The Python API wouldn't clear them, so this needs a manual pass in MetaHuman Creator; none is visible in play. Helmet optics have only been checked from the side and at a distance.

## Update — real weapon models (12 Nov 2026)

- **Source:** the free *Sci Fi gunpack* by PStudio (Fab, Standard licence). It replaces the placeholder cubes:

| Weapon | Pack model | Orientation | Weapon animation |
|---|---|---|---|
| VX-9 Service Pistol | `SK_A_Sci_fi_Pistol` | yaw -90 | slide `punch` on fire, `reload` |
| Kestrel SMG | `SK_b_w_smg_mini` (a bullpup, so the muzzle is at +Y) | yaw -92 | `fire`, `reload` |
| Harrow Precision Rifle | `SK_SCI_fi_sniper_rifle_ANIMATION` | yaw -90 | `TRIGGER`, `RELOAD` |

- **Code:**
  - `UNVWeaponData` gains `MuzzleOffset` (the pack has no sockets), `WeaponFireAnim` and `WeaponReloadAnim`.
  - The reload animation's play rate is auto-fitted to `ReloadTime`.
  - `UNVWeaponComponent` plays both animations on the weapon's own skeletal mesh.
- **Tuning:** viewmodel hip and ADS offsets were tuned live in play with `nv_gun_tune` and the `NVAim` cheat. Final values are in `nv_guns_setup.py`.
- **Tested in play:**
  - **VX-9:** hip pose, ADS sight alignment, firing.
  - **Kestrel:** hip pose, ADS, firing, reload (ammo goes 27 → 30, the "RELOADING" state shows, and the viewmodel tilts).
  - **Harrow:** configured from its bounds but **not seen in play**. It isn't a Level 1 weapon (the Bible's M00 simulation uses two classes), and its ADS height is an estimate.
- **Textures:** gun textures capped at 2048 (32 textures).
- **Packaged benchmark** (PSO cache re-recorded): 72.9–79.6 fps across all stops, p95 ≤ 15.5 ms, VRAM peak 4.60 GB, and no PSO events after load.
- **Not used:** the Infima Free FPS Template (one stylised rifle with a flat 11 KB texture). The engine's UE5 mannequin already supplies pistol and rifle animation sets.

## Update — weapon audio (12 Nov 2026)

- **Sources (both free, Fab Standard licence):**
  - *Free Weapon Sound Effects* by SoundLab1: realistic shots (3 variants each), reverb tails, reload and handling foley.
  - *Sci-Fi Shots Pack2: Game Of Weapons* by ShashiRaj Productions: a subtle tech accent layer.
- **How the accent layer was chosen:** I exported the 99 short sci-fi shots to WAV and analysed them offline. Kept: 12 clips about 0.2 s long, with attack under 7 ms, spectral centroid 3.6–4.4 kHz and tonal (spectral flatness under 0.35). I measured rather than listened, so the mix still needs a listen.
- **Code:** `UNVWeaponData` gains `FireSoundVariants`, `FireTailVariants` (with a voice cap), `FireLayerVariants`, `FirePitchRange`, `ReloadSequence` (each `FNVTimedSound` step is timed as a fraction of `ReloadTime`) and `EquipSound`.
  - `UNVWeaponComponent` plays every weapon sound as a 2D audio component, with no repeated variant twice in a row.
  - Reload foley is cancelled if you switch weapons mid-reload.
  - The older `FireSound` and `ReloadSound` remain as fallbacks.

| Weapon | Shot | Pitch | Tail (voices) | Accent | Reload steps |
|---|---|---|---|---|---|
| VX-9 | handgun ×3 | 0.97–1.03 | handgun, 0.55 vol (3) | 4 clips, 0.22 | mag out / draw / in / slide lock |
| Kestrel | rifle ×3 | 1.08–1.15 (compact SMG) | rifle, 0.40 vol (2) | 4 clips, 0.18 | mag out / draw / in / charge |
| Harrow | rifle ×3 | 0.82–0.88 (heavy) | shotgun, 0.70 vol (2) | 3 clips, 0.25 | mag out / in / charge (untested in play) |

- **Verified in play (verbose log, `log LogNeonVeil Verbose`):**
  - Every layer reports `playing=1`.
  - VX-9 reload steps fire at 0.03 / 0.38 / 0.71 / 1.08 s against a 1.45 s reload.
  - In an 8-round Kestrel burst no variant repeats back-to-back, and tails stay at 2 voices or fewer.
  - **Not verified by ear:** the levels and the accent's character are design choices and need a listening pass.

## Packaged benchmark after the subway tram (2026-11-12)
NV_PSO_Pipeline (539 stable PSOs) then NV_BenchmarkPackaged, RTX 4050 6 GB, 1080p, TSR 67%, vsync off.

| Segment | avg fps | p95 ms | max ms |
|---|---|---|---|
| A_TramArrival | 65.3 | 17.32 | 21.2 |
| A_Skybridge | 72.9 | 15.40 | 34.4 |
| B_Atrium | 78.0 | 15.16 | 18.2 |
| C_SimSuite | 80.5 | 13.73 | 17.3 |
| D_Gallery | 77.2 | 14.60 | 17.0 |
| E_Antechamber | 78.2 | 14.40 | 20.9 |

VRAM peak (GPUMem/LocalUsedMB) 4924 MB of the 5152 MB budget (was 4600 MB before the tram): under budget, ~230 MB headroom.
The editor's "video memory exhausted" warnings were editor overhead; the packaged game stays within budget.
Note: packaging fails with "Unable to build while Live Coding is active" if any editor instance is still open.
