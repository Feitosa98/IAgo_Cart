@echo off
echo ===========================================
echo   Iniciando Processo de Empacotamento
echo ===========================================

echo [1/5] Instalando PyInstaller e Dependencias...
pip install pyinstaller pywin32 tk

echo [2/5] Gerando Executavel do Servidor (Aplicacao)...
pyinstaller --noconfirm --onedir --windowed --name "IndicadorRealServer" --add-data "templates;templates" --add-data "static;static" --hidden-import "imoveis_web" --hidden-import "email_service" server_gui.py

echo [3/5] Preparando Payload...
REM Create a clean db template if not exists
python create_clean_db.py
move imoveis.db dist\IndicadorRealServer\clean.db.template

REM Zip the IndicadorRealServer folder to payload.zip
powershell Compress-Archive -Path dist\IndicadorRealServer\* -DestinationPath dist\payload.zip -Force

echo [4/5] Gerando Instalador...
pyinstaller --noconfirm --onefile --windowed --name "Instalador_IndicadorReal" --add-data "dist/payload.zip;." setup_installer.py

echo [5/5] Limpeza e Finalizacao...
echo.
echo Processo Concluido!
echo O instalador esta em: dist\Instalador_IndicadorReal.exe
pause
