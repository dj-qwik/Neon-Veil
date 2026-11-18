# Build notes

## C++ rebuilds with the MetaHuman crowd wardrobe enabled

`MetaHumanCrowdContent` (the Fab "MetaHuman Crowd Sample" content plugin, installed under the
engine's `Plugins/Marketplace`) is mounted fine by the editor, but UnrealBuildTool 5.8 reports
"Unable to find plugin 'MetaHumanCrowdContent'" and refuses to build. Neither `"Optional": true`
nor `AdditionalPluginDirectories` helps (Optional also stops the editor mounting it).

Workaround for any C++ change (Live Coding included):
1. Close the editor.
2. Temporarily remove the `MetaHumanCrowdContent` entry from `NeonVeil.uproject`.
3. Open the project and accept the module rebuild.
4. Close, restore the entry, reopen. (No rebuild is triggered; the crowd assets mount again.)

**Never save a level in the step-3 session.** Without the crowd plugin mounted, the citizens' MetaHuman
references load as null, and saving `L_M00_Prologue` then writes the nulls into the map: every citizen
turns invisible except a stray hair-card mesh lying on the floor. If that happens, reopen with the full
uproject and run `nv_npcs.py`, then `nv_skycar.py nofbx` and `nv_vo_hook.py SKY` (the sky-car driver is
a copy of `NPC_St_E2`).

The citizens (`Scripts/Python/nv_npcs.py`) use the pack's Chaos cloth garments
(`CA_<Garment>_<f|m>_med_<nrw|ovw>`) on `ANVGuardCharacter::Garments`; they are skinned to the
visible MetaHuman body by leader pose with simulation off. The pack's `*_CombinedSkelMesh` assets are
whole-body crowd proxies, not garments: don't use them as outfit parts.

## GHOST-OS UI (Nov 2026)

All screen UI is code-built Slate in `Source/NeonVeil/UI`:
- `NVUIStyle` palette, fonts (Content/UI/Fonts, OFL: Orbitron, Rajdhani, Share Tech Mono) and the `NVUI::FPainter` shape batcher.
- `NVUIWidgets` building blocks: SNVFrame, SNVTypeText, SNVMeter, SNVKeyCap, SNVButton, SNVTab, SNVRule, SNVSignal.
- `NVHUDOverlay` the in-game layer (comms cards, subtitles, notices, title card, objectives, prompt, vitals, cyberware slots, weapon, threat).
- `NVMenuShell` the pause/system menu with tabs. New systems plug in with `NVUI::RegisterMenuPage({Id, Label, BuildFn})`;
  reuse an Id (System, Cyberware, Upgrades, Skills, Comms) to replace a placeholder page.
- Messages: `ANVHUD::PushMessage(FNVCommsMessage)` / `ShowMessage(...)`, or set `bAsComms` on an FNVSubtitleLine.
- Console: `NVUIDemo [Title=0|1] [MenuTab+1]` fires one of everything.
Fonts are read from disk, so packaging stages `Content/UI/Fonts` as non-UFS (DefaultGame.ini).

## M01 testing and video memory (Nov 2026)

The owner's GPU (RTX 4060 laptop, 8 GB, ~5.1 GB budget in the editor) runs the Glass Crown close to its limit.
Over budget, D3D12 removes the device and the editor dies ("GPU Crashed or D3D Device Removed").
- Don't `HighResShot` in PIE in this map; use window screenshots.
- Don't teleport from the prologue tram straight into M01: the tram/city section stays resident. Run
  `nv_pie_m01.py` twice: the first pass completes M00-O01..O03 and reloads the gallery checkpoint, the second
  plays M01. A third pass after its deliberate death checks the checkpoint restore and finishes the mission.
- Keep the texture pool at the project default (`r.Streaming.PoolSize 1000`) when testing here. After the M01 art
  pass, 1200 put the editor 45 MB over its video-memory budget on the tram; at 1000 the pool only drops mips.
- Hostile fire and drone deaths spawn no GPU Niagara per shot; M01 graybox meshes cast no shadows. Keep it that
  way until the art pass budgets for it.
- The art pass (`nv_m01_art.py`, folder M01_Art, ~760 actors) lays kit meshes over the graybox with no collision
  and no shadows; graybox props it replaces are only hidden. Re-run it after every `nv_setup_m01.py` run.

## M01 story beats, options and title (2026-11-18)
- Order after `nv_setup_m01.py`: `nv_m01_art.py` (dressing, crawlway), `nv_m01_director_arms.py` (Director beat, name
  tag, restraint arms, prologue title on BP_NVGameMode_Prologue), then `nv_vo_hook.py M01`.
- The restraint arm comes from Downloads/black_honey_robotic_arm.glb: `nv_import_restraint_arm.py`, then
  `Saved/nv_arm_assemble.py`-style merge to `/Game/BlackHoneyArm/SM_SM_NV_RestraintArm`, then `nv_arm_textures.py`.
  Keep its textures at 1K: at 4K the editor went ~900 MB over its video-memory budget in M01.
- Volume sliders need `nv_audio_classes.py` (SC_NV_Music, SC_NV_Voice); re-run it after importing music or VO.
- In PIE, open the pause menu with P (Esc stops PIE in the editor).
- Editing a Blueprint's class defaults from Python: compile it, set the CDO, then save with `only_if_is_dirty=False`.
