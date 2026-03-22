# xkcd-mcp — backend 10778 + Vite 10779
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

foreach ($p in 10778, 10779) {
    Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Start-Process -FilePath "uv" -ArgumentList "run", "xkcd-mcp", "--serve" -WorkingDirectory $root -WindowStyle Hidden
Start-Sleep -Seconds 2

Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) {
    npm install
}
Start-Process "http://127.0.0.1:10779/"
npm run dev
