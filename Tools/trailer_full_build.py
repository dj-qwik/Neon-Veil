"""NEON VEIL - full-game trailer edit (v1). Hard cuts, grade, grain, 2.39 letterbox, Fab score, VO + SFX."""
import subprocess, os
T = "/mnt/user-data/uploads/NeonVeil/Saved/Trailer"
MUS = "/mnt/user-data/uploads/NeonVeil/Saved/MusicReview"
B = "/home/claude/trailer/gbuild"; os.makedirs(B, exist_ok=True)
FONT_THIN = "/usr/share/fonts/opentype/inter/Inter-Thin.otf"
def run(c): subprocess.run(c, check=True)

# (file, in-point, duration, extra-vf)
CUTS = [
 ("g_v01_aerial.mp4", 0.0, 6.0, "fadein"),
 ("s01.mp4", 2.0, 1.5, ""),
 ("g_w03_weapon.mp4", 0.4, 3.0, ""),
 ("s03_test.mp4", 2.0, 1.5, ""),
 ("g_w04_corridor.mp4", 0.6, 2.5, ""),
 ("s05.mp4", 1.0, 1.5, ""),
 ("s04.mp4", 3.0, 1.5, ""),
 ("g_v06_order.mp4", 0.3, 3.5, ""),
 ("s07v2.mp4", 2.5, 2.0, ""),
 ("s06.mp4", 0.8, 1.0, ""),
 ("g_w08_betrayal.mp4", 0.2, 3.0, ""),
 ("s08.mp4", 0.5, 1.5, ""),
 ("BLACK", 0, 0.7, ""),
 ("g_w09_dead.mp4", 0.5, 3.0, ""),
 ("g_w10_survivor.mp4", 0.4, 3.3, ""),
 ("g_w11_market.mp4", 0.5, 3.0, ""),
 ("s09.mp4", 4.5, 2.0, ""),
 ("g_v13_chase.mp4", 0.0, 3.0, "zoom"),
 ("g_v19a_chrome.mp4", 0.2, 2.0, ""),
 ("g_v19b_helix.mp4", 0.5, 1.5, ""),
 ("g_v19c_spindle.mp4", 1.0, 2.0, ""),
 ("g_v15_citymachine.mp4", 0.3, 4.5, ""),
 ("g_v16_troops.mp4", 1.0, 1.2, ""),
 ("g_v17_vault.mp4", 0.8, 1.5, ""),
 ("g_w20_cathedral.mp4", 0.0, 4.0, ""),
 ("g_w21_defiance.mp4", 0.3, 3.0, ""),
 ("g_w22_collapse.mp4", 0.3, 3.0, ""),
 ("g_w03_weapon.mp4", 3.2, 0.4, ""),
 ("g_v06_order.mp4", 3.0, 0.4, ""),
 ("g_w08_betrayal.mp4", 0.3, 0.4, ""),
 ("g_w22_collapse.mp4", 2.4, 0.4, ""),
 ("BLACK", 0, 0.5, ""),
]
TITLE_D = 6.5
LB = "crop=1920:804:0:138,pad=1920:1080:0:138:black"
GRADE = ("eq=contrast=1.06:saturation=0.92:gamma=0.97,"
         "colorbalance=rs=-0.03:bs=0.04:rh=0.02:bh=-0.02,"
         "vignette=PI/5,noise=alls=7:allf=t")

parts = []; starts = []; acc = 0.0
for i, (f, ss, d, x) in enumerate(CUTS):
    o = f"{B}/c{i:02d}.mp4"; parts.append(o); starts.append(acc); acc += d
    if f == "BLACK":
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r=24:d={d}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", o]); continue
    if os.path.exists(o) and not os.environ.get("REBUILD"): continue
    vf = "scale=1920:1080:flags=lanczos,fps=24"
    if x == "zoom": vf = "scale=2150:1210:flags=lanczos,crop=1920:1080,fps=24"
    vf += "," + GRADE + "," + LB + ",format=yuv420p"
    if x == "fadein": vf += ",fade=t=in:st=0:d=1.4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(d), "-i", f"{T}/{f}", "-vf", vf, "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", o])
