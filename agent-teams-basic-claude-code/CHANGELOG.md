# Changelog

## v3 — 2026-10-29

- Integración **opcional** de Context7 mediante referencia `atb-shared/context7.md`, disponible bajo demanda para las ocho skills y agentes.
- Política del coordinador en `CLAUDE.md`: detección de APIs/versiones, documentación actual, privacidad y fallback si Context7 no está disponible.
- Añadido `scripts/setup-context7.ps1` (comprobación por defecto, instalación voluntaria `-Install`, sin duplicar MCP); autenticación OAuth manual.
- El instalador ATB sigue sin tocar Engram, Context7, plugins, hooks o archivos de settings.
- Auditor y tests ampliados para asegurar enlaces Context7, instalaciones seguras y migración de v2.

# CHANGELOG

## v2 — 2026-10-29

- Sustituido `CLAUDE.snippet.md` por **`CLAUDE.md`** como fuente canónica del coordinador; el instalador conserva la integración global o por proyecto en el archivo reconocido por Claude Code.
- Clarificado que el paquete utiliza subagentes (herramienta `Agent`) y **no** Agent Teams nativo.
- Unificados los títulos de las ocho skills `# atb-...` con sus nombres de carpeta y frontmatter.
- Endurecido el instalador: conflictos ahora producen código de salida distinto de cero; actualizaciones conservan backups y el bloque anterior sin duplicarlo.
- Ampliado el validador: frontmatter, identificadores de skills, enlaces Markdown, entrada CLAUDE.md instalada y cambios de versión.
- Auditadas rutas globales/proyecto, modelos, esfuerzos y permisos frente a documentación oficial (ver `docs/CONFIGURATION-AUDIT.md`).
- Se conservan los ocho roles, todas las referencias y la independencia de Engram.

## v1 — 2026-10-29

- Adaptados ocho roles Codex/TOML a subagentes Claude Code/YAML.
- Añadidas ocho skills con precarga, referencias bajo demanda y script de instalación aditiva.
- Conservada compatibilidad con Engram global externo.
