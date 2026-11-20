@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo   Downloading clip for analysis - please wait
echo ============================================
if not exist deno.exe (
  echo Getting deno ...
  curl.exe -L -o deno.zip https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip
  tar.exe -xf deno.zip
  del deno.zip
)
if not exist ffmpeg\bin\ffmpeg.exe (
  echo Getting ffmpeg ...
  curl.exe -L -o ff.zip https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip
  tar.exe -xf ff.zip
  del ff.zip
  for /d %%D in (ffmpeg-master-latest-win64-gpl*) do move "%%D" ffmpeg >nul
)
set /p URL=<url.txt
set "PATH=%~dp0;%PATH%"
yt-dlp.exe -U >nul 2>&1
yt-dlp.exe --js-runtimes deno:"%~dp0deno.exe" --ffmpeg-location "%~dp0ffmpeg\bin" -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 --write-info-json -o "clip\%%(id)s.%%(ext)s" "%URL%" > log.txt 2>&1
yt-dlp.exe --js-runtimes deno:"%~dp0deno.exe" --skip-download --ignore-errors --sleep-subtitles 5 --write-subs --sub-langs "th,en" --sub-format vtt -o "clip\%%(id)s.%%(ext)s" "%URL%" >> log.txt 2>&1
for %%F in (clip\*) do copy /b /y "%%F" "out\%%~nxF" >nul
dir out
echo.
echo DONE - tell Claude: done
