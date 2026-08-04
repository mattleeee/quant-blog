@echo off
chcp 65001 >nul 2>&1
setlocal

REM ========== 博客自动发布定时任务 ==========
REM 由Windows任务计划程序调用
REM 流程：生成文章 -> 构建站点 -> 推送GitHub -> 微信通知

set BASE_DIR=C:\Users\liyaming\.local\share\TeleAgent\TeleAgent的工作空间\quant-blog
set PYTHON_EXE=python

REM 设置环境变量优化线程
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
set OMP_NUM_THREADS=1

cd /d "%BASE_DIR%"
if errorlevel 1 (
    echo [%date% %time%] 切换目录失败 >> "%BASE_DIR%\logs\auto_publish_error.log"
    exit /b 1
)

echo [%date% %time%] 开始博客自动发布 >> "%BASE_DIR%\logs\auto_publish_scheduler.log"

REM 运行自动发布脚本
"%PYTHON_EXE%" "%BASE_DIR%\scripts\auto_publish.py" >> "%BASE_DIR%\logs\auto_publish_scheduler.log" 2>&1

set EXIT_CODE=%errorlevel%
echo [%date% %time%] 发布完成，退出码: %EXIT_CODE% >> "%BASE_DIR%\logs\auto_publish_scheduler.log"

exit /b %EXIT_CODE%