TITLE_AT = acc
# title: NEON VEIL with violet/cyan glitch-in, cyan line, fade
t = f"{B}/title.mp4"; parts.append(t)
g = "if(lt(t,0.9),if(lt(mod(t*24,4),2),12,-9),0)"
title = ("color=c=black:s=1920x1080:r=24:d=%s," % TITLE_D +
 f"drawtext=fontfile={FONT_THIN}:text='N E O N    V E I L':fontsize=132:fontcolor=0x9B5CFF:x='(w-tw)/2+({g})':y=(h-th)/2-20:alpha='if(lt(t,0.35),0,if(lt(t,0.9),0.8,0))',"
 f"drawtext=fontfile={FONT_THIN}:text='N E O N    V E I L':fontsize=132:fontcolor=0x22E6FF:x='(w-tw)/2-({g})':y=(h-th)/2-20:alpha='if(lt(t,0.35),0,if(lt(t,0.9),0.7,0))',"
 f"drawtext=fontfile={FONT_THIN}:text='N E O N    V E I L':fontsize=132:fontcolor=white:x=(w-tw)/2:y=(h-th)/2-20:alpha='if(lt(t,0.5),0,if(lt(t,0.9),if(lt(mod(t*24,3),1),0.3,1),1))',"
 "drawbox=x=(iw-min(1240\\,max(0\\,(t-1.0)*1400)))/2:y=ih/2+70:w=min(1240\\,max(0\\,(t-1.0)*1400)):h=2:color=0x9B5CFF@0.95:t=fill:enable='gte(t,1.0)',"
 "noise=alls=6:allf=t,fade=t=out:st=%s:d=1.2" % (TITLE_D - 1.2))
run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", title, "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", t])
TOTAL = TITLE_AT + TITLE_D
open(f"{B}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy", f"{B}/video.mp4"])
S = {CUTS[i][0] + f"#{i}": s for i, s in enumerate(starts)}
print("TOTAL", round(TOTAL, 2), "title at", round(TITLE_AT, 2))
for i, (c, s) in enumerate(zip(CUTS, starts)): print(f"{i:2d} {s:6.2f} {c[0]}")

# ---- audio
st = starts  # index -> start time
SIL0, SIL1 = st[12], st[13]           # black gap = near silence before Act II
VO = [  # file, time, gain dB
 ("g_vo_a1_order.mp3", 0.8, 0), ("g_vo_a2_designed.mp3", st[2] + 0.5, 0), ("g_vo_a3_unpredictable.mp3", st[7] + 0.4, 0),
 ("g_vo_a4_terminate.mp3", st[10] + 0.25, 0), ("g_vo_g1_dead.mp3", st[14] + 0.5, 1), ("g_vo_a5_city.mp3", st[17] + 0.3, 0),
 ("g_vo_g2_heart.mp3", st[21] + 2.2, 1), ("g_vo_a6_understand.mp3", st[24] + 0.4, 0), ("g_vo_g3_neither.mp3", st[25] + 0.8, 1),
 ("g_vo_a7_ghost.mp3", TITLE_AT + 1.6, 0)]
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())
HEART_END = st[21] + 2.2 + dur(f"{T}/g_vo_g2_heart.mp3")
NEITHER_END = st[25] + 0.8 + dur(f"{T}/g_vo_g3_neither.mp3")
inputs = []; filt = []; n = 0
def add(p, pre=None):
    global n; inputs.extend((pre or []) + ["-i", p]); n += 1; return n - 1
A = "aformat=sample_rates=48000:channel_layouts=stereo"
labs = []
for k, (f, tt, g) in enumerate(VO):
    i = add(f"{T}/{f}")
    # AION gets a faint doubled synthetic layer
    fx = "" if "_g" in f else ",asplit=2[x%da][x%db];[x%db]asetrate=48000*0.985,aresample=48000,volume=-14dB[x%dc];[x%da][x%dc]amix=inputs=2:normalize=0" % (k, k, k, k, k, k)
    filt.append(f"[{i}:a]{A},volume={g}dB{fx},adelay={int(tt*1000)}:all=1[v{k}]"); labs.append(f"[v{k}]")
