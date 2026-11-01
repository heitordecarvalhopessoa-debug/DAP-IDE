@echo off
title Central de Instalacao de Pacotes Python

:MM
cls
powershell -Command "Write-Host '==================================================' -ForegroundColor Cyan"
powershell -Command "Write-Host '      CENTRAL DE INSTALACAO DE REQUISITOS        ' -ForegroundColor Yellow"
powershell -Command "Write-Host '==================================================' -ForegroundColor Cyan"
echo.
powershell -Command "Write-Host '--- PROCESSAMENTO DE IMAGEM E DADOS ---' -ForegroundColor DarkGray"
powershell -Command "Write-Host '  [1] Instalar Pillow (Manipulacao de Imagens)' -ForegroundColor Green"
powershell -Command "Write-Host '  [2] Instalar NumPy (Calculo Numerico)' -ForegroundColor Magenta"
powershell -Command "Write-Host '  [3] Instalar Pandas (Analise de Dados)' -ForegroundColor Yellow"
powershell -Command "Write-Host '  [4] Instalar Matplotlib (Graficos e Visualizacao)' -ForegroundColor Blue"
powershell -Command "Write-Host '  [5] Instalar OpenCV (Visao Computacional)' -ForegroundColor Cyan"
echo.
powershell -Command "Write-Host '--- WEB & MACHINE LEARNING ---' -ForegroundColor DarkGray"
powershell -Command "Write-Host '  [6] Instalar Requests + BeautifulSoup4 (Web Scraping)' -ForegroundColor DarkYellow"
powershell -Command "Write-Host '  [7] Instalar Scikit-Learn (Machine Learning)' -ForegroundColor DarkGreen"
echo.
powershell -Command "Write-Host '--- PACOTES COMPLETOS E FERRAMENTAS ---' -ForegroundColor DarkGray"
powershell -Command "Write-Host '  [8] Instalar Pacote Basico (Pillow + NumPy + Pandas)' -ForegroundColor White"
powershell -Command "Write-Host '  [9] Instalar a partir do requirements.txt' -ForegroundColor DarkMagenta"
powershell -Command "Write-Host ' [10] Atualizar apenas o PIP' -ForegroundColor DarkCyan"
powershell -Command "Write-Host ' [11] Verificar versao do Python e PIP' -ForegroundColor DarkGray"
powershell -Command "Write-Host '  [0] Sair' -ForegroundColor Red"
echo.
powershell -Command "Write-Host '==================================================' -ForegroundColor Cyan"

set /p opcao="Digite o numero da opcao desejada: "

if "%opcao%"=="1" goto inst_pillow
if "%opcao%"=="2" goto inst_numpy
if "%opcao%"=="3" goto inst_pandas
if "%opcao%"=="4" goto inst_matplotlib
if "%opcao%"=="5" goto inst_opencv
if "%opcao%"=="6" goto inst_web
if "%opcao%"=="7" goto inst_sklearn
if "%opcao%"=="8" goto inst_basico
if "%opcao%"=="9" goto inst_req
if "%opcao%"=="10" goto upgrade_pip
if "%opcao%"=="11" goto checar_versao
if "%opcao%"=="0" goto sair

echo.
powershell -Command "Write-Host '[ERRO] Opcao invalida! Tente novamente.' -ForegroundColor Red"
timeout /t 2 >nul
goto MM

:inst_pillow
cls
powershell -Command "Write-Host '[INFO] Instalando Pillow...' -ForegroundColor Green"
python -m pip install --upgrade Pillow
goto fim

:inst_numpy
cls
powershell -Command "Write-Host '[INFO] Instalando NumPy...' -ForegroundColor Magenta"
python -m pip install --upgrade numpy
goto fim

:inst_pandas
cls
powershell -Command "Write-Host '[INFO] Instalando Pandas...' -ForegroundColor Yellow"
python -m pip install --upgrade pandas
goto fim

:inst_matplotlib
cls
powershell -Command "Write-Host '[INFO] Instalando Matplotlib...' -ForegroundColor Blue"
python -m pip install --upgrade matplotlib
goto fim

:inst_opencv
cls
powershell -Command "Write-Host '[INFO] Instalando OpenCV...' -ForegroundColor Cyan"
python -m pip install --upgrade opencv-python
goto fim

:inst_web
cls
powershell -Command "Write-Host '[INFO] Instalando Requests e BeautifulSoup4...' -ForegroundColor DarkYellow"
python -m pip install --upgrade requests beautifulsoup4
goto fim

:inst_sklearn
cls
powershell -Command "Write-Host '[INFO] Instalando Scikit-Learn...' -ForegroundColor DarkGreen"
python -m pip install --upgrade scikit-learn
goto fim

:inst_basico
cls
powershell -Command "Write-Host '[INFO] Instalando Pacote Basico (Pillow, NumPy e Pandas)...' -ForegroundColor White"
python -m pip install --upgrade Pillow numpy pandas
goto fim

:inst_req
cls
if exist requirements.txt (
    powershell -Command "Write-Host '[INFO] Encontrado requirements.txt! Instalando pacotes...' -ForegroundColor DarkMagenta"
    python -m pip install -r requirements.txt
) else (
    powershell -Command "Write-Host '[ERRO] Arquivo requirements.txt nao encontrado na pasta do script!' -ForegroundColor Red"
)
goto fim

:upgrade_pip
cls
powershell -Command "Write-Host '[INFO] Atualizando o PIP...' -ForegroundColor DarkCyan"
python -m pip install --upgrade pip
goto fim

:checar_versao
cls
powershell -Command "Write-Host '[INFO] Informacoes do Ambiente:' -ForegroundColor Yellow"
echo.
python --version
python -m pip --version
goto fim

:fim
echo.
powershell -Command "Write-Host '==================================================' -ForegroundColor Green"
powershell -Command "Write-Host '       OPERACAO CONCLUIDA COM SUCESSO!            ' -ForegroundColor Yellow"
powershell -Command "Write-Host '==================================================' -ForegroundColor Green"
echo.
pause
goto MM

:sair
exit /b