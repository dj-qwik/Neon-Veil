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

The citizens (`Scripts/Python/nv_npcs.py`) use the pack's Chaos cloth garments
(`CA_<Garment>_<f|m>_med_<nrw|ovw>`) on `ANVGuardCharacter::Garments`; they are skinned to the
visible MetaHuman body by leader pose with simulation off. The pack's `*_CombinedSkelMesh` assets are
whole-body crowd proxies, not garments: don't use them as outfit parts.
