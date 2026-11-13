"""NEON VEIL full-game trailer v3.
One continuous Cauldronized bed (123 bpm) at steady level, edited on bar lines; every cut on a beat.
Only one music drop: "Neither do you" -> bass hit on the cut, reverse cymbal from the end of the line
into the resume downbeat. VO processing/levels identical to v2 (approved).
"""
import subprocess, os, re, json, glob
import numpy as np
T = "/mnt/user-data/uploads/NeonVeil/Saved/Trailer"
MUS = "/mnt/user-data/uploads/NeonVeil/Saved/MusicReview/Cauldronized_WAV.wav"
B = "/home/claude/trailer/gbuild3"; os.makedirs(B, exist_ok=True)
FONT_THIN = "/usr/share/fonts/opentype/inter/Inter-Thin.otf"
def run(c): subprocess.run(c, check=True)
SKIPV = os.environ.get("SKIPV") == "1"   # reuse rendered shots when only the audio changes
def dur(f):  return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())
def lufs(f, extra=""):
    o = subprocess.run(["ffmpeg", "-i", f, "-af", (extra + "," if extra else "") + "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])

BB = 0.4876; BAR = 4 * BB; PH = 0.046          # Cauldronized beat, bar, downbeat phase
mbar = lambda n: PH + n * BAR                    # music time of bar n

# motion curves (frame-diff per 1/24 s) for beat-synced in-points
MOT = {}
for j in glob.glob("/home/claude/trailer/motion/*.json"): MOT.update(json.load(open(j)))
def pick_in(f, beats, lo=0.0, hi=None):
    """in-point whose motion accents (positive jumps) fall on the beats inside the slot"""
    m = np.array(MOT[f]); acc = np.maximum(0, np.diff(m, prepend=m[0]))
    d = beats * BB; avail = len(m) / 24
    hi = min(hi if hi is not None else avail, avail - d - 0.02)
    best, bi = -1, lo
    for i in np.arange(lo, max(lo, hi) + 1e-6, 1 / 24):
        s = sum(acc[min(len(acc) - 1, int(round((i + k * BB) * 24)))] * (2 if k % 4 == 0 else 1) for k in range(1, int(beats)))
        if s > best: best, bi = s, i
    return round(float(bi), 3)

A = "auto"
# (file, in, beats, fx)
CUTS = [
 # bars 0-3: quiet intro + build
 ("g3_r01_aerial.mp4", 0.1, 12, "fadein"), ("s01.mp4", 2.0, 4, ""),
 # bars 4-19: full section, Act I
 ("g_w03_weapon.mp4", 0.0, 8, ""), ("s03_test.mp4", A, 6, ""), ("g3_r05_range.mp4", 0.04, 4, ""),
 ("g3_r04_corridor.mp4", 0.0, 8, ""), ("s04.mp4", A, 4, ""), ("g_v06_order.mp4", 0.1, 8, ""),
 ("s07v2.mp4", A, 8, ""), ("s06.mp4", A, 2, ""), ("g_w08_betrayal.mp4", A, 8, ""), ("s08.mp4", A, 4, ""),
 ("BLACK", 0, 2, ""),
 # left for dead spans bar 19 tail + build bar (music bar 38)
 ("g3_r09_dead.mp4", 1.0, 6, ""),
 # music bars 39+: full section, Acts II-V
 ("g_w10_survivor.mp4", A, 8, ""), ("g_w11_market.mp4", A, 6, ""), ("s09.mp4", A, 6, ""),
 ("g_v13_chase.mp4", 0.0, 8, "zoom"), ("g_v19a_chrome.mp4", A, 4, ""), ("g3_r19b_helix.mp4", 0.0, 3, ""),
 ("g_v19c_spindle.mp4", A, 5, ""), ("g_v15_citymachine.mp4", A, 12, ""), ("g_v16_troops.mp4", A, 2, ""),
 ("g_v17_vault.mp4", A, 2, ""), ("g_w20_cathedral.mp4", A, 8, ""),
 ("g_w21_defiance.mp4", 0.1, 8, ""),          # THE drop
 ("g_w22_collapse.mp4", A, 4, ""),            # music resumes on this cut
 # final two bars (music bars 114-115, the track's real ending): 1-beat montage
 ("g_w03_weapon.mp4", 0.85, 1, ""), ("g3_r05_range.mp4", 0.0, 1, ""), ("g3_r04_corridor.mp4", 2.4, 1, ""),
 ("g_w08_betrayal.mp4", 1.15, 1, ""), ("g_v13_chase.mp4", 0.4, 1, ""), ("g_v15_citymachine.mp4", 1.55, 1, ""),
 ("g3_r09_dead.mp4", 3.0, 1, ""), ("g_w22_collapse.mp4", 1.15, 1, ""),
]
CUTS = [(f, pick_in(f, b) if i == A else i, b, x) for f, i, b, x in CUTS]
TITLE_D = 6.5
LB = "crop=1920:804:0:138,pad=1920:1080:0:138:black"
GRADE = ("eq=contrast=1.06:saturation=0.92:gamma=0.97,colorbalance=rs=-0.03:bs=0.04:rh=0.02:bh=-0.02,"
         "vignette=PI/5,noise=alls=7:allf=t")
parts, st = [], []
cum = 0.0; fprev = 0
for i, (f, ss, b, x) in enumerate(CUTS):
    cum += b * BB; fnow = round(cum * 24); nf = fnow - fprev
    o = f"{B}/c{i:02d}.mp4"; parts.append(o); st.append(fprev / 24); fprev = fnow; d = nf / 24
    if SKIPV and os.path.exists(o): continue
    if f == "BLACK":
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r=24:d={d+0.2:.4f}", "-frames:v", str(nf),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", o]); continue
    avail = dur(f"{T}/{f}") - ss
    pre = f"setpts=PTS*{(d / avail) * 1.02:.4f}," if avail < d + 0.05 else ""
    vf = pre + "scale=1920:1080:flags=lanczos,fps=24"
    if x == "zoom": vf = pre + "scale=2300:1294:flags=lanczos,crop=1920:1080,fps=24"
    vf += "," + GRADE + "," + LB + ",format=yuv420p"
    if x == "fadein": vf += ",fade=t=in:st=0:d=1.4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", f"{T}/{f}", "-vf", vf, "-an", "-frames:v", str(nf),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", o])
