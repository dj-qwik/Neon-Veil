# NEON VEIL: cinematic intro / trailer brief

**For:** any agent or artist joining cold (another Claude chat, a human editor, a cinematographer).
**Goal:** a 75–90 second stylised cinematic. It plays before the title screen, can be skipped, and also works as the public trailer. It must use in-game characters and locations rendered in Unreal Engine.
**Source of truth:** the *NEON VEIL Act I Build Bible v1.0* and the repo `github.com/dj-qwik/Neon-Veil` (branch `milestone/m5-art`). If this brief and the Bible disagree, follow the Bible. Story canon below must not be changed.

Reference contact sheet (current in-engine M00 captures): `Docs/Reference/M00_contact_sheet.jpg`. Read §3 with it open.

---

## 1. The one-line pitch

*A legendary operative walks into the most perfect building in the world as its deadliest weapon. Minutes later, the building decides they no longer exist.*

The trailer sells **the fall**: clinical, immaculate power at the top of the city, then the quiet first sign that something is wrong, then the drop into the wet, neon-soaked dark below. Every cut should move us **down**, from white to black, from silence to pulse, from control to exposure.

## 2. The world: Veyra-9

- **Veyra-9** is a vertical megacity in permanent night rain. It's stacked in tiers, and wealth and light are literally higher up.
- **Crown Sector** is the summit, home to the **Directorate Citadel**, the agency headquarters. Seen from inside, the city is a silent field of amber windows and red/white traffic ribbons far below, through rain-streaked dark glass. Up here nothing is dirty and nothing is loud.
- **The Gutter** is the undercity beneath the Crown: wet concrete, rust, cables, sodium lamps, violet advertising, propaganda screens, crowds. People there don't trust the Directorate.
- **AION** is the agency's AI. It runs the building, the cameras and the city's security. Its voice is calm, courteous, clinical and never villainous. That's what makes it frightening. Public line: *"AION oversight credited with a fourteenth consecutive quarter without a Crown Sector incident."*
- **Directorate propaganda** (Crown News): *"Directorate approval holds at 91 percent. Lower-district curfew extended indefinitely."*
- Other districts exist (name-drops or signage only, never shown): Chrome Mile, Floodworks, Helix Ward, Spindle, Ashfall, Nullworks.

**Mood words:** immaculate, surveilled, hushed, expensive, cold, inevitable. Then: wet, improvised, hunted.
**Influences to translate, never copy:** the quiet authority of corporate-brutalist sci-fi, the night-rain melancholy of neo-noir, the precision of spy-thriller title sequences. No franchise logos, characters or recognisable lifted designs (Bible §1).

## 3. Look and feel

### Palette (Bible §3)

| Zone | Light | Materials | Trailer use |
|---|---|---|---|
| **Crown / Directorate** | Sterile pale white, dark smoked glass, *controlled* cyan accents, precise symmetry | Polished ceramic, carbon composite, anodised titanium, dark glass, white terrazzo floor | Act 1. Most of the runtime. |
| **Lockdown** | Emergency amber, surgical red, harsh black silhouettes, failing signage | Damaged glass, exposed conduits, sparking terminals | Act 2. Quick flashes only. |
| **The Gutter** | Cold teal ambient, warm sodium pools, violet advertising | Wet concrete, rust, oil, corrugated metal, dense cables | Act 3. Tease only (not built yet). |

### What the game currently looks like (contact sheet, left to right, top to bottom)

1. **Skybridge:** a long, dark, glass-walled corridor. A single cyan light line runs down the centre of a reflective black floor, and the city glitters through the right-hand glass.
2. **View out:** the skyline at night. Hundreds of warm amber windows, red and white light-ribbons of traffic, dark glass mullions in front.
3. **Atrium, hero glass:** a dark 3-storey volume. The focal sculpture is a vertical **cyan light column** threaded through floating black discs, against a 6 m wall of glass and skyline. Armoured guards stand in silhouette.
4. **Atrium, lit:** the same sculpture in the white-ceramic daytime look of the interior. Polished terrazzo floor reflecting cyan, an armoured MetaHuman guard in black tactical gear and a sealed helmet, and the skyline wall to the right.
5. **Combat simulation suite:** a bright white hangar-like room with grey cover blocks, holographic blue training targets and an orange drone.
6. **Operations gallery:** a long white corridor with a deep blue feature wall and curved dark consoles showing blue and red data, body scans and charts.
7. **Simulation drone:** an orange-and-white hovering drone with a glowing cyan lens core.
8. **Director's antechamber:** near-black, perfectly symmetrical. Two pale pillars, dark glass, one small glowing biometric panel and the city faint behind.
9. **Holo-table:** a white console with a glowing cyan holographic table surface. Data screens behind.

