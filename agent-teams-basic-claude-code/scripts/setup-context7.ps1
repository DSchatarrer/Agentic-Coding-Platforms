#Requires -Version 5.1
<#
.SYNOPSIS
  Comprueba Context7 y, SOLO con -Install, instala el plugin oficial global de Claude Code.
.DESCRIPTION
  No modifica directamente .claude.json, settings.json ni Engram.
  La autenticación OAuth requiere reiniciar Claude y ejecutar /mcp interactivo.
.EXAMPLE
  .\scripts\setup-context7.ps1
.EXAMPLE
  .\scripts\setup-context7.ps1 -Install
#>
[CmdletBinding()]
param([switch]$Install)
$ErrorActionPreference = 'Stop'

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    throw 'No se encuentra claude en el PATH. Instala/inicia Claude Code antes de continuar.'
}

$plugins = (& claude plugin list 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw "No se pudo consultar 'claude plugin list': $plugins" }
$mcpList = (& claude mcp list 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0) { throw "No se pudo consultar 'claude mcp list': $mcpList" }

$hasPlugin = $plugins -match 'context7@(?:context7-marketplace|claude-plugins-official)'
$hasMcp = $mcpList -match '(?im)^\s*(?:context7|context7[^:
]*)\s*:'
if ($hasPlugin) {
    Write-Host 'Context7 ya figura como plugin de Claude Code. No se reinstala.'
    Write-Host 'Reinicia Claude Code y usa /mcp para comprobar conexión y autenticación.'
    exit 0
}
if ($hasMcp) {
    Write-Host 'Ya hay un MCP Context7 registrado. No se instala el plugin para evitar duplicaciones.'
    Write-Host 'Comprueba la conexión desde Claude Code con /mcp.'
    exit 0
}
if (-not $Install) {
    Write-Host 'Context7 no aparece en el listado de plugins ni como MCP de usuario.'
    Write-Host 'Para instalar el plugin global: .\scripts\setup-context7.ps1 -Install'
    exit 0
}

Write-Host 'Instalando Context7 desde el marketplace oficial de Upstash...'
& claude plugin marketplace add upstash/context7
if ($LASTEXITCODE -ne 0) {
    # El marketplace puede existir ya; comprobar si hay plugin instalado después.
    Write-Warning 'No se pudo añadir el marketplace; comprueba si ya existe o hay un problema de red.'
}
& claude plugin install context7@context7-marketplace --scope user
if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación del plugin Context7. Revisa los mensajes de claude.' }
Write-Host 'Plugin instalado. Reinicia Claude Code y ejecuta /mcp para completar OAuth.'
