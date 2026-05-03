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
set SEED_SCHOOL_NAME=Escola Demonstracao

REM ============================
REM Usuarios de demonstracao
REM Senhas em desenvolvimento; troque em producao.
REM CPFs precisam ser validos pelo algoritmo brasileiro.
REM ============================

REM Super Admin (Organizacao)
set SEED_ADMIN_CPF=11144477735
set SEED_ADMIN_NAME=Super Admin
set SEED_ADMIN_EMAIL=admin@neuroflow.local
set SEED_ADMIN_PASSWORD=ChangeMe!123

REM Administrador da Escola
set SEED_SCHOOL_ADMIN_CPF=52998224725
set SEED_SCHOOL_ADMIN_NAME=Diretor Demo
set SEED_SCHOOL_ADMIN_EMAIL=diretor@neuroflow.local
set SEED_SCHOOL_ADMIN_PASSWORD=Demo123!

REM Administrativo (cria usuarios/profissionais/formularios; nao ve atendimentos)
set SEED_ADMINISTRATIVE_CPF=39053344705
set SEED_ADMINISTRATIVE_NAME=Secretaria Demo
set SEED_ADMINISTRATIVE_EMAIL=secretaria@neuroflow.local
set SEED_ADMINISTRATIVE_PASSWORD=Demo123!

REM Profissional Psicologo (realiza atendimentos)
set SEED_PSI_CPF=12345678909
set SEED_PSI_NAME=Maria Psicologa
set SEED_PSI_EMAIL=maria.psi@neuroflow.local
set SEED_PSI_PASSWORD=Demo123!

REM Aluno demo (Maria ja entra na equipe automaticamente)
set SEED_STUDENT_NAME=Lucas Demonstracao

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
>> .env echo SEED_SCHOOL_NAME=%SEED_SCHOOL_NAME%
>> .env echo SEED_ADMIN_CPF=%SEED_ADMIN_CPF%
>> .env echo SEED_ADMIN_NAME=%SEED_ADMIN_NAME%
>> .env echo SEED_ADMIN_EMAIL=%SEED_ADMIN_EMAIL%
>> .env echo SEED_ADMIN_PASSWORD=%SEED_ADMIN_PASSWORD%
>> .env echo SEED_SCHOOL_ADMIN_CPF=%SEED_SCHOOL_ADMIN_CPF%
>> .env echo SEED_SCHOOL_ADMIN_NAME=%SEED_SCHOOL_ADMIN_NAME%
>> .env echo SEED_SCHOOL_ADMIN_EMAIL=%SEED_SCHOOL_ADMIN_EMAIL%
>> .env echo SEED_SCHOOL_ADMIN_PASSWORD=%SEED_SCHOOL_ADMIN_PASSWORD%
>> .env echo SEED_ADMINISTRATIVE_CPF=%SEED_ADMINISTRATIVE_CPF%
>> .env echo SEED_ADMINISTRATIVE_NAME=%SEED_ADMINISTRATIVE_NAME%
>> .env echo SEED_ADMINISTRATIVE_EMAIL=%SEED_ADMINISTRATIVE_EMAIL%
>> .env echo SEED_ADMINISTRATIVE_PASSWORD=%SEED_ADMINISTRATIVE_PASSWORD%
>> .env echo SEED_PSI_CPF=%SEED_PSI_CPF%
>> .env echo SEED_PSI_NAME=%SEED_PSI_NAME%
>> .env echo SEED_PSI_EMAIL=%SEED_PSI_EMAIL%
>> .env echo SEED_PSI_PASSWORD=%SEED_PSI_PASSWORD%
>> .env echo SEED_STUDENT_NAME=%SEED_STUDENT_NAME%

echo [4/5] Validando PostgreSQL e criando database se necessario...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_postgres.ps1 -DbName "%APP_DB_NAME%" -PgSuperUser "%APP_DB_USER%" -PgSuperPassword "%APP_DB_PASSWORD%"
if errorlevel 1 (
    echo Falha ao configurar o PostgreSQL. Verifique as mensagens acima.
    exit /b 1
)

echo [5/5] Inicializando banco e usuarios da aplicacao...
python init_db.py
if errorlevel 1 (
    echo Falha ao inicializar o banco da aplicacao.
    exit /b 1
)

echo.
echo ================================================
echo NeuroFlow rodando em http://localhost:5000
echo ================================================
echo.
echo Usuarios de teste (todos com login por CPF):
echo.
echo   [Super Admin - Organizacao]
echo     CPF:   %SEED_ADMIN_CPF%
echo     Senha: %SEED_ADMIN_PASSWORD%
echo     -> ve "Escolas" e tem vinculo de Admin na Escola Demo
echo.
echo   [Administrador da Escola]
echo     CPF:   %SEED_SCHOOL_ADMIN_CPF%
echo     Senha: %SEED_SCHOOL_ADMIN_PASSWORD%
echo     -> acesso geral dentro da Escola Demo
echo.
echo   [Administrativo]
echo     CPF:   %SEED_ADMINISTRATIVE_CPF%
echo     Senha: %SEED_ADMINISTRATIVE_PASSWORD%
echo     -> cria usuarios/profissionais/formularios. NAO ve atendimentos.
echo.
echo   [Profissional - Psicologo]
echo     CPF:   %SEED_PSI_CPF%
echo     Senha: %SEED_PSI_PASSWORD%
echo     -> realiza atendimentos do aluno %SEED_STUDENT_NAME%
echo.
echo Aluno demo: %SEED_STUDENT_NAME% (Maria ja esta na equipe)
echo.

python serve.py
