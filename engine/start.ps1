$ErrorActionPreference = 'Continue'
$Engine = $PSScriptRoot
$Host.UI.RawUI.WindowTitle = 'ชุดเรนเดอร์ฉากต่อสู้ไดโนเสาร์'
function RefreshPath { $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') }
function FindPy {
  foreach ($c in @("$env:LOCALAPPDATA\Programs\Python\Python312\python.exe", "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe", "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe")) { if (Test-Path $c) { return $c } }
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { $p = & py -3 -c "import sys; print(sys.executable)" 2>$null; if ($p -and (Test-Path $p)) { return $p } }
  $pc = Get-Command python -ErrorAction SilentlyContinue
  if ($pc -and $pc.Source -notlike '*WindowsApps*') { return $pc.Source }
  return $null
}
$wg = @('--accept-source-agreements','--accept-package-agreements','-e','--silent')
$Py = FindPy
if (-not $Py) {
  Write-Host 'ครั้งแรก: กำลังติดตั้ง Python (รอสักครู่)...' -ForegroundColor Cyan
  winget install --id Python.Python.3.12 @wg; RefreshPath; $Py = FindPy
  if (-not $Py) { Write-Host 'ติดตั้ง Python ไม่สำเร็จ ถ่ายรูปหน้าจอนี้ส่งให้ Claude' -ForegroundColor Red; Read-Host 'กด Enter เพื่อปิด'; exit 1 }
}
$ffmpegOk = (Get-Command ffmpeg -ErrorAction SilentlyContinue) -or (Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter 'Gyan.FFmpeg*' -ErrorAction SilentlyContinue)
if (-not $ffmpegOk) {
  Write-Host 'ครั้งแรก: กำลังติดตั้ง ffmpeg (ตัวทำวิดีโอ)...' -ForegroundColor Cyan
  winget install --id Gyan.FFmpeg @wg; RefreshPath
}
$Mark = Join-Path $Engine '.installed'
if (-not (Test-Path $Mark)) {
  Write-Host 'ครั้งแรก: กำลังติดตั้งไลบรารี (ประมาณ 1-3 นาที)...' -ForegroundColor Cyan
  & $Py -m pip install --upgrade --quiet pip
  & $Py -m pip install --upgrade --quiet pillow numpy scipy soundfile
  & $Py -c "import PIL, numpy, scipy, soundfile"
  if ($LASTEXITCODE -eq 0) { 'ok' | Out-File $Mark } else { Write-Host 'ติดตั้งไลบรารีไม่สำเร็จ ถ่ายรูปหน้าจอนี้ส่งให้ Claude' -ForegroundColor Red; Read-Host 'กด Enter เพื่อปิด'; exit 1 }
}
Set-Location $Engine
$env:PYTHONIOENCODING = 'utf-8'
& $Py server.py
Read-Host 'กด Enter เพื่อปิด'
