@echo off
rem Runs M00 as a standalone game (no editor) at 1920x1080, TSR upscaling from 67%,
rem vsync off, and records a CSV profile (frame/GPU times) to Saved\Profiling\CSV.
rem Log: Saved\Logs\NV_Standalone.log
setlocal
set PROJ=%~dp0..\NeonVeil.uproject
start "" "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJ%" /Game/NeonVeil/Maps/M00/L_M00_GlassCrown -game -windowed -ResX=1920 -ResY=1080 -log=NV_Standalone.log -csvGpuStats -ExecCmds="r.ScreenPercentage 67,r.VSync 0,t.MaxFPS 0,csvprofile frames=4000"
endlocal
