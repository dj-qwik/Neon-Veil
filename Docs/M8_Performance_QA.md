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