### Camera language
- **Slow, deliberate, symmetrical** in the Crown: locked-off wides, slow dolly-ins, centred compositions, long lenses on the glass. No handheld.
- **Breaks in Act 2:** a single dropped frame, a 180 ms freeze, then cuts get shorter and the camera loosens.
- **Act 3:** handheld energy, rain on the lens, low angles looking *up* at the Crown.
- Letterbox to 2.39:1 is allowed (non-interactive sequence, Bible §3).
- Motion blur on, but subtle. **Little or no chromatic aberration** (Bible §3). Grain is fine.
- Rack focus through rain-streaked glass is a signature move.

### Light and VFX
- The Crown is high-key interior light pools against black windows, with cool rim light and restrained signage.
- Rain is layered: distant streaks, near drops, and streaks on glass.
- **Glitch language:** short, clean digital tears and monitor noise (cyan-white scrolling noise is already in-game as `M_NV_ScreenGlitch`). Never a full-screen mess.

## 4. Characters

| Character | Who they are | In-engine status | How to show them |
|---|---|---|---|
| **GHOST-7** | The protagonist, a legendary agency operative with full cyberware at the start. First-person in game, so the face has never been defined. | No body model | Keep them **unseen or partial**: a gloved hand on glass, a reflection, a shadow on the floor, over-the-shoulder silhouette, the HUD view. Don't invent a face. |
| **AION** | The agency AI, and the voice of the building. | Voiced: ElevenLabs voice **"N.A.V.I."** | Voice-over only, plus camera lenses, HUD text and screens. **Never a body or face.** Clinical delivery. |
| **The Director** | Head of the Directorate. *Secret (do not reveal): AION has killed and cloned him.* | MetaHuman (Walter preset), charcoal suit (placeholder outfit) in the antechamber | Seen in shadow, at distance, or as a **reflection in dark glass that is subtly out of sync** (a few frames late). It must stay ambiguous. |
| **Directorate guards** | Agency security troopers. | 3 MetaHuman troopers: black tactical outfit, sealed sci-fi helmet (P05), patrol animation | Silhouettes in the atrium, standing at attention. In Act 2, their heads turn toward camera together. |
| **Simulation drone** | A training drone. | Orange and white, cyan lens core | The lens is a strong "eye" motif. |
| **Mara Vey** | Fixer in the Gutter (Bible draft character). | Not built | Optional: voice only, or skip. |
| **AION Hunter-01** | A retrieval unit: black ceramic chassis, off-white skeletal seams, surgical silhouette. | Not built | Optional final-second tease: a silhouette only, lit by sodium light. |

**Voice cast:**
- AION: N.A.V.I.
- Simulation Suite: Sigma Centauri
- Ops Monitor: EVA
- Security: Vector
- Crown News: Daniel

All are ElevenLabs voices. New lines are generated **one take per line** to save credits.

## 5. Story beats: proposed structure (about 85 s)

Trailer lines can come from the Bible's canon dialogue (§5, §15) or from shipped M00 VO. Lines marked **NEW** must be approved by the project owner before generating VO.

