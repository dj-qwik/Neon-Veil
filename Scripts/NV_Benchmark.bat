@echo off
rem M8 benchmark: standalone M00, fullscreen 1920x1080, TSR from 67%%, vsync off.
rem Tours every room (-nvbench), writes Saved\NV_Benchmark.txt + a CSV profile, then quits by itself.
setlocal
set PROJ=%~dp0..\NeonVeil.uproject
start "" "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJ%" /Game/NeonVeil/Maps/M00/L_M00_GlassCrown -game -fullscreen -ResX=1920 -ResY=1080 -nvbench -log=NV_Benchmark.log -csvGpuStats -ExecCmds="r.setres 1920x1080f,r.ScreenPercentage 67,r.VSync 0,t.MaxFPS 0"
endlocal
