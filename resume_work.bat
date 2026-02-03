@echo off
echo ==================================================
echo      RETOMANDO TRABALHO - PURETEGO CRM
echo ==================================================
echo.
echo 1. Atualizando dependencias (Fix do PDF)...
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo 2. Iniciando o servidor...
echo.
echo    Acesse: http://localhost:5000/proposals
echo.
python run.py
pause
