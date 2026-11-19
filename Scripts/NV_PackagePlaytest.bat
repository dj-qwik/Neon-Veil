@echo off
rem Playtest build for outside testers: Win64 Shipping (no console, no cheats, no on-screen debug text),
rem Prologue + Glass Crown (M00 and M01), compressed paks, archived to Saved\Playtest\Windows and zipped to
rem Saved\Playtest\NeonVeil_Playtest_<version>.zip. Full log: Saved\Logs\NV_PackagePlaytest.log
setlocal
set ROOT=%~dp0..
set PROJ=%ROOT%\NeonVeil.uproject
set OUT=%ROOT%\Saved\Playtest
set LOG=%ROOT%\Saved\Logs\NV_PackagePlaytest.log
set ZIP=%OUT%\NeonVeil_Playtest_v0.1.0.zip
if not exist "%ROOT%\Saved\Logs\UAT" mkdir "%ROOT%\Saved\Logs\UAT"
set uebp_LogFolder=%ROOT%\Saved\Logs\UAT
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"
echo [%date% %time%] Playtest package started > "%LOG%"
call "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun -project="%PROJ%" -platform=Win64 -clientconfig=Shipping -build -cook -stage -pak -iostore -compressed -prereqs -nodebuginfo -archive -archivedirectory="%OUT%" -map=/Game/NeonVeil/Maps/M00/L_M00_Prologue+/Game/NeonVeil/Maps/M00/L_M00_GlassCrown -unattended -utf8output >> "%LOG%" 2>&1
set RC=%ERRORLEVEL%
echo [%date% %time%] Package exit code %RC% >> "%LOG%"
if not "%RC%"=="0" goto done
copy /y "%ROOT%\Docs\Playtest_README.txt" "%OUT%\Windows\README.txt" >> "%LOG%" 2>&1
pushd "%OUT%"
tar.exe -a -c -f "%ZIP%" Windows >> "%LOG%" 2>&1
echo [%date% %time%] Zip exit code %ERRORLEVEL% >> "%LOG%"
popd
:done
echo [%date% %time%] DONE >> "%LOG%"
endlocal
