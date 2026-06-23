@echo off
REM 绕过 PowerShell 执行策略限制（无需改系统设置）
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_tunnel.ps1"
