<#
    Verifica se o PostgreSQL esta acessivel e cria o database da aplicacao
    se ele ainda nao existir. Usa psql via env PGPASSWORD.

    Uso:
        powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_postgres.ps1 `
            -DbName "neuroflow" -PgSuperUser "postgres" -PgSuperPassword "senha"
#>

param(
    [Parameter(Mandatory = $true)]  [string]$DbName,
    [Parameter(Mandatory = $false)] [string]$PgHost = "localhost",
    [Parameter(Mandatory = $false)] [int]$PgPort = 5432,
    [Parameter(Mandatory = $true)]  [string]$PgSuperUser,
    [Parameter(Mandatory = $true)]  [string]$PgSuperPassword
)

$ErrorActionPreference = "Stop"

function Test-Command($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    return [bool]$cmd
}

if (-not (Test-Command "psql")) {
    Write-Host "ERRO: 'psql' nao encontrado no PATH." -ForegroundColor Red
    Write-Host "Instale o PostgreSQL e adicione a pasta 'bin' (ex.: C:\Program Files\PostgreSQL\16\bin) ao PATH."
    exit 1
}

$env:PGPASSWORD = $PgSuperPassword

Write-Host "Testando conexao com PostgreSQL em $PgHost`:$PgPort como '$PgSuperUser'..."
$ping = & psql -h $PgHost -p $PgPort -U $PgSuperUser -d postgres -t -A -c "SELECT 1" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: nao foi possivel conectar ao PostgreSQL." -ForegroundColor Red
    Write-Host $ping
    exit 1
}
Write-Host "Conexao OK."

Write-Host "Verificando se o banco '$DbName' existe..."
$exists = & psql -h $PgHost -p $PgPort -U $PgSuperUser -d postgres -t -A `
    -c "SELECT 1 FROM pg_database WHERE datname = '$DbName';" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao consultar pg_database:" -ForegroundColor Red
    Write-Host $exists
    exit 1
}

if ($exists.Trim() -eq "1") {
    Write-Host "Banco '$DbName' ja existe."
} else {
    Write-Host "Banco '$DbName' nao existe. Criando..."
    & psql -h $PgHost -p $PgPort -U $PgSuperUser -d postgres `
        -c "CREATE DATABASE `"$DbName`" ENCODING 'UTF8';" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO ao criar o banco." -ForegroundColor Red
        exit 1
    }
    Write-Host "Banco '$DbName' criado."
}

exit 0
