# 启动 Cloudflare 命名隧道（固定域名 https://mybookwise.xyz）
#
# 用法（推荐）：scripts\start_tunnel_named.cmd
# 或：powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_tunnel_named.ps1
# 前提：另开终端已运行 python manage.py runserver 0.0.0.0:8000

$ConfigExample = Join-Path $PSScriptRoot "cloudflared-mybookwise.yml.example"
$Config = Join-Path $PSScriptRoot "cloudflared-mybookwise.yml"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " MyBookwise 固定域名隧道" -ForegroundColor Cyan
Write-Host " https://mybookwise.xyz" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $Config)) {
    Write-Host "未找到 $Config" -ForegroundColor Red
    Write-Host "请先按 README 完成一次性配置，并复制：" -ForegroundColor Yellow
    Write-Host "  copy `"$ConfigExample`" `"$Config`"" -ForegroundColor White
    Write-Host "然后编辑 yml，填入 tunnel UUID 与 credentials-file 路径。" -ForegroundColor Yellow
    exit 1
}

$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
    Write-Host "未找到 cloudflared。请安装：winget install Cloudflare.cloudflared" -ForegroundColor Red
    exit 1
}

Write-Host "使用配置: $Config" -ForegroundColor DarkGray
Write-Host "按 Ctrl+C 停止隧道。" -ForegroundColor DarkGray
Write-Host ""

cloudflared tunnel --config $Config run
