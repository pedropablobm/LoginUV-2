param(
  [string]$BinaryPath = ".\dist\windows\loginuv-agent.exe",
  [string]$ConfigPath = ".\config\agent.example.json",
  [string]$InstallDir = "C:\ProgramData\LoginUV"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BinaryPath)) {
  throw "Binary not found: $BinaryPath"
}
if (-not (Test-Path $ConfigPath)) {
  throw "Config not found: $ConfigPath"
}

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Copy-Item $BinaryPath (Join-Path $InstallDir "loginuv-agent.exe") -Force
Copy-Item $ConfigPath (Join-Path $InstallDir "agent.json") -Force

Write-Host "Installed files in $InstallDir"
Write-Host "Run manually for demo: $InstallDir\loginuv-agent.exe"
Write-Host "Note: Windows Service integration is pending in agent code."