TITLE_AT = fprev / 24; TOTAL = TITLE_AT + TITLE_D
t = f"{B}/title.mp4"; parts.append(t)
g = "if(lt(t,0.9),if(lt(mod(t*24,4),2),12,-9),0)"
title = (f"color=c=black:s=1920x1080:r=24:d={TITLE_D},"
 f"drawtext=fontfile={FONT_THIN}:text='N E O N    V E I L':fontsize=150:fontcolor=0x9B5CFF:x='(w-tw)/2+({g})':y=(h-th)/2-20:alpha='if(lt(t,0.2),0,if(lt(t,0.8),0.8,0))',"
 f"drawtext=fontfile={FONT_THIN}:text='N E O N    V E I L':fontsize=150:fontcolor=0x22E6FF:x='(w-tw)/2-({g})':y=(h-th)/2-20:alpha='if(lt(t,0.2),0,if(lt(t,0.8),0.7,0))',"
 f"drawtext=fontfile={FONT_THIN}:text='N E O N    V E I L':fontsize=150:fontcolor=white:x=(w-tw)/2:y=(h-th)/2-20:alpha='if(lt(t,0.35),0,if(lt(t,0.8),if(lt(mod(t*24,3),1),0.3,1),1))',"
 "drawbox=x=(iw-min(1400\\,max(0\\,(t-0.9)*1600)))/2:y=ih/2+80:w=min(1400\\,max(0\\,(t-0.9)*1600)):h=2:color=0x9B5CFF@0.95:t=fill:enable='gte(t,0.9)',"
 f"noise=alls=6:allf=t,fade=t=out:st={TITLE_D-1.2}:d=1.2")
if not (SKIPV and os.path.exists(t)): run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", title, "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", t])
open(f"{B}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy", f"{B}/video.mp4"])
for i, (c, s) in enumerate(zip(CUTS, st)): print(f"{i:2d} {s:6.2f} beat {s/BB:6.2f} in {c[1]:5.2f} {c[2]:>3} {c[0]}")
print("TITLE_AT", round(TITLE_AT, 3), "TOTAL", round(TOTAL, 2))

ix = lambda name, k=0: [i for i, c in enumerate(CUTS) if c[0] == name][k]
iW, iOrd, iBet, iS08 = ix("g_w03_weapon.mp4"), ix("g_v06_order.mp4"), ix("g_w08_betrayal.mp4"), ix("s08.mp4")
iSurv, iChase, iCM, iCath = ix("g_w10_survivor.mp4"), ix("g_v13_chase.mp4"), ix("g_v15_citymachine.mp4"), ix("g_w20_cathedral.mp4")
iDef, iCol = ix("g_w21_defiance.mp4"), ix("g_w22_collapse.mp4")
DROP, RESUME = st[iDef], st[iCol]

