@echo off
rem Runs the packaged M00 benchmark (fullscreen 1920x1080, TSR from 67%%, vsync off); quits by itself.
rem Results: Saved\StagedBuilds\Windows\NeonVeil\Saved\NV_Benchmark.txt and ...\Saved\Profiling\CSV
setlocal
start "" "%~dp0..\Saved\StagedBuilds\Windows\NeonVeil.exe" -fullscreen -ResX=1920 -ResY=1080 -nvbench -csvGpuStats -ExecCmds="stat dumphitches,t.HitchFrameTimeThreshold 250,r.setres 1920x1080f,r.ScreenPercentage 67,r.VSync 0,t.MaxFPS 0"
endlocal
