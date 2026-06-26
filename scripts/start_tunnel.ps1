# Start a temporary Cloudflare tunnel for local testing.
#
# Usage:
#   scripts\start_tunnel.cmd
# or:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_tunnel.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " MyBookwise temporary tunnel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Make sure the backend is already running at:" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:8000" -ForegroundColor White
Write-Host ""
Write-Host "After a https://....trycloudflare.com URL appears:" -ForegroundColor Yellow
Write-Host "  1. Copy that URL." -ForegroundColor White
Write-Host "  2. Use it as the public web/app base URL if needed." -ForegroundColor White
Write-Host "  3. Press Ctrl+C here to stop the tunnel." -ForegroundColor White
Write-Host ""

$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
    Write-Host "cloudflared was not found. Install it first:" -ForegroundColor Red
    Write-Host "  winget install Cloudflare.cloudflared" -ForegroundColor White
    exit 1
}

cloudflared tunnel `
    --url http://localhost:8000 `
    --protocol http2 `
    --edge-ip-version 4 `
    --retries 20
