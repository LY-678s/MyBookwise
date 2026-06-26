# Start Cloudflare named tunnel for the fixed domain.
#
# Usage:
#   scripts\start_tunnel_named.cmd
# or:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_tunnel_named.ps1

$ConfigExample = Join-Path $PSScriptRoot "cloudflared-mybookwise.yml.example"
$Config = Join-Path $PSScriptRoot "cloudflared-mybookwise.yml"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " MyBookwise fixed-domain tunnel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $Config)) {
    Write-Host "Config file was not found:" -ForegroundColor Red
    Write-Host "  $Config" -ForegroundColor White
    Write-Host "Create it from the example file first:" -ForegroundColor Yellow
    Write-Host "  copy `"$ConfigExample`" `"$Config`"" -ForegroundColor White
    Write-Host "Then edit tunnel and credentials-file in the yml file." -ForegroundColor Yellow
    exit 1
}

$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
    Write-Host "cloudflared was not found. Install it first:" -ForegroundColor Red
    Write-Host "  winget install Cloudflare.cloudflared" -ForegroundColor White
    exit 1
}

Write-Host "Using config: $Config" -ForegroundColor DarkGray
Write-Host "Press Ctrl+C to stop the tunnel." -ForegroundColor DarkGray
Write-Host ""

cloudflared tunnel `
    --config $Config `
    --protocol http2 `
    --edge-ip-version 4 `
    --retries 20 `
    run