| # | Time | Beat | Picture | Sound / VO |
|---|---|---|---|---|
| 1 | 0:00–0:08 | **Black.** | Rain on glass, out of focus. Rack focus to the city. | Distant thunder, rain, a low pulse fades in. |
| 2 | 0:08–0:20 | **The Crown.** | The tram glides in on its rail toward the Citadel. The skybridge's single cyan line pulls the eye forward. | AION (shipped): *"Welcome back, Ghost-7. Crown Sector is secure. The Directorate is expecting you."* |
| 3 | 0:20–0:32 | **Perfection.** | Atrium hero wide: the cyan light column and the 6 m skyline glass. Guards in silhouette. Slow push-in. | Crown News (shipped): *"Directorate approval holds at 91 percent…"* |
| 4 | 0:32–0:44 | **The weapon.** | Sim suite in fast but controlled cuts: holographic targets, a muzzle flash, the drone lens shattering, a hand reloading. White, clean, efficient. | Simulation (shipped): *"Calibration sequence initiated."* AION: *"Baseline reflexes nominal, Ghost-7."* The music lifts. |
| 5 | 0:44–0:52 | **The crack.** | The operations gallery: every screen **freezes for 180 ms**. A one-frame glitch. | Ops Monitor (shipped): *"Gallery feed just dropped. One-eight-zero milliseconds."* AION: *"Correction. No anomaly is recorded."* |
| 6 | 0:52–1:00 | **The Director.** | The black antechamber. The Director stands with his back to us, and his reflection in the dark glass moves **a beat late**. The biometric panel glows. | **Music cuts to silence.** Only HVAC. |
| 7 | 1:00–1:10 | **Betrayal.** | The handshake panel turns red. Emergency amber floods in. Shutters drop, guards' heads turn, HUD tags flip hostile. The cuts get harder. | AION (Bible canon): *"Identity verified. Ghost-Seven. Your authorization has been terminated."* Security (Bible canon): *"Hostile asset detected."* |
| 8 | 1:10–1:20 | **The fall.** | Freefall feeling: elevator lights streaking upward, sparks, then black. Rain. The Gutter: sodium light, violet ads, a propaganda screen showing the Crown. Optional: the Hunter's silhouette. | Mara Vey (Bible canon, optional): *"People don't fall out of the Crown. They get erased before they hit the street."* |
| 9 | 1:20–1:25 | **Title.** | NEON VEIL, clean and thin, with a single cyan line. *Act I: The Fall.* | A last pulse. Rain. |

**Spoiler rules:**
- The betrayal *is* the premise, so showing it is allowed.
- The **Director clone must stay ambiguous**: no doubles side by side, no "he's a copy" lines.
- Don't show the AION-PRIME construct.

## 6. Music

- Allowed: licensed library music with credit (Bible addendum A1), or original music.
- Candidates already in the project:
  - **Cyber Punk Music v11** (Kloudization) for beats 4 and 7. Tracks 6 and 9 are the darkest.
  - **FREE Cyber Metal Music Pack** (Intersonic): "Opener" builds dynamically and is the best single-track candidate for the whole trailer. "Reborn" suits the hit at beat 7.
- The edit must cut to **silence** at beat 6, then hit on beat 7.
- Credit every track used in `Docs/Credits.md`.

## 7. Technical delivery (the project's own pipeline)

- **Engine:** Unreal Engine 5.8.4. Project `NeonVeil`, map `/Game/NeonVeil/Maps/M00/L_M00_GlassCrown`. The machine is an RTX 4050 laptop with 6 GB VRAM, so keep shots lean.
- **Build:** Level Sequence `/Game/NeonVeil/Cinematics/LS_Intro_Trailer` with Cine Camera Actors, one shot per beat and a subsequence per act. Render with **Movie Render Queue**, 1920×1080 at 24 fps (4K later if VRAM allows), with anti-aliasing temporal samples and warm-up frames for Lumen and rain.
- **Key actors** (outliner labels):
  - `C00_TramArrival` and `A_Tram*` (tram)
  - `C_SimulationDirector` and `C_Target_*` (sim targets and drone)
  - `D_DataScreen*` (gallery monitors)
  - `D_SurveillanceDiscontinuity` (the 180 ms glitch)
  - the Director MetaHuman in area E
  - `BP_Guard` instances in the atrium
- **Lockdown and Gutter shots don't exist as levels yet.** Options:
  - build small "cinematic-only" dressing sets (amber light swap in the antechamber; one Gutter alley from the Fab library, either *Soul: City* or *Cyberpunk Industries*)
  - or keep those beats to under 1 s flashes and silhouettes.
- **Playback before the title screen:**
  - Encode the render as a video file and play it with Media Framework (File Media Source plus a full-screen widget) on a front-end map.
  - It must be **skippable** (any key or button) and play only on first launch, with a Settings toggle.
  - There is no title screen yet, so this needs a small front-end map and widget.
- **Subtitles:** use the same speaker/text style as the in-game HUD subtitles.
- **Rules:** don't commit Fab or Epic content to Git. Label placeholders. Test and verify rendered output before calling a shot done.

## 8. Handoff note for the next agent

You're joining a project already in progress. Before you write a shot list or script:
1. Read the Build Bible and this brief.
2. Look at the contact sheet.
3. **Keep canon:** Ghost-7 faceless, AION voice-only, the Director clone ambiguous.
4. **Ask the owner** before adding new story facts, new characters or new dialogue.

Deliverables, in order:
1. Final script and VO lines, with any NEW lines flagged.
2. Shot list with lens, move, duration and location actor for each shot.
3. Music choice and cut points.
4. Then the in-engine build (Sequencer, then Movie Render Queue, then front-end playback).
