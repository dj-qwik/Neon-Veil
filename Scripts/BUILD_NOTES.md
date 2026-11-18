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
- Set `r.Streaming.PoolSize 1200` in the editor console before PIE when testing here.
- Hostile fire and drone deaths spawn no GPU Niagara per shot; M01 graybox meshes cast no shadows. Keep it that
  way until the art pass budgets for it.
- The art pass (`nv_m01_art.py`, folder M01_Art, ~760 actors) lays kit meshes over the graybox with no collision
  and no shadows; graybox props it replaces are only hidden. Re-run it after every `nv_setup_m01.py` run.
