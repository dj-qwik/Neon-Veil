@echo off
rem Packages M00 (Win64 Development: keeps -nvbench and cheats) to Saved\StagedBuilds\Windows (no archive copy: saves ~2.7 GB of disk).
rem Full log: Saved\Logs\NV_Package.log
setlocal
set PROJ=%~dp0..\NeonVeil.uproject
set LOG=%~dp0..\Saved\Logs\NV_Package.log
if not exist "%~dp0..\Saved\Logs" mkdir "%~dp0..\Saved\Logs"
echo [%date% %time%] Package started > "%LOG%"
call "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun -project="%PROJ%" -platform=Win64 -clientconfig=Development -build -cook -stage -pak -iostore -prereqs -map=/Game/NeonVeil/Maps/M00/L_M00_GlassCrown -unattended -utf8output >> "%LOG%" 2>&1
echo [%date% %time%] Package exit code %ERRORLEVEL% >> "%LOG%"
endlocal
