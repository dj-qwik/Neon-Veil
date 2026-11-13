"""NEON VEIL full-game trailer v2: beat-locked cuts, cleaned and normalized VO, musical drops."""
import subprocess, os, re
T = "/mnt/user-data/uploads/NeonVeil/Saved/Trailer"
MUS = "/mnt/user-data/uploads/NeonVeil/Saved/MusicReview"
B = "/home/claude/trailer/gbuild2"; os.makedirs(B, exist_ok=True)
FONT_THIN = "/usr/share/fonts/opentype/inter/Inter-Thin.otf"
def run(c): subprocess.run(c, check=True)
def dur(f):  return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())
def lufs(f):
    o = subprocess.run(["ffmpeg", "-i", f, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])

BA = 0.8243               # Opener beat (72.8 bpm half-time feel)
OFF_A = 0.163 + 14 * BA   # bar-aligned start ~11.70 s
BB = 0.4876               # Cauldronized beat (123 bpm)
BAR = 4 * BB
OFF_B = 0.046 + 140 * BB  # bar-aligned ~68.31 s; full section lands 16 beats later

# (file, in, beats, beat_len, fx)
A = [("g_v01_aerial.mp4", 0.0, 8, BA, "fadein"), ("s01.mp4", 2.0, 2, BA, ""), ("g_w03_weapon.mp4", 0.4, 4, BA, ""),
     ("s03_test.mp4", 2.0, 2, BA, ""), ("g_w04_corridor.mp4", 0.6, 3, BA, ""), ("s05.mp4", 1.0, 2, BA, ""),
     ("s04.mp4", 3.0, 2, BA, ""), ("g_v06_order.mp4", 0.2, 4, BA, ""), ("s07v2.mp4", 2.5, 3, BA, ""),
     ("s06.mp4", 0.8, 1, BA, ""), ("g_w08_betrayal.mp4", 0.2, 4, BA, ""),
     ("s08.mp4", 0.5, 2, BA, ""), ("BLACK", 0, 1, BA, ""), ("g_w09_dead.mp4", 1.2, 2.5, BA, "")]
Bc = [("g_w10_survivor.mp4", 0.4, 6, BB, ""), ("g_w11_market.mp4", 0.6, 6, BB, ""), ("s09.mp4", 4.4, 4, BB, ""),
      ("g_v13_chase.mp4", 0.0, 8, BB, "zoom"), ("g_v19a_chrome.mp4", 0.2, 4, BB, ""), ("g_v19b_helix.mp4", 0.6, 2, BB, ""),
      ("g_v19c_spindle.mp4", 1.0, 4, BB, ""), ("g_v15_citymachine.mp4", 0.3, 12, BB, ""), ("g_v16_troops.mp4", 1.0, 2, BB, ""),
      ("g_v17_vault.mp4", 1.0, 2, BB, ""), ("g_w20_cathedral.mp4", 0.0, 8, BB, ""), ("g_w21_defiance.mp4", 0.3, 8, BB, ""),
      ("g_w22_collapse.mp4", 0.3, 6, BB, ""), ("g_w03_weapon.mp4", 3.2, 1, BB, ""), ("g_v06_order.mp4", 3.0, 1, BB, ""),
      ("g_w08_betrayal.mp4", 0.3, 1, BB, ""), ("g_w22_collapse.mp4", 2.4, 1, BB, "")]
CUTS = [(f, i, b * L, x) for f, i, b, L, x in A + Bc]
TITLE_D = 6.5
LB = "crop=1920:804:0:138,pad=1920:1080:0:138:black"
GRADE = ("eq=contrast=1.06:saturation=0.92:gamma=0.97,colorbalance=rs=-0.03:bs=0.04:rh=0.02:bh=-0.02,"
         "vignette=PI/5,noise=alls=7:allf=t")
parts, st, acc = [], [], 0.0
cum = 0.0; fprev = 0
for i, (f, ss, d, x) in enumerate(CUTS):
    cum += d; fnow = round(cum * 24); nf = fnow - fprev
    o = f"{B}/c{i:02d}.mp4"; parts.append(o); st.append(fprev / 24); fprev = fnow; d = nf / 24; acc = fnow / 24
    if f == "BLACK":
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r=24:d={d+0.2:.4f}", "-frames:v", str(nf),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", o]); continue
    avail = dur(f"{T}/{f}") - ss
    pre = f"setpts=PTS*{(d / avail) * 1.02:.4f}," if avail < d + 0.05 else ""
    vf = pre + "scale=1920:1080:flags=lanczos,fps=24"
    if x == "zoom": vf = "scale=2300:1294:flags=lanczos,crop=1920:1080,fps=24"
    vf += "," + GRADE + "," + LB + ",format=yuv420p"
    if x == "fadein": vf += ",fade=t=in:st=0:d=1.4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", f"{T}/{f}", "-vf", vf, "-an", "-frames:v", str(nf),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", o])
