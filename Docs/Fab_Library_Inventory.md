# Fab library inventory (snapshot 2026-11-12)

The account's Fab library has 58 items. All Fab, Epic, Quixel and MetaHuman content is licensed for use in the game, but it can't be redistributed. It stays local and gitignored (see `.gitignore`), and anyone cloning the repo has to re-acquire it through Fab.

Status key:
- **In use**: in the NeonVeil project now.
- **Added**: in the project's Content folder, but not used in a level yet.
- **Library**: owned but not added to the project.

## New since the last review

### Music

| Item | Seller | Status | Notes |
|---|---|---|---|
| Cyber Punk Music v11 | Kloudization | **In use (M00 sim suite)** | 10 tracks of about 171 s each. Heavily compressed (about -9 LUFS, LRA 0.9–2.8), 99–129 BPM, constant high energy. Background 6 is the darkest and least busy, so it is the M00 sim-suite combat layer. |
| FREE Cyber Metal Music Pack | Intersonic | Added | Reborn, The Devil's Confidant, Focus, Focus 2, Cauldronized, Opener. Metal energy is too much for M00. **M01** escape/lockdown could use Opener (dynamic, LRA 11.8) or Cauldronized. **M02** Hunter boss could use Reborn or Devil's Confidant. |

**Licensing:** *resolved.* Bible addendum A1 (`Docs/Bible_Addendum_A1_Licensed_Music.md`) allows licensed library music, as long as every track is credited in `Docs/Credits.md` and the in-game credits.

### Environments and city building (later levels)

| Item | Seller | Best fit |
|---|---|---|
| Soul: City | Epic | **M02 Below the Veil**: rainy undercity streets, neon signage, wet alleys. It's the best match for the Gutter routes. It's heavy, so check VRAM on the 4050 before using it. |
| Cyberpunk Industries Vol.1 | Softkick | **M02** industrial undercity and relay/cooling units (M02-O03). The seller is leaving Fab, so download it locally soon. |
| Underground Sci-Fi | GeorgeShachnev | **M01** transit shaft and service bypass (M01-O02/O03), and the M02 underpass. |
| Underground Tunnel (existing) | — | **M01** drainage spillway approach (M01 area F). |
| SICKA Free Environment Pack | SICKA | Sci-fi interior kit for M01 maintenance and back-of-house areas. The bundled ancient kit isn't needed. |
| Sci Fi Alien Facility / High Tech Base / Sci Fi Space Station Interior | YaMaKundra | **M01** lockdown corridors in the same tower. These are good for the hostile "same building, other side" spaces. |
| Sci-Fi Security X-Ray | — | FBX checkpoint scanner. Could replace the M00 security arch prop (M00-O01) later, and works as M01 lockdown dressing. |
| scifi walls set | — | AI-generated geometry. Use only as background filler, and check topology and licence notes first. |
| City Sample Buildings / Vehicles (existing) | Epic | Already used for the M00 skyline. Also covers M02 street-level traffic and facades. |
| City Subway Train Modular (existing) | — | Maglev/tram dressing. M01/M02 transit. |

### Props, characters and kitbash

| Item | Best fit |
|---|---|
| Heavy Big Mecha Unit Kitbash Pack (17 units) | FBX/Blender kitbash. A source for the **M02 Hunter** (AION retrieval unit) silhouette or for M01 security mechs. Needs material setup. |
| FREE SciFi Drone (existing) | **In use**: M00 sim drone (C_Target_Drone). It's also the base for M01 lockdown drones (M01-O01). |

### Audio SFX

| Item | Fit |
|---|---|
| TII 3Step SCI-FI Audio Package | Weapon and tech SFX. A candidate for upgrading the Harrow/sidearm fire layers and M01 turret sounds. |

### Quixel surfaces

Rubber Flooring, Terrazzo, Brushed Metal, Scratched Metal, Painted Metal, Black Marble Tiles, Roman Polished Marble. Terrazzo and the marbles suit the **M00 Crown/antechamber** floors if we refresh materials. The scratched and painted metals suit the **M01/M02** industrial spaces.

## Already owned (from earlier milestones)

- **Environments and kits:** Medical Clinic Sci-Fi, Sci-Fi Light Pack, Sci-Fi Lite Sample, Sci FI Hallway, Niagara Examples, Hologram Shader.
- **Characters:** Game Animation Sample, Paragon Murdock and Wraith, Sci-Fi Mercenary (MESHCORP), Sci-Fi Trooper v3, Sci-Fi Soldier 02, Retro Futuristic Soldier, Waveforce Modular Mercenary.
- **MetaHuman outfits:** Techwear, Tactical Soldier, Casual MetaOutfit, Sci Fi Helmet P05.
- **Weapons:** Free Sci-Fi Rifle, Sci Fi gunpack, Sci-Fi Shots Pack2, Free Weapon SFX.
- **UI and feedback SFX:** Hove Audio UI/health/terminal SFX, Sci-Fi UI SFX Vol.1.
- **Templates and surfaces:** Free FPS Template, Wall Paint, Brushed Aluminum, Smooth Concrete, Ziarat.
- **Not usable in Unreal:** Rain Particles is a Unity package. Use Niagara rain instead.

## M00 music implementation

- **Explore** (unchanged): `MUS_CrownBed` is an original placeholder bed from rooms A to D. It fades over the last 9 m of the gallery and is silent in the antechamber, so the handshake dropout follows the Bible.
- **Combat** (new): `ANVSimulationDirector` now has `SimMusic`, `SimMusicVolume`, the fade times, `MusicToDuck` and `DuckLevel`.
  - The layer starts when the sim run begins, fading in over 3 s at volume 0.22, which sits about 3 dB under the VO.
  - At the same time it ducks `MUS_CrownBed` to 15%.
  - When the sim finishes, the layer fades out over 6 s and the explore bed comes back.
- **Asset:** `/Game/NeonVeil/Fab/Music/MUS_M00_SimSuite_FabCyberPunk06` is a looping import of Cyber Punk v11 Background 6. It's gitignored. The script is `Scripts/Python/nv_music_sim.py`.
