@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\HP\OneDrive\ドキュメント\mottora\youtube-agent"
echo [%date% %time%] 処理を開始します >> agent.log
python main.py --channel "UCfapRkagDtoQEkGeyD3uERQ,UCprz7y12WLqOvpEO28eBKVA,UCRxPq02pjQS_ax60gcTSDHQ,UC_kTlZMryHFPMc7QMi4g0VQ,UCZQVTC3uLCyuJUOcRlguazA,UChD63R31attT5w8WOZeuXyg" --count 2 >> agent.log 2>&1
echo [%date% %time%] 処理が完了しました >> agent.log
echo ---------------------------------------- >> agent.log
