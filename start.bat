@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
python 1-云盘.py > test.log
exit