TITLE_AT = acc; TOTAL = acc + TITLE_D
t = f"{B}/title.mp4"; parts.append(t)
g = "if(lt(t,0.9),if(lt(mod(t*24,4),2),12,-9),0)"
title = (f"color=c=black:s=1920x1080:r=24:d={TITLE_D},"
 f"drawtext=fontfile={FONT_THIN}:text='N E O N    V E I L':fontsize=150:fontcolor=0x9B5CFF:x='(w-tw)/2+({g})':y=(h-th)/2-20:alpha='if(lt(t,0.2),0,if(lt(t,0.8),0.8,0))',"
 f"drawtext=fontfile={FONT_THIN}:text='N E O N    V E I L':fontsize=150:fontcolor=0x22E6FF:x='(w-tw)/2-({g})':y=(h-th)/2-20:alpha='if(lt(t,0.2),0,if(lt(t,0.8),0.7,0))',"
 f"drawtext=fontfile={FONT_THIN}:text='N E O N    V E I L':fontsize=150:fontcolor=white:x=(w-tw)/2:y=(h-th)/2-20:alpha='if(lt(t,0.35),0,if(lt(t,0.8),if(lt(mod(t*24,3),1),0.3,1),1))',"
 "drawbox=x=(iw-min(1400\\,max(0\\,(t-0.9)*1600)))/2:y=ih/2+80:w=min(1400\\,max(0\\,(t-0.9)*1600)):h=2:color=0x9B5CFF@0.95:t=fill:enable='gte(t,0.9)',"
 f"noise=alls=6:allf=t,fade=t=out:st={TITLE_D-1.2}:d=1.2")
run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", title, "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", t])
open(f"{B}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy", f"{B}/video.mp4"])
NA = len(A)
for i, (c, s) in enumerate(zip(CUTS, st)): print(f"{i:2d} {s:6.2f} {c[2]:5.2f} {c[0]}")
print("TOTAL", round(TOTAL, 2))

# ---------------- audio stems
A_FMT = "aformat=sample_rates=48000:channel_layouts=stereo"
HIT = st[11]                     # lockdown cut: Opener stops on the hit
B0 = st[NA]                      # Cauldronized starts with the survivor
iC = NA + 7                      # city machine
iDef = NA + 11                   # defiance
VO = [("g_vo_a1_order.mp3", 0.9), ("g_vo_a2_designed.mp3", st[2] + 0.5), ("g_vo_a3_unpredictable.mp3", st[7] + 0.3),
      ("g_vo_a4_terminate.mp3", st[10] + 0.3), ("g_vo_g1_dead.mp3", st[NA] + 0.6), ("g_vo_a5_city.mp3", st[NA + 3] + 0.35),
      ("g_vo_g2_heart.mp3", st[iC] + 8 * BB - 0.25), ("g_vo_a6_understand.mp3", st[NA + 10] + 0.4),
      ("g_vo_g3_neither.mp3", st[iDef] + 4 * BB + 0.1), ("g_vo_a7_ghost.mp3", TITLE_AT + 1.8)]
# VO: each line cleaned and leveled to -16 LUFS. Ghost-7 warm + present; AION clean, faint short slap for a synthetic edge
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
# music dips 9 dB under each line (150 ms ramps)
duck = "*".join(f"(1-0.645*max(0,min(1,min((t-{a-0.15:.3f})/0.15,({b+0.1:.3f}-t)/0.2))))" for a, b in VOINT)

# Music: Opener (bar-aligned) up to the lockdown hit, short tail; Cauldronized from the survivor, bar-aligned.
# Drops are 1-bar-long and end exactly on a downbeat; resumption = same track position (stays on the grid).
heart_drop = (st[iC] + 8 * BB, st[iC] + 12 * BB)          # last bar of the city-machine shot
def_drop = (st[iDef], st[iDef] + 8 * BB)                  # whole defiance shot (2 bars)
end_cut = TITLE_AT
def gate(lo, hi, base):  # 25 ms ramps at drop edges, measured from stem start 'base'
    a, b = lo - base, hi - base
    return (f"min(1,max(0,(t-{b:.3f})/0.02))+max(0,min(1,({a:.3f}-t)/0.03))")
