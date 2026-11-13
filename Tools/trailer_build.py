import subprocess, os
T="/mnt/user-data/uploads/NeonVeil/Saved/Trailer"
VO="/home/claude/neon-veil/RawAssets/VO/M00"
MUS="/mnt/user-data/uploads/NeonVeil/Saved/MusicReview/6_Background_6.wav"
B="/home/claude/trailer/build"
FONT_THIN="/usr/share/fonts/opentype/inter/Inter-Thin.otf"
FONT="/usr/share/fonts/opentype/inter/Inter-Regular.otf"
FONT_MED="/usr/share/fonts/opentype/inter/Inter-Medium.otf"
def run(c): subprocess.run(c, check=True)
# (file, in-point, duration)
shots=[("s01.mp4",0,6.0),("s02.mp4",0.3,7.5),("s03_test.mp4",0.5,7.0),("s04.mp4",0.3,7.5),
       ("s05.mp4",0,4.5),("s06.mp4",0,6.0),("s07v2.mp4",0,6.0),("s08.mp4",0,6.0),("s09.mp4",0,8.0)]
LB="crop=1920:804:0:138,pad=1920:1080:0:138:black"
grade="eq=contrast=1.04:saturation=0.95,noise=alls=6:allf=t"
parts=[]
for i,(f,ss,d) in enumerate(shots):
    o=f"{B}/p{i:02d}.mp4"; parts.append(o)
    vf=f"scale=1920:1080:flags=lanczos,fps=24,{grade},{LB},format=yuv420p"
    if i==0: vf+=",fade=t=in:st=0:d=1.5"
    run(["ffmpeg","-v","error","-y","-ss",str(ss),"-t",str(d),"-i",(f"{T}/{f}" if os.path.exists(f"{T}/{f}") else f"{B}/{f}"),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","16",o])
# title card 7s
t=f"{B}/p99.mp4"; parts.append(t)
title=("color=c=black:s=1920x1080:r=24:d=7,"
 f"drawtext=fontfile={FONT_THIN}:text='N E O N   V E I L':fontsize=120:fontcolor=white:x=(w-tw)/2:y=(h-th)/2-40:alpha='if(lt(t,0.8),0,min(1,(t-0.8)/1.5))',"
 "drawbox=x=(iw-min(1100\\,(t-1.2)*900))/2:y=ih/2+60:w=min(1100\\,max(0\\,(t-1.2)*900)):h=2:color=0x22E6FF@1:t=fill:enable='gte(t,1.2)',"
 f"drawtext=fontfile={FONT}:text='ACT I  ·  THE FALL':fontsize=34:fontcolor=0xBFEFFF:x=(w-tw)/2:y=h/2+95:alpha='if(lt(t,2.6),0,min(1,(t-2.6)/1.0))',"
 "fade=t=out:st=6.2:d=0.8")
run(["ffmpeg","-v","error","-y","-f","lavfi","-i",title,"-c:v","libx264","-preset","veryfast","-crf","16","-pix_fmt","yuv420p",t])
open(f"{B}/list.txt","w").write("".join(f"file '{p}'\n" for p in parts))
run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",f"{B}/list.txt","-c","copy",f"{B}/video_nosubs.mp4"])
# shot start times
starts=[]; acc=0
for _,_,d in shots: starts.append(acc); acc+=d
TITLE=acc; TOTAL=acc+7
print("starts",[round(s,2) for s in starts],"title",TITLE,"total",TOTAL)
# subtitles (speaker, text, start, file, gain_db, fx)
s=starts
vo=[("AION","Welcome back, Ghost-7. Crown Sector is secure. The Directorate is expecting you.",s[1]+0.8,f"{VO}/M00_AION_06.wav",0,None),
    ("CROWN NEWS","Directorate approval holds at 91 percent. Lower-district curfew extended indefinitely.",s[3]+0.4,f"{VO}/M00_CrownNews_01.wav",-2,"highpass=f=300,lowpass=f=4500"),
    ("AION","Baseline reflexes nominal, Ghost-7. Proceed.",s[4]+0.6,f"{VO}/M00_AION_01.wav",0,None),
    ("OPS MONITOR","Gallery feed just dropped. One-eight-zero milliseconds, all cameras.",s[5]+0.2,f"{VO}/M00_OpsMonitor_01.wav",0,None),
    ("AION","Correction. Feed continuity is nominal. No anomaly is recorded.",s[5]+5.3,f"{VO}/M00_AION_08.wav",0,None),
    ("AION","Identity verified. Ghost-Seven. Your authorization has been terminated.",s[7]+0.5,f"{T}/vo_aion_term.mp3",0,None),
    ("SECURITY","Hostile asset detected.",s[8]+0.1,f"{T}/vo_sec_hostile.mp3",0,None)]
def dur(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]).decode())
# --- subtitles burned into the lower letterbox bar
draws=[]
for k,(spk,txt,st,f,g,fx) in enumerate(vo):
    en=st+dur(f)+0.3
    open(f"{B}/sub{k}_s.txt","w").write(spk); open(f"{B}/sub{k}_t.txt","w").write(txt)
    a=f"if(lt(t,{st}+0.15),(t-{st})/0.15,if(gt(t,{en}-0.2),({en}-t)/0.2,1))"
    draws.append(f"drawtext=fontfile={FONT_MED}:textfile={B}/sub{k}_s.txt:fontsize=22:fontcolor=0x22E6FF:x=(w-tw)/2:y=968:enable='between(t,{st},{en})':alpha='{a}'")
    draws.append(f"drawtext=fontfile={FONT}:textfile={B}/sub{k}_t.txt:fontsize=30:fontcolor=white:x=(w-tw)/2:y=1000:enable='between(t,{st},{en})':alpha='{a}'")
