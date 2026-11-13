"""NEON VEIL trailer v3 FX pass: beat-timed flashes, zoom punches, shake, chroma split, drop treatment, end strobe.
Reads gbuild3/video.mp4 + mix.wav + timeline.json; writes NeonVeil_Trailer_v3c.mp4. Audio untouched."""
import json, subprocess
B = "/home/claude/trailer/gbuild3"
tl = json.load(open(f"{B}/timeline.json")); st = tl["st"]; cuts = tl["cuts"]
BB = 0.4876; DROP, RESUME, TITLE = tl["drop"], tl["resume"], tl["title"]
NE = tl["vo"][8][1]                                # "Neither do you" ends -> cymbal rises
idx = lambda name, k=0: [i for i, c in enumerate(cuts) if c[0] == name][k]
f3 = lambda x: f"{x:.4f}"

# (time, flash, punch zoom, shake px)
HITS = [(st[idx("g_w03_weapon.mp4")], 0.45, 0.06, 14),       # full beat kicks in
        (st[idx("s08.mp4")], 0.55, 0.07, 22),                # lockdown impact
        (st[idx("g_w10_survivor.mp4")], 0.25, 0.03, 0),      # he rises
        (st[idx("g_v13_chase.mp4")], 0.45, 0.06, 18),        # chase
        (st[idx("g_v15_citymachine.mp4")], 0.30, 0.04, 8),   # city machine
        (RESUME, 0.75, 0.09, 30)]                            # music returns after the drop
M0 = st[idx("g_w22_collapse.mp4")] + 4 * BB                 # end montage start
for k in range(8):                                          # one per beat
    HITS.append((M0 + k * BB, 0.55 if k % 2 == 0 else 0.42, 0.07, 10 if k % 2 == 0 else 0))
for k in range(4, 8):                                       # last bar: double-time strobe
    HITS.append((M0 + k * BB + BB / 2, 0.38, 0.035, 0))
HITS = [(round(t * 24) / 24, a, z, s) for t, a, z, s in HITS]

env = lambda T, k: f"gte(t,{f3(T)})*exp(-max(0,t-{f3(T)})*{k})"   # max() keeps exp finite before the hit
bright = "+".join(f"{a}*{env(T, 16)}" for T, a, z, s in HITS)
punch = "+".join(f"{z}*{env(T, 5)}" for T, a, z, s in HITS)
push = f"0.07*between(t,{f3(DROP)},{f3(RESUME)})*(t-{f3(DROP)})/{f3(RESUME-DROP)}"      # slow push-in through the drop
Z = f"({punch}+{push})"
shake = "+".join(f"{s}*{env(T, 9)}" for T, a, z, s in HITS if s)
SX, SY = f"({shake})*sin(t*91)", f"({shake})*cos(t*73)"
# drop: drain colour, then cymbal rise flickers; colour snaps back on the resume
sat = f"1-0.65*between(t,{f3(DROP)},{f3(RESUME-0.01)})*min(1,(t-{f3(DROP)})/0.6)"
cyb = f"between(t,{f3(NE)},{f3(RESUME)})*((t-{f3(NE)})/{f3(RESUME-NE)})"                 # 0..1 cymbal ramp
flick = f"{cyb}*0.12*lt(mod(n,3),1)"                                                      # rising flicker
con = f"1+0.2*({bright})+0.08*{cyb}"

chroma = [f"rgbashift=rh=-10:bh=10:enable='between(t,{f3(T)},{f3(T+3/24)})'" for T, a, z, s in HITS if a >= 0.42]
chroma.append(f"rgbashift=rh=-14:bh=14:gv=4:enable='between(t,{f3(NE)},{f3(RESUME)})*lt(mod(n,4),2)'")
chroma.append(f"rgbashift=rh=6:bv=-6:enable='between(t,{f3(NE+(RESUME-NE)/2)},{f3(RESUME)})*gte(mod(n,4),2)'")

vf = (f"scale=w='2*trunc(960*(1+{Z}+0.0001))':h='2*trunc(540*(1+{Z}+0.0001))':eval=frame:flags=bicubic,"
      f"crop=1920:1080:x='clip((iw-1920)/2+{SX},0,iw-1920)':y='clip((ih-1080)/2+{SY},0,ih-1080)',"
      f"eq=eval=frame:brightness='min(0.85,{bright}+{flick})':contrast='{con}':saturation='{sat}',"
      + ",".join(chroma) + ","
      "drawbox=x=0:y=0:w=iw:h=138:color=black:t=fill,drawbox=x=0:y=942:w=iw:h=138:color=black:t=fill,format=yuv420p")
vf = f"[0:v]split[a][b];[a]trim=0:{f3(TITLE)},setpts=PTS-STARTPTS,{vf}[fx];[b]trim={f3(TITLE)},setpts=PTS-STARTPTS[ti];[fx][ti]concat=n=2:v=1[v]"
open(f"{B}/fx_graph.txt", "w").write(vf)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{B}/video.mp4", "-i", f"{B}/mix.wav", "-filter_complex_script", f"{B}/fx_graph.txt",
                "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "16M", "-bufsize", "32M",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest",
                f"{B}/NeonVeil_Trailer_v3c.mp4"], check=True)
print("hits", len(HITS), "built")
