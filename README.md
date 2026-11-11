# NEON VEIL — Act I

Single-player cyberpunk FPS built in Unreal Engine 5.8 (C++ + Blueprints). Current scope: **Level 1, M00: The Glass Crown** (see the Build Bible).

## Requirements

- Unreal Engine 5.8 (Launcher build)
- Visual Studio 2022 17.14+ with *Game development with C++*, MSVC v143 14.44, Windows 11 SDK 10.0.22621.0
- NVIDIA driver 591.86 or newer (older drivers are denylisted by UE 5.8 for D3D12)
- Git LFS (binary assets are tracked through LFS)

## Project layout

| Path | Contents |
| --- | --- |
| `Source/NeonVeil/` | C++ module: `Character`, `Combat`, `Interaction`, `Objectives`, `UI`, `Core`, `Debug` |
| `Content/NeonVeil/` | Project assets: input, weapon/mission data, Blueprints, maps |
| `Scripts/NV_Build.bat` | Builds the editor target and writes `Saved/Logs/NV_Build.log` |
| `Scripts/Python/` | Editor automation (run with `py "<path>/nv_run.py" <script>` in the Unreal console) |
| `Docs/` | Milestone change logs and QA results |

### Engine template content (not in this repo)

The project was created from Epic's **First Person (Blueprint)** template. Its content folders (`Content/Characters`, `Content/FirstPerson`, `Content/Input`, `Content/LevelPrototyping`) are Epic sample content and are not committed here. To rebuild a working copy, create a UE 5.8 First Person Blueprint project named `NeonVeil` and copy this repository over it.

## Building

1. Close the Unreal Editor.
2. Run `Scripts/NV_Build.bat` (or build `NeonVeilEditor | Development | Win64` in Visual Studio).
3. Open `NeonVeil.uproject`.

## Placeholder policy

Everything named `TEMP_` is temporary and is replaced in the art milestones. See `Docs/AssetManifest.md` once assets are acquired.

## QA console commands (non-shipping)

`NVReport`, `NVGoTo <name> [dist] [yaw]`, `NVAimAt <name> [weakpoint]`, `NVFire <n>`, `NVReload`, `NVAim <0|1>`, `NVEquip <slot>`, `NVUse [hold]`, `NVMove <fwd> <right> <sec> <sprint>`, `NVJump`, `NVCrouch <0|1>`, `NVFace <yaw>`, `NVSampleAds [sec] [samples]`, `NVHurtSelf <amount>`. All results go to `Saved/Logs/NeonVeil.log` under `LogNeonVeil`.
