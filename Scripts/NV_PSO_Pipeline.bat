@echo off
rem M8: bundled PSO cache. 1) package (cook writes shader stable keys)  2) run the -nvbench tour with -logPSO to
rem record every pipeline the level uses  3) expand recordings + stable keys into Build\Windows\PipelineCaches\*.spc
rem 4) repackage so the cache ships in the build. Log: Saved\Logs\NV_PSO.log  (takes ~10 min, game window runs ~2 min)
setlocal
set ROOT=%~dp0..
set ENG=C:\Program Files\Epic Games\UE_5.8\Engine
set LOG=%ROOT%\Saved\Logs\NV_PSO.log
set STAGE=%ROOT%\Saved\StagedBuilds\Windows
echo [%date% %time%] PSO pipeline started %1 > "%LOG%"
if /i "%1"=="finish" goto build

echo [%time%] 1/4 package (stable keys) >> "%LOG%"
call "%~dp0NV_Package.bat"
type "%ROOT%\Saved\Logs\NV_Package.log" | findstr /C:"Package exit code" >> "%LOG%"

echo [%time%] 2/4 record PSOs >> "%LOG%"
if exist "%STAGE%\NeonVeil\Saved\CollectedPSOs" rmdir /s /q "%STAGE%\NeonVeil\Saved\CollectedPSOs"
start "" /wait "%STAGE%\NeonVeil.exe" -fullscreen -ResX=1920 -ResY=1080 -nvbench -logPSO -ExecCmds="r.setres 1920x1080f,r.ScreenPercentage 67,r.VSync 0"
dir /b "%STAGE%\NeonVeil\Saved\CollectedPSOs" >> "%LOG%" 2>&1


:build
echo [%time%] 3/4 build cache >> "%LOG%"
if exist "%ROOT%\Build\Windows\PipelineCaches\PSO_NeonVeil_PCD3D_SM6.spc" del "%ROOT%\Build\Windows\PipelineCaches\PSO_NeonVeil_PCD3D_SM6.spc"
if not exist "%ROOT%\Build\Windows\PipelineCaches" mkdir "%ROOT%\Build\Windows\PipelineCaches"
"%ENG%\Binaries\Win64\UnrealEditor-Cmd.exe" "%ROOT%\NeonVeil.uproject" -run=ShaderPipelineCacheTools expand "%STAGE%\NeonVeil\Saved\CollectedPSOs\*.rec.upipelinecache" "%ROOT%\Saved\Cooked\Windows\NeonVeil\Metadata\PipelineCaches\*PCD3D_SM6.shk" "%ROOT%\Build\Windows\PipelineCaches\PSO_NeonVeil_PCD3D_SM6.spc" -unattended -nopause >> "%LOG%" 2>&1
echo expand exit code %ERRORLEVEL% >> "%LOG%"
dir "%ROOT%\Build\Windows\PipelineCaches" >> "%LOG%" 2>&1

echo [%time%] 4/4 repackage with cache >> "%LOG%"
call "%~dp0NV_Package.bat"
type "%ROOT%\Saved\Logs\NV_Package.log" | findstr /C:"Package exit code" >> "%LOG%"
echo [%date% %time%] PSO pipeline done >> "%LOG%"
endlocal
