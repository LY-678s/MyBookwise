# 启动 cloudflared 内网穿透（跨网访问 Django）
#
# 用法（推荐）：scripts\start_tunnel.cmd
# 或：powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_tunnel.ps1
#
# 前提：另开终端已运行  python manage.py runserver 0.0.0.0:8000

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " MyBookwise 跨网穿透（cloudflared）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请确认已在【另一个终端】启动后端：" -ForegroundColor Yellow
Write-Host "  python manage.py runserver 0.0.0.0:8000" -ForegroundColor White
Write-Host ""
Write-Host "下面将启动隧道。出现 https://....trycloudflare.com 后：" -ForegroundColor Yellow
Write-Host "  1. 复制该地址" -ForegroundColor White
Write-Host "  2. 后端终端执行: `$env:TUNNEL_ORIGIN = `"https://你的地址`"" -ForegroundColor White
Write-Host "  3. 重启 runserver（Web 登录需要）" -ForegroundColor White
Write-Host "  4. ApiClient.kt 的 SERVER_BASE 改为同一地址" -ForegroundColor White
Write-Host "  5. Android Studio Rebuild 后装到手机" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 可停止隧道。" -ForegroundColor DarkGray
Write-Host ""

$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
    Write-Host "未找到 cloudflared。请先安装：" -ForegroundColor Red
    Write-Host "  winget install Cloudflare.cloudflared" -ForegroundColor White
    Write-Host "或见 README「跨网访问」章节。" -ForegroundColor White
    exit 1
}

cloudflared tunnel --url http://localhost:8000
