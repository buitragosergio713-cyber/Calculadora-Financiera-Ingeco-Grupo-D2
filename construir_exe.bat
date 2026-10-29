@echo off
chcp 65001 >nul
where python >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python. Instalalo desde python.org marcando "Add Python to PATH"
  echo o usa el metodo de GitHub descrito en LEEME.txt ^(no necesita instalar nada^).
  pause
  exit /b 1
)
echo Instalando PyInstaller...
python -m pip install --upgrade pyinstaller
echo.
echo Construyendo la aplicacion portable (puede tardar un minuto)...
python -m PyInstaller --onefile --windowed --name CalculadoraFinanciera app.py
echo.
echo Listo. Tu aplicacion portable esta en: dist\CalculadoraFinanciera.exe
echo Copia ese unico archivo a cualquier computador con Windows y abrelo con doble clic.
pause
