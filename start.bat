@echo off
setlocal
cd /d %~dp0

echo ================================================
echo NeuroFlow - Inicializacao Windows com PostgreSQL
echo ================================================

REM ---------- Configuracao ----------
set APP_DB_NAME=neuroflow
set APP_DB_USER=postgres
set APP_DB_PASSWORD=postgres
set APP_DB_HOST=localhost
set APP_DB_PORT=5432

set FLASK_SECRET_KEY=NEUROFLOW-LOCAL-SECRET-CHANGE-ME

set SEED_ORG_NAME=NeuroFlow Org
set SEED_ORG_CNPJ=00.000.000/0001-00

REM CPF abaixo precisa ser valido (passa pelo validador de CPF brasileiro)
set SEED_ADMIN_CPF=11144477735
set SEED_ADMIN_NAME=Super Admin
set SEED_ADMIN_EMAIL=admin@neuroflow.local
set SEED_ADMIN_PASSWORD=ChangeMe!123

set HOST=0.0.0.0
set PORT=5000

REM ----------------------------------

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py -3
) else (
    set PYTHON_CMD=python
)

if not exist .venv (
    echo [1/6] Criando ambiente virtual...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo Falha ao criar o ambiente virtual.
        exit /b 1
    )
) else (
    echo [1/6] Ambiente virtual ja existe.
)

call .venv\Scripts\activate.bat

echo [2/6] Instalando dependencias Python...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Falha ao instalar dependencias.
    exit /b 1
)

echo [3/6] Gerando/atualizando arquivo .env...
> .env echo FLASK_APP=app:create_app
>> .env echo FLASK_ENV=production
>> .env echo SECRET_KEY=%FLASK_SECRET_KEY%
>> .env echo DATABASE_URL=postgresql+psycopg://%APP_DB_USER%:%APP_DB_PASSWORD%@%APP_DB_HOST%:%APP_DB_PORT%/%APP_DB_NAME%
>> .env echo SEED_ORG_NAME=%SEED_ORG_NAME%
>> .env echo SEED_ORG_CNPJ=%SEED_ORG_CNPJ%
>> .env echo SEED_ADMIN_CPF=%SEED_ADMIN_CPF%
>> .env echo SEED_ADMIN_NAME=%SEED_ADMIN_NAME%
>> .env echo SEED_ADMIN_EMAIL=%SEED_ADMIN_EMAIL%
>> .env echo SEED_ADMIN_PASSWORD=%SEED_ADMIN_PASSWORD%
>> .env echo HOST=%HOST%
>> .env echo PORT=%PORT%

echo [4/6] Validando PostgreSQL e criando database se necessario...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_postgres.ps1 -DbName "%APP_DB_NAME%" -PgHost "%APP_DB_HOST%" -PgPort %APP_DB_PORT% -PgSuperUser "%APP_DB_USER%" -PgSuperPassword "%APP_DB_PASSWORD%"
if errorlevel 1 (
    echo Falha ao configurar o PostgreSQL. Verifique as mensagens acima.
    exit /b 1
)

echo [5/6] Inicializando schema e usuario admin da aplicacao...
python init_db.py
if errorlevel 1 (
    echo Falha ao inicializar o banco da aplicacao.
    exit /b 1
)

echo [6/6] Iniciando NeuroFlow em http://localhost:%PORT% ...
echo.
echo Login inicial:
echo   CPF:   %SEED_ADMIN_CPF%
echo   Senha: %SEED_ADMIN_PASSWORD%
echo.
python serve.py

endlocal
