# Voice lines (ElevenLabs)

The spoken lines are listed in `Scripts/VO/<set>_lines.json`. Each line has an id, a speaker and the subtitle text.

## M00 cast

| Speaker | ElevenLabs voice | Model |
|---|---|---|
| AION | N.A.V.I. – The Sarcastic Spaceship AI (`HwYMTNpEVtWEr6t0FDKA`) | eleven_v4, [calm, clinical] |
| Simulation | Sigma Centauri – AI Robot (`bAq8AI9QURijOtmeFFqT`) | eleven_v3 (the voice's recommended model) |
| Ops Monitor | Eva – Futuristic Robot Helper (`weA4Q36twV5kwSaTEL0Q`) | eleven_v4 |
| Security | Vector – Tec Voice (`NoiYxL9g25M4orC8Q0ls`) | eleven_v4 |
| Crown News | Daniel – Steady Broadcaster (`onwK4e9ZLuTAKqWW03F9`) | eleven_v4 |

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