# ---------------- VO (identical processing/levels to v2)
A_FMT = "aformat=sample_rates=48000:channel_layouts=stereo"
VO = [("g_vo_a1_order.mp3", 0.9), ("g_vo_a2_designed.mp3", st[iW] + 0.5), ("g_vo_a3_unpredictable.mp3", st[iOrd] + 0.3),
      ("g_vo_a4_terminate.mp3", st[iBet] + 0.3), ("g_vo_g1_dead.mp3", st[iSurv] + 0.4), ("g_vo_a5_city.mp3", st[iChase] + 0.35),
      ("g_vo_g2_heart.mp3", st[iCM] + 8 * BB - 0.25), ("g_vo_a6_understand.mp3", st[iCath] + 0.4),
      ("g_vo_g3_neither.mp3", DROP + 0.45), ("g_vo_a7_ghost.mp3", TITLE_AT + 1.8)]
os.makedirs(f"{B}/vo", exist_ok=True)
ins, fl, VOINT = [], [], []
for k, (f, tt) in enumerate(VO):
    p = f"{T}/{f}"
    if "_g" in f:
        eq = "highpass=f=85,equalizer=f=280:t=q:w=1.2:g=-4,equalizer=f=2800:t=q:w=1.0:g=3.5,equalizer=f=9000:t=q:w=1:g=1.5"
    else:
        eq = "highpass=f=110,equalizer=f=320:t=q:w=1.2:g=-4,equalizer=f=3200:t=q:w=1.0:g=4,aecho=0.9:0.5:22:0.12"
    q = f"{B}/vo/{k:02d}.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", p, "-af", f"{A_FMT},{eq},acompressor=threshold=-24dB:ratio=3:attack=4:release=90:makeup=2", q])
    gain = -15.0 - lufs(q); ins += ["-i", q]
    VOINT.append((tt, tt + dur(q)))
    fl.append(f"[{k}:a]volume={gain:.1f}dB,adelay={int(tt*1000)}:all=1[v{k}]")
fl.append("".join(f"[v{k}]" for k in range(len(VO))) + f"amix=inputs={len(VO)}:normalize=0,apad=whole_dur={TOTAL},atrim=0:{TOTAL}[vo]")
run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[vo]", f"{B}/stem_vo.wav"])
for (a, b), (f, _) in zip(VOINT, VO): print(f"VO {a:6.2f}-{b:6.2f} {f}")
NEITHER_END = VOINT[8][1]

# ---------------- music: one track, edited on bar lines, steady level
# trailer bars 0-19 = music bars 0-19 | 20-39 = music 38-57 | 40-41 = 114-115 + the track's own ending
def tbar(n): return n * BAR
SEGS = [(0, 20, 0), (20, 40, 38), (40, 42, 114)]   # (trailer bar from, to, music bar)
fm, ins = [], ["-i", MUS]
for k, (a, b, mb) in enumerate(SEGS):
    s0 = mbar(mb); ln = tbar(b) - tbar(a)
    last = k == len(SEGS) - 1
    ln_take = ln + (3.0 if last else 0.012)
    fm.append(f"[0:a]{A_FMT},atrim={s0-0.006:.4f}:{s0+ln_take:.4f},asetpts=PTS-STARTPTS,"
              f"afade=t=in:st=0:d=0.006,{'' if last else f'afade=t=out:st={ln_take-0.012:.4f}:d=0.012,'}"
              f"adelay={int(round((tbar(a)-0.006)*1000)) if a else 0}:all=1[m{k}]")
# intro rides up a little (track intro is ~20 dB under the full section), fades from quiet to full by bar 4
intro = f"if(lt(t,{tbar(3):.3f}),{10**(7/20):.3f},if(lt(t,{tbar(4):.3f}),{10**(7/20):.3f}-({10**(7/20)-1:.3f})*(t-{tbar(3):.3f})/{BAR:.3f},1))"
# the one drop: hard cut (30 ms) on the defiance cut, back exactly on the collapse downbeat
gate = f"if(between(t,{DROP:.3f},{RESUME-0.004:.3f}),0,1)*min(1,max(0,({DROP:.3f}-t)/0.03)+max(0,(t-{RESUME-0.004:.3f})/0.004))"
fm.append("".join(f"[m{k}]" for k in range(len(SEGS))) + f"amix=inputs={len(SEGS)}:normalize=0,apad=whole_dur={TOTAL},atrim=0:{TOTAL},"
          f"volume='{intro}':eval=frame,volume='min(1,{gate})':eval=frame[mraw]")