open(f"{B}/subs.txt","w").write(",".join(draws))
# --- audio
inputs=[]; filt=[]; n=0
def add(path, extra=None):
    global n
    inputs.extend((extra or [])+["-i",path]); n+=1; return n-1
vo_labels=[]
for k,(spk,txt,st,f,g,fx) in enumerate(vo):
    i=add(f); chain=f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo"
    if fx: chain+=","+fx
    chain+=f",volume={g}dB,adelay={int(st*1000)}:all=1[v{k}]"; filt.append(chain); vo_labels.append(f"[v{k}]")
filt.append("".join(vo_labels)+f"amix=inputs={len(vo_labels)}:normalize=0:duration=longest,apad=whole_dur={TOTAL}[vobus]")
filt.append("[vobus]asplit=2[vo_out][vo_key]")
CUT=s[6]; RET=s[7]
mi=add(MUS)
mi2=add(MUS)
filt.append(f"[{mi}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{CUT},afade=t=in:st=0:d=4,afade=t=out:st={CUT-0.35}:d=0.35,volume=-6dB[mA]")
retlen=TOTAL-RET
filt.append(f"[{mi2}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=89.59:{89.59+retlen},asetpts=PTS-STARTPTS,afade=t=out:st={retlen-4.5}:d=4.5,volume=-4dB,adelay={int(RET*1000)}:all=1[mB]")
filt.append(f"[mA][mB]amix=inputs=2:normalize=0:duration=longest,apad=whole_dur={TOTAL}[mus]")
filt.append("[mus][vo_key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400:makeup=1[musd]")
ri=add(f"{T}/sfx_rain.mp3",["-stream_loop","2"])
filt.append(f"[{ri}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{s[4]},afade=t=in:st=0:d=1.5,afade=t=out:st={s[4]-2}:d=2,volume=-14dB[rainA]")
ri2=add(f"{T}/sfx_rain.mp3")
filt.append(f"[{ri2}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{TITLE-s[8]+2},afade=t=in:st=0:d=0.5,afade=t=out:st={TITLE-s[8]}:d=2,volume=-12dB,adelay={int(s[8]*1000)}:all=1[rainB]")
gi=add(f"{T}/sfx_glitch.mp3")
filt.append(f"[{gi}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=-4dB,adelay={int((s[5]+1.0)*1000)}:all=1[gl]")
ii=add(f"{T}/sfx_impact.mp3")
filt.append(f"[{ii}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0dB,adelay={int(RET*1000)}:all=1[imp]")
ht=add("anoisesrc=color=brown:amplitude=0.05:duration=6.4:sample_rate=48000",["-f","lavfi"])
filt.append(f"[{ht}:a]aformat=sample_rates=48000:channel_layouts=stereo,lowpass=f=180,afade=t=in:st=0:d=0.6,afade=t=out:st=5.8:d=0.3,volume=-6dB,adelay={int(CUT*1000)}:all=1[hum]")
filt.append(f"[vo_out][musd][rainA][rainB][gl][imp][hum]amix=inputs=7:normalize=0:duration=longest,atrim=0:{TOTAL},loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
run(["ffmpeg","-v","error","-y"]+inputs+["-filter_complex",";".join(filt),"-map","[aout]","-ar","48000","-c:a","pcm_s16le",f"{B}/mix.wav"])
run(["ffmpeg","-v","error","-y","-i",f"{B}/video_nosubs.mp4","-i",f"{B}/mix.wav","-filter_complex",f"[0:v]{','.join(draws)}[v]","-map","[v]","-map","1:a",
     "-c:v","libx264","-preset","slow","-crf","17","-pix_fmt","yuv420p","-c:a","aac","-b:a","256k","-movflags","+faststart","-shortest",f"{B}/NeonVeil_Intro_v1.mp4"])
print("built")
