@echo off
rem Builds the NeonVeil editor target and writes the full log to Saved\Logs\NV_Build.log
setlocal
set PROJ=%~dp0..\NeonVeil.uproject
set LOG=%~dp0..\Saved\Logs\NV_Build.log
if not exist "%~dp0..\Saved\Logs" mkdir "%~dp0..\Saved\Logs"
echo [%date% %time%] Build started > "%LOG%"
call "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" NeonVeilEditor Win64 Development -Project="%PROJ%" -WaitMutex -NoHotReloadFromIDE >> "%LOG%" 2>&1
echo [%date% %time%] Build exit code %ERRORLEVEL% >> "%LOG%"
endlocal
