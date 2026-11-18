# Voice lines (ElevenLabs)

The spoken lines are listed in `Scripts/VO/<set>_lines.json`. Each line has an id, a speaker and the subtitle text.

## M00 cast (the master cast for all levels is `Docs/VO_Cast.md`)

| Speaker | ElevenLabs voice | Model |
|---|---|---|
| AION | N.A.V.I. – The Sarcastic Spaceship AI (`HwYMTNpEVtWEr6t0FDKA`) | eleven_v4, [calm, clinical] |
| Simulation | Sigma Centauri – AI Robot (`bAq8AI9QURijOtmeFFqT`) | eleven_v3 (the voice's recommended model) |
| Ops Monitor | Eva – Futuristic Robot Helper (`weA4Q36twV5kwSaTEL0Q`) | eleven_v4 |
| Security | Vector – Tec Voice (`NoiYxL9g25M4orC8Q0ls`) | eleven_v4 |
| Crown News | Daniel – Steady Broadcaster (`onwK4e9ZLuTAKqWW03F9`) | eleven_v4 |
| **GHOST-7** | Vane – Rugged and gravelly (`cymHWdiF8WjUCg6vvFxx`) | eleven_v4. Cast by the owner on 2026-11-13 for the game and all trailers. Direction: weary, restrained anger. |

## Crown Line ride (set `CL`, R_RideDirector)

The ride reuses the cast above: Station PA and Crown News = Daniel (same as the prologue PA), Ops = Eva, AION = N.A.V.I., Ghost-7 = Vane.
The one new role is **CPD Unit 7**: Admiral Action – Military Man (`GLSWsaquVBsIPLPPRi2s`, eleven_v4). Its wavs get a radio band-pass (380 Hz–3.2 kHz) and light bit-crush after `vo_convert.sh`.
The flow is "NEON VEIL – Crown Line Ride VO", with one take per line. The HUD queues lines back to back, so `nv_ride_director.py` spaces the cue times to fit each take. It also re-attaches the CL voices whenever it rebuilds the lines. `CL_Ops_01` ("You're green on the board…") was voiced but is not used, because it didn't fit before the pursuit warning.

The ElevenLabs flow is "NEON VEIL - M00 Voice Lines". It holds two takes per line, and take 1 is the one imported.

## Rule for future runs
Generate one take per line (`generations_count=1`) to save credits. The user asked for this on 2026-11-12.
Regenerate a single line only when it is asked for.

## Pipeline

1. Generate the lines in ElevenLabs. Pronunciation tweaks go in the spoken prompt only (for example "Ghost-Seven").
2. Write `<set>_takes.json` as `{line_id: signed url}`. The URLs are signed and expire, so this file is gitignored.
3. Run `nv_vo_get` in the editor on the PC to download the mp3s to `Saved/VO_raw/`.
4. Run `Tools/vo_convert.sh` to make the wavs in `RawAssets/VO/<set>/`: 48 kHz, mono, -18 LUFS.
5. Run `nv_vo_hook` to import the wavs to `/Game/NeonVeil/Audio/VO/<set>`. It also links each one to its subtitle line by matching the text, and extends the subtitle duration to the audio length plus 0.35 s.

## Operation LANTERN (set `LAN`, M00 gallery holo-table)

Three lines on `D_HoloTable` (Review assignment), between the assignment line and "Proceed to the antechamber": AION = N.A.V.I., Ghost-7 = Vane, one take each, flow "NEON VEIL – LAN VO". Ghost-7's times are spoken as words ("twenty-one twelve"). No new roles. Story context: `Docs/Bible/Continuity.md` (Operation LANTERN).
