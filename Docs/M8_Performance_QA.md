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

## Final packaged result (12 Nov 2026, after fixes)
| Stop | avg fps | p95 frame | GPU | max frame |
|---|---|---|---|---|
| C00 tram ride | 71.6 | 15.3 ms | 13.0 ms | 409 ms (one PSO compile) |
| A skybridge | 74.2 | 15.1 ms | 12.9 ms | 62 ms |
| B atrium | 81.3 | 14.3 ms | 11.8 ms | 22 ms |
| C sim suite | 82.9 | 13.5 ms | 11.5 ms | 22 ms |
| D gallery | 77.8 | 14.2 ms | 12.3 ms | 22 ms |
| E antechamber | 80.0 | 13.9 ms | 11.9 ms | 24 ms |

- **Target 60 fps at 1080p with upscaling: met in every room.** 95% of frames are under 15.3 ms.
- **VRAM:** the previous packaged run peaked at 4.43 GB of a 5.15 GB budget. In the editor, play-in-editor sits at the budget; that is an editor-only overhead.
- **Tram ride wall time:** 14.49 s, inside the Bible's 12–18 s.
- **Top GPU passes:** TSR about 2.0 ms, shadow depths 1.2–1.7, Lumen reflections 1.2–2.6, lights 0.8–2.0, volumetric fog about 0.5.

## Fixes made in M8
1. **Skyline physics bodies.**
   - The 46 City Sample towers are packed-level Blueprints and carried about 508,000 collision bodies.
   - That caused a 4–9 s load stall and 7–10 s Chaos `CreateExternalAccelerationStructure` stalls while the tram's colliding parts moved.
   - Collision was stripped in the five tower Blueprint templates (`nv_m8_skyline_bp.py`; local Fab content, gitignored). Overlap and navigation relevance were turned off on the visual-only atmosphere meshes (`nv_m8_perf.py`).
   - Verified: 0 skyline bodies. Load stall 9.4 s → 1.8 s; tram stall 10.3 s → gone.
   - No visual change: the towers are 160 m to 1 km away and unreachable.
2. **Tram timing.** The tram parks out on the line and waits for steady frames, then glides on wall-clock time, so start-up hitches no longer stretch or skip the ride.

## Open
- **First-time shader (PSO) compiles:** one 0.38 s hitch on the ride, and the 1.8 s start-up frame, which happens while the tram is still parked.
  - "0 of them were precached" in the log.
  - Fix: record a bundled PSO cache. Run the packaged game with `-logPSO`, convert with `ShaderPipelineCacheTools`, and add it to the project, then repackage.
- **Disk:** keep at least 15 GB free on C:. Cooking, the DDC and the staged build need it; an earlier package failed with a full disk.
- **Shipping config** (no cheats or benchmark) and an installer or zip are not produced yet.
