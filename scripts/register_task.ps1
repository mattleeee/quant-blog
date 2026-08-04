# ========== 注册博客自动发布定时任务 ==========
# 每天上午9:00自动生成并发布一篇博客文章
# 运行方式: 以管理员身份运行 PowerShell，执行此脚本

$taskName = "QuantBlogAutoPublish"
$batPath = "C:\Users\liyaming\.local\share\TeleAgent\TeleAgent的工作空间\quant-blog\scripts\run_blog_task.bat"

# 检查bat文件是否存在
if (-not (Test-Path $batPath)) {
    Write-Host "错误: 找不到 $batPath" -ForegroundColor Red
    exit 1
}

# 如果任务已存在，先删除
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "已删除旧任务: $taskName" -ForegroundColor Yellow
}

# 创建任务
$action = New-ScheduledTaskAction -Execute $batPath
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

# 以当前用户运行，不需要登录时也运行
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "每天9:00自动生成并发布一篇量化博客文章"

Write-Host ""
Write-Host "定时任务创建成功！" -ForegroundColor Green
Write-Host "  任务名称: $taskName" -ForegroundColor Cyan
Write-Host "  执行时间: 每天 9:00 AM" -ForegroundColor Cyan
Write-Host "  脚本路径: $batPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "管理命令:" -ForegroundColor Gray
Write-Host "  查看状态: Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host "  手动运行: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host "  删除任务: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray
