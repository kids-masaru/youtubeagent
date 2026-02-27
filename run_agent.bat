@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\HP\OneDrive\ドキュメント\mottora\youtube-agent"
echo [%date% %time%] 処理を開始します >> agent.log
python main.py --channel "UCfapRkagDtoQEkGeyD3uERQ" --count 2 >> agent.log 2>&1
echo [%date% %time%] 処理が完了しました >> agent.log
echo ---------------------------------------- >> agent.log
