<#
    Verifica se o PostgreSQL esta acessivel e cria o database da aplicacao
    se ele ainda nao existir.

    Localiza o psql.exe primeiro no PATH; se nao achar, tenta as pastas
    padrao de instalacao do PostgreSQL no Windows
    (C:\Program Files\PostgreSQL\<versao>\bin\psql.exe e a equivalente em
    Program Files (x86)). Assim o usuario nao precisa configurar PATH.

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

function Find-Psql {
    # 1) Try PATH
    $cmd = Get-Command psql.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    # 2) Standard install locations (any installed major version, newest first)
    $roots = @(
        "$env:ProgramFiles\PostgreSQL",
        "${env:ProgramFiles(x86)}\PostgreSQL"
    )
    $candidates = @()
    foreach ($root in $roots) {
        if (Test-Path $root) {
            Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
                ForEach-Object {
                    $p = Join-Path $_.FullName "bin\psql.exe"
                    if (Test-Path $p) { $candidates += $p }
                }
        }
    }
    if ($candidates.Count -gt 0) {
        return ($candidates | Sort-Object -Descending)[0]
    }

    return $null
}

$Psql = Find-Psql
if (-not $Psql) {
    Write-Host "ERRO: 'psql.exe' nao encontrado." -ForegroundColor Red
    Write-Host "Locais verificados:" -ForegroundColor Yellow
    Write-Host "  - PATH"
    Write-Host "  - C:\Program Files\PostgreSQL\<versao>\bin\psql.exe"
    Write-Host "  - C:\Program Files (x86)\PostgreSQL\<versao>\bin\psql.exe"
    Write-Host ""
    Write-Host "Instale o PostgreSQL (https://www.postgresql.org/download/windows/)"
    Write-Host "ou ajuste manualmente o caminho dentro de scripts\setup_postgres.ps1."
    exit 1
}

Write-Host "psql encontrado em: $Psql"

$env:PGPASSWORD = $PgSuperPassword

Write-Host "Testando conexao com PostgreSQL em $PgHost`:$PgPort como '$PgSuperUser'..."
$ping = & $Psql -h $PgHost -p $PgPort -U $PgSuperUser -d postgres -t -A -c "SELECT 1" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: nao foi possivel conectar ao PostgreSQL." -ForegroundColor Red
    Write-Host $ping
    Write-Host ""
    Write-Host "Verifique:"
    Write-Host "  - O servico do PostgreSQL esta rodando (services.msc -> postgresql-x64-XX)"
    Write-Host "  - A senha de '$PgSuperUser' esta correta no start.bat (APP_DB_PASSWORD)"
    Write-Host "  - Porta $PgPort esta liberada"
    exit 1
}
Write-Host "Conexao OK."

Write-Host "Verificando se o banco '$DbName' existe..."
$exists = & $Psql -h $PgHost -p $PgPort -U $PgSuperUser -d postgres -t -A `
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
    & $Psql -h $PgHost -p $PgPort -U $PgSuperUser -d postgres `
        -c "CREATE DATABASE `"$DbName`" ENCODING 'UTF8';" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO ao criar o banco." -ForegroundColor Red
        exit 1
    }
    Write-Host "Banco '$DbName' criado."
}

exit 0