gexpr = f"min(1,({gate(*heart_drop, B0)})*({gate(*def_drop, B0)}))"
fm = [f"[0:a]{A_FMT},atrim={OFF_A:.3f}:{OFF_A+HIT:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=3,afade=t=out:st={HIT-0.05:.3f}:d=0.05[ma]",
      f"[1:a]{A_FMT},atrim={OFF_B:.3f}:{OFF_B+TOTAL-B0:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.2,"
      f"volume='{gexpr}':eval=frame,afade=t=out:st={end_cut-B0-0.03:.3f}:d=0.03,adelay={int(B0*1000)}:all=1[mb]",
      f"[ma][mb]amix=inputs=2:normalize=0,volume=-8dB,apad=whole_dur={TOTAL},atrim=0:{TOTAL},volume='{duck}':eval=frame[m]",
      f"[m][2:a]sidechaincompress=threshold=0.02:ratio=4:attack=10:release=250[md]"]
run(["ffmpeg", "-v", "error", "-y", "-i", f"{MUS}/Opener_WAV.wav", "-i", f"{MUS}/Cauldronized_WAV.wav", "-i", f"{B}/stem_vo.wav",
     "-filter_complex", ";".join(fm), "-map", "[md]", f"{B}/stem_music.wav"])

# SFX: impacts on downbeats, risers ending on downbeats
SFX = [("sfx_rain.mp3", 0.0, -14, 7.0), ("g_sfx_hydraulic.mp3", st[2] + 0.2, -2, None), ("sfx_glitch.mp3", st[9], -2, None),
       ("g_sfx_failure.mp3", st[10] + 0.5, 0, None), ("sfx_impact.mp3", HIT, 2, None), ("sfx_rain.mp3", st[12], -10, 9.0),
       ("g_sfx_riser.mp3", st[NA + 3] - 4.0, -3, None), ("sfx_impact.mp3", st[NA + 3], -2, None),
       ("sfx_impact.mp3", heart_drop[1], 2, None), ("g_sfx_riser.mp3", st[iDef + 1] - 4.0, -5, None),
       ("sfx_impact.mp3", def_drop[1], 3, None), ("sfx_glitch.mp3", st[NA + 13], -4, None), ("sfx_impact.mp3", TITLE_AT, 3, None),
       ("sfx_glitch.mp3", TITLE_AT + 0.2, -4, None)]
ins, fl = [], []
for k, (f, tt, g, ln) in enumerate(SFX):
    ins += ["-i", f"{T}/{f}"]
    tr = f",atrim=0:{ln},afade=t=in:st=0:d=0.6,afade=t=out:st={ln-1.5}:d=1.5" if ln else ""
    fl.append(f"[{k}:a]{A_FMT}{tr},volume={g}dB,adelay={int(max(tt,0)*1000)}:all=1[s{k}]")
fl.append("".join(f"[s{k}]" for k in range(len(SFX))) + f"amix=inputs={len(SFX)}:normalize=0,volume=-3dB,apad=whole_dur={TOTAL},atrim=0:{TOTAL}[s]")
run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[s]", f"{B}/stem_sfx.wav"])

run(["ffmpeg", "-v", "error", "-y", "-i", f"{B}/stem_vo.wav", "-i", f"{B}/stem_music.wav", "-i", f"{B}/stem_sfx.wav",
     "-filter_complex", f"[0][1][2]amix=inputs=3:normalize=0:duration=longest,atrim=0:{TOTAL},alimiter=limit=0.89:attack=3:release=60,loudnorm=I=-14:TP=-1.0:LRA=10[a]",
     "-map", "[a]", "-ar", "48000", "-c:a", "pcm_s16le", f"{B}/mix.wav"])
run(["ffmpeg", "-v", "error", "-y", "-i", f"{B}/video.mp4", "-i", f"{B}/mix.wav", "-map", "0:v", "-map", "1:a",
     "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "16M", "-bufsize", "32M", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", f"{B}/NeonVeil_Trailer_v2.mp4"])
print("built")
