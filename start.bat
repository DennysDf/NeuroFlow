@echo off
setlocal
cd /d %~dp0

echo ================================================
echo NeuroFlow - Inicializacao Windows com PostgreSQL
echo ================================================

set APP_DB_NAME=neuroflow
set APP_DB_USER=postgres
set APP_DB_PASSWORD=76560$Ms
set FLASK_SECRET_KEY=NEUROFLOW-LOCAL-SECRET

set SEED_ORG_NAME=NeuroFlow Org
set SEED_ORG_CNPJ=00.000.000/0001-00

REM CPF abaixo precisa ser valido (passa pelo validador de CPF brasileiro)
set SEED_ADMIN_CPF=11144477735
set SEED_ADMIN_NAME=Administrador NeuroFlow
set SEED_ADMIN_EMAIL=admin@neuroflow.local
set SEED_ADMIN_PASSWORD=ChangeMe!123

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py -3
) else (
    set PYTHON_CMD=python
)

if not exist .venv (
    echo [1/5] Criando ambiente virtual...
    %PYTHON_CMD% -m venv .venv
)

call .venv\Scripts\activate.bat

echo [2/5] Instalando dependencias Python...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/5] Gerando/atualizando arquivo .env...
> .env echo APP_NAME=NeuroFlow
>> .env echo SECRET_KEY=%FLASK_SECRET_KEY%
>> .env echo DATABASE_URL=postgresql+psycopg://%APP_DB_USER%:%APP_DB_PASSWORD%@localhost:5432/%APP_DB_NAME%
>> .env echo SEED_ORG_NAME=%SEED_ORG_NAME%
>> .env echo SEED_ORG_CNPJ=%SEED_ORG_CNPJ%
>> .env echo SEED_ADMIN_CPF=%SEED_ADMIN_CPF%
>> .env echo SEED_ADMIN_NAME=%SEED_ADMIN_NAME%
>> .env echo SEED_ADMIN_EMAIL=%SEED_ADMIN_EMAIL%
>> .env echo SEED_ADMIN_PASSWORD=%SEED_ADMIN_PASSWORD%

echo [4/5] Validando PostgreSQL e criando database se necessario...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_postgres.ps1 -DbName "%APP_DB_NAME%" -PgSuperUser "%APP_DB_USER%" -PgSuperPassword "%APP_DB_PASSWORD%"
if errorlevel 1 (
    echo Falha ao configurar o PostgreSQL. Verifique as mensagens acima.
    exit /b 1
)

echo [5/5] Inicializando banco e usuario admin da aplicacao...
python init_db.py
if errorlevel 1 (
    echo Falha ao inicializar o banco da aplicacao.
    exit /b 1
)

echo Iniciando NeuroFlow em http://localhost:5000 ...
echo Login inicial: CPF %SEED_ADMIN_CPF% / Senha %SEED_ADMIN_PASSWORD%
python serve.py
