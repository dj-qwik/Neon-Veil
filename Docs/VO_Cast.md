# NEON VEIL: voice cast (ElevenLabs)

This is the master cast list. Every new level, cutscene or trailer reuses these voices so each character always sounds the same. Add a new role here before generating its first line.

## Cast

| Character | ElevenLabs voice | Voice ID | Model and direction | First used |
|---|---|---|---|---|
| **GHOST-7** (player) | Vane – Rugged and gravelly | `cymHWdiF8WjUCg6vvFxx` | eleven_v4. Weary, restrained anger, low. Cast by the owner for the game and all trailers. | Trailer v1, M00P, Crown Line |
| **AION** | N.A.V.I. – The Sarcastic Spaceship AI | `HwYMTNpEVtWEr6t0FDKA` | eleven_v4, `[calm, clinical]` | M00 |
| **Ops Monitor / Directorate Ops** | Eva – Futuristic Robot Helper | `weA4Q36twV5kwSaTEL0Q` | eleven_v4, `[crisp, over a comm channel]` | M00, M00P, Crown Line |
| **Simulation Suite** | Sigma Centauri – AI Robot | `bAq8AI9QURijOtmeFFqT` | eleven_v3, the voice's recommended model | M00 |
| **Security** (scanners, arches) | Vector – Tec Voice | `NoiYxL9g25M4orC8Q0ls` | eleven_v4, `[flat, automated]` | M00, M00P |
| **Crown News** | Daniel – Steady Broadcaster | `onwK4e9ZLuTAKqWW03F9` | eleven_v4, `[news anchor]` | M00, Crown Line |
| **Station PA** (Crown Line, transit) | Daniel – Steady Broadcaster | `onwK4e9ZLuTAKqWW03F9` | eleven_v4, `[station announcement, calm]` | M00P, Crown Line |
| **CPD officers** (police radio) | Admiral Action – Military Man | `GLSWsaquVBsIPLPPRi2s` | eleven_v4. Radio filter in post: see below. | Crown Line |

Daniel voices both Crown News and the Station PA. If those two ever speak back to back, or a level needs a separate announcer, cast a new voice for the PA and record it here.

## Rules

- **One take per line** (`generations_count=1`), to save credits. Regenerate a single line only when the owner asks.
- In the spoken prompt, write "Ghost-7" as "Ghost-Seven". Subtitle text stays "Ghost-7".
- Each set gets its own ElevenLabs flow, named `NEON VEIL – <set> VO`.
- **Pipeline:** `Scripts/VO/README.md`. In short:
  1. Write `<set>_lines.json`.
  2. Generate the lines.
  3. Write `<set>_takes.json`. The URLs in it are signed, so the file is gitignored.
  4. Run `nv_vo_get <set>` in the editor.
  5. Run `Tools/vo_convert.sh`.
  6. Run `nv_vo_hook <set>`.
- **Radio voices** (CPD and any police or comms chatter) get this after `vo_convert.sh`:
  `highpass=f=380,lowpass=f=3200,acrusher=bits=10:mix=0.25,volume=1.4,alimiter=limit=0.9`
- **Loudness:** every SoundWave under `Audio/VO` plays through the `SMX_NV_Voice` submix, which has a limiter (`DP_NV_VoiceLimiter`). The HUD boosts voice by `VoiceVolume` (2.2x). `nv_vo_hook` routes new imports to that submix automatically. For older imports, run `nv_vo_submix.py` once.
- The HUD plays subtitle lines one after another. When lines are timed, space their cues by each take's length plus 0.35 s.

## Existing flows

| Set | Flow |
|---|---|
| M00 (Glass Crown sim) | NEON VEIL - M00 Voice Lines |
| M00P (prologue) | NEON VEIL – Prologue VO (Crown Line) |
| CL (Crown Line ride) | NEON VEIL – Crown Line Ride VO |
| GC (Glass Crown extras: atrium entry scanner) | NEON VEIL – Crown Line Ride VO |
| Trailers | NEON VEIL – Intro Trailer, NEON VEIL – Ghost Protocol Trailer |