run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fm), "-map", "[mraw]", f"{B}/music_raw.wav"])
# level: full section sits at -21 LUFS (VO at -15 -> clear without ducking)
full = lufs(f"{B}/music_raw.wav", f"atrim={tbar(4):.2f}:{tbar(18):.2f}")
mg = -21.0 - full
# clarity without dips: only the 300 Hz-4 kHz band yields ~2-3 dB to the voice; lows and highs untouched
run(["ffmpeg", "-v", "error", "-y", "-i", f"{B}/music_raw.wav", "-i", f"{B}/stem_vo.wav", "-filter_complex",
     f"[0:a]volume={mg:.2f}dB,acrossover=split=300 4000:order=8th[lo][mid][hi];"
     f"[1:a]asplit=1[sc];[mid][sc]sidechaincompress=threshold=0.05:ratio=2:attack=30:release=350:knee=6[midd];"
     f"[lo][midd][hi]amix=inputs=3:normalize=0[m]", "-map", "[m]", f"{B}/stem_music.wav"])
print(f"music gain {mg:.1f} dB  drop {DROP:.3f}-{RESUME:.3f}  neither ends {NEITHER_END:.3f}")

# ---------------- SFX
CYM_LEN = 2.48                                  # reverse cymbal peaks at its very end
cym_take = RESUME - NEITHER_END                 # starts the moment Ghost finishes
cym_ss = max(0.0, CYM_LEN - cym_take)
SFX = [  # (file, time, gain dB, trim_len, extra filter)
    ("sfx_rain.mp3", 0.0, -14, 7.0, ""), ("g_sfx_hydraulic.mp3", st[iW] + 0.05, -7, None, ""),
    ("sfx_glitch.mp3", st[ix("s06.mp4")], -4, None, ""), ("g_sfx_failure.mp3", st[iBet] + 0.5, -9, None, ""),
    ("sfx_impact.mp3", st[iS08], -7, None, ""), ("sfx_rain.mp3", st[ix("BLACK")], -12, 6.0, ""),
    ("g_sfx_riser.mp3", st[iChase] - 4.0, -10, None, ""), ("sfx_impact.mp3", st[iChase], -9, None, ""),
    # the drop: extended bass hit on the cut (shaped into a long decay), reverse cymbal into the resume downbeat
    ("g3_sfx_basshit.mp3", DROP, -8, 4.4, f"lowpass=f=260,afade=t=out:st=0.25:d={RESUME-DROP-0.1:.3f}:curve=tri"),
    ("g3_sfx_revcymbal.mp3", NEITHER_END, -3, None, f"atrim={cym_ss:.3f}:{CYM_LEN:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.25"),
    ("sfx_impact.mp3", RESUME, -6, None, ""),
    ("sfx_glitch.mp3", st[iCol + 1], -6, None, ""), ("sfx_impact.mp3", TITLE_AT, -2, None, ""),
    ("sfx_glitch.mp3", TITLE_AT + 0.2, -4, None, "")]
ins, fl = [], []
for k, (f, tt, gdb, ln, ex) in enumerate(SFX):
    ins += ["-i", f"{T}/{f}"]
    tr = f",atrim=0:{ln},afade=t=in:st=0:d=0.02" if ln else ""
    if ln and not ex: tr = f",atrim=0:{ln},afade=t=in:st=0:d=0.6,afade=t=out:st={ln-1.5}:d=1.5"
    fl.append(f"[{k}:a]{A_FMT}{tr}{(',' + ex) if ex else ''},volume={gdb}dB,adelay={int(max(tt,0)*1000)}:all=1[s{k}]")
fl.append("".join(f"[s{k}]" for k in range(len(SFX))) + f"amix=inputs={len(SFX)}:normalize=0,volume=-3dB,apad=whole_dur={TOTAL},atrim=0:{TOTAL}[s]")
run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[s]", f"{B}/stem_sfx.wav"])

run(["ffmpeg", "-v", "error", "-y", "-i", f"{B}/stem_vo.wav", "-i", f"{B}/stem_music.wav", "-i", f"{B}/stem_sfx.wav",
     "-filter_complex", f"[0][1][2]amix=inputs=3:normalize=0:duration=longest,atrim=0:{TOTAL},alimiter=limit=0.89:attack=3:release=60,loudnorm=I=-14:TP=-1.0:LRA=11[a]",
     "-map", "[a]", "-ar", "48000", "-c:a", "pcm_s16le", f"{B}/mix.wav"])
run(["ffmpeg", "-v", "error", "-y", "-i", f"{B}/video.mp4", "-i", f"{B}/mix.wav", "-map", "0:v", "-map", "1:a",
     "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "16M", "-bufsize", "32M", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", f"{B}/NeonVeil_Trailer_v3.mp4"])
json.dump({"st": st, "cuts": CUTS, "vo": VOINT, "drop": DROP, "resume": RESUME, "title": TITLE_AT, "total": TOTAL}, open(f"{B}/timeline.json", "w"))
print("built")
