param(
  [string]$OutputDir = "dist/windows"
)

$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
  New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

  $env:GOOS = "windows"
  $env:GOARCH = "amd64"
  $env:CGO_ENABLED = "0"

  go build -trimpath -ldflags "-s -w" -o (Join-Path $OutputDir "loginuv-agent.exe") ./cmd/agent
  Write-Host "Windows build generated at $OutputDir/loginuv-agent.exe"
}
finally {
  Pop-Location
}