filt.append("".join(labs) + f"amix=inputs={len(labs)}:normalize=0,apad=whole_dur={TOTAL}[vob]")
filt.append("[vob]asplit=2[vo][key]")
# music A: Opener from 12 s, until the betrayal blackout
mA = add(f"{MUS}/Opener_WAV.wav")
lenA = SIL0
filt.append(f"[{mA}:a]{A},atrim=12:{12+lenA},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=3,afade=t=out:st={lenA-0.08}:d=0.08,volume=-5dB[mA]")
# music B: Cauldronized from 68.7 s, starting with the survivor shot (after Left for Dead)
bStart = st[14]; offB = 68.7
lenB = TOTAL - bStart
gate = (f"volume='if(between(t,{HEART_END-bStart:.2f},{HEART_END-bStart+0.55:.2f})+between(t,{st[25]-bStart:.2f},{NEITHER_END-bStart+0.1:.2f}),0,1)':eval=frame")
mB = add(f"{MUS}/Cauldronized_WAV.wav")
filt.append(f"[{mB}:a]{A},atrim={offB}:{offB+lenB},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=2.5,{gate},"
            f"afade=t=out:st={TITLE_AT-bStart+1.5:.2f}:d=3.5,volume=-5dB,adelay={int(bStart*1000)}:all=1[mB]")
filt.append(f"[mA][mB]amix=inputs=2:normalize=0,apad=whole_dur={TOTAL}[mus]")
filt.append("[mus][key]sidechaincompress=threshold=0.03:ratio=5:attack=15:release=350[musd]")
SFX = [  # file, time, gain
 ("sfx_rain.mp3", 0.0, -16), ("g_sfx_hydraulic.mp3", st[2] + 0.3, -3), ("sfx_glitch.mp3", st[9], -3),
 ("g_sfx_failure.mp3", st[10] + 0.6, -2), ("sfx_impact.mp3", st[11], 0), ("sfx_rain.mp3", SIL1, -14),
 ("sfx_impact.mp3", st[15] - 0.05, -3), ("g_sfx_riser.mp3", st[17] - 4.0, -4), ("sfx_impact.mp3", HEART_END + 0.5, 0),
 ("g_sfx_riser.mp3", st[25] - 4.0 + 0.0, -8), ("sfx_impact.mp3", NEITHER_END + 0.15, 1), ("sfx_glitch.mp3", st[27], -6),
 ("sfx_impact.mp3", TITLE_AT, 0), ("sfx_glitch.mp3", TITLE_AT + 0.35, -4)]
sl = []
for k, (f, tt, g) in enumerate(SFX):
    i = add(f"{T}/{f}")
    trim = ",atrim=0:5.5,afade=t=out:st=4.5:d=1" if f == "sfx_rain.mp3" else ""
    if f == "sfx_rain.mp3" and tt > 0: trim = ",atrim=0:8,afade=t=in:st=0:d=0.8,afade=t=out:st=6.5:d=1.5"
    filt.append(f"[{i}:a]{A}{trim},volume={g}dB,adelay={int(max(tt,0)*1000)}:all=1[s{k}]"); sl.append(f"[s{k}]")
filt.append("".join(sl) + f"amix=inputs={len(sl)}:normalize=0[sfx]")
filt.append(f"[vo][musd][sfx]amix=inputs=3:normalize=0,atrim=0:{TOTAL},loudnorm=I=-14:TP=-1.0:LRA=11[aout]")
if True:
    f2=[x for x in filt if not x.startswith("[vo][musd][sfx]")]
    f2.append("[vo]anullsink"); 
    run(["ffmpeg","-v","error","-y"]+inputs+["-filter_complex",";".join(f2[:-1]),"-map","[musd]",f"{B}/stem_music.wav","-map","[sfx]",f"{B}/stem_sfx.wav","-map","[vo]",f"{B}/stem_vo.wav"])
run(["ffmpeg","-v","error","-y","-i",f"{B}/stem_vo.wav","-i",f"{B}/stem_music.wav","-i",f"{B}/stem_sfx.wav","-filter_complex",f"[0][1][2]amix=inputs=3:normalize=0:duration=longest,atrim=0:{TOTAL},loudnorm=I=-14:TP=-1.0:LRA=11[a]","-map","[a]","-ar","48000","-c:a","pcm_s16le",f"{B}/mix.wav"])
run(["ffmpeg", "-v", "error", "-y", "-i", f"{B}/video.mp4", "-i", f"{B}/mix.wav", "-map", "0:v", "-map", "1:a",
     "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "16M", "-bufsize", "32M", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", f"{B}/NeonVeil_Trailer_v1.mp4"])
print("built")
