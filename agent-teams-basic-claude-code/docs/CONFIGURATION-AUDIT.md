# Auditoría documental Claude Code — 29 octubre 2026

## Fuentes oficiales consultadas

- [Claude Code: How Claude remembers your project](https://code.claude.com/docs/en/memory) — ubicaciones de `CLAUDE.md`, carga al iniciar la sesión y concatenación de instrucciones.
- [Claude Code: Create custom subagents](https://code.claude.com/docs/en/sub-agents) — ubicación global/proyecto, frontmatter con `name`, `description`, `model`, `effort`, `permissionMode`, `skills`, `disallowedTools`, y límites de delegación.
- [Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/skills) — ruta `SKILL.md`, nombres y metadata de skills, carga de referencias, precarga y llamada manual.
- [Claude Code: Settings files and precedence](https://code.claude.com/docs/en/settings) — rutas globales y de proyecto de settings; no es el archivo de instrucciones del coordinador.
- [Claude Code: Plugins](https://code.claude.com/docs/en/plugins) — plugins y distribución de agentes/skills frente a instalación personal.
- [Engram: Agent Setup](https://github.com/Gentleman-Programming/engram/blob/main/docs/AGENT-SETUP.md) — plugin y MCP de Claude Code, ámbitos, propiedad de la configuración.
- [Engram: Plugins](https://github.com/Gentleman-Programming/engram/blob/main/docs/PLUGINS.md) — ciclo de sesión, hooks y memoria.

## Matriz de archivos / comportamiento real

| Elemento | Fuente del paquete | Destino global | Destino proyecto | Carga real |
|---|---|---|---|---|
| Coordinador | `CLAUDE.md` | `~/.claude/CLAUDE.md` | `.claude/CLAUDE.md` | Se lee al inicio como instrucciones |
| Agente | `.claude/agents/atb-rol.md` | `~/.claude/agents/` | `.claude/agents/` | Descubierto e invocado por nombre |
| Skill | `.claude/skills/atb-rol/SKILL.md` | `~/.claude/skills/` | `.claude/skills/` | Invocada directamente o precargada con `skills:` |
| Referencias | `.claude/skills/atb-shared/*.md` | `~/.claude/skills/atb-shared/` | `.claude/skills/atb-shared/` | Solo se abren bajo demanda, no se autodetectan como skill |
| Engram | **No suministrado** | MCP/plugin preexistentes | Idéntico | A través del plugin/host, si está disponible |
| Context7 | **No suministrado** (solo instrucciones y script opt-in) | Plugin/MCP oficial opcional | Idéntico | Herramientas remotas si plugin está instalado y autenticado |

## Errores de la v1 que corrige v2

1. **Nombre engañoso del punto de entrada:** `CLAUDE.snippet.md` no es una ubicación reconocida por Claude Code. En v1 solo lo consumía el instalador, lo cual era válido técnicamente pero inducía a confusión. v2 distribuye un **`CLAUDE.md` real** y lo integra en la ubicación oficial.
2. **Confusión de «Agent Teams»:** la arquitectura original usa subagentes `Agent`, no *Agent Teams* nativo. Se aclara en el README y en el `CLAUDE.md` de orquestación.
3. **Inconsistencia entre título de skill y nombre:** v1 tenía `name: atb-create` pero título `# create`. v2 utiliza `# atb-create` para los ocho roles.
4. **Validación insuficiente:** v1 no verificaba el bloque real de `CLAUDE.md` ni detectaba frontmatter desconocido; v2 añade estas comprobaciones y los nombres/enlaces de las referencias.
5. **Errores silenciosos de instalación:** v1 finalizaba con código 0 si había archivos en conflicto. v2 devuelve código 1 para indicar instalación incompleta, sin sobrescribirlos.
6. **MCP duplicado y Engram:** la v2 no instala ni modifica servidor MCP, plugin, hooks ni `settings.json`; ya los gestiona el setup oficial de Engram.
7. **Compatibilidad de actualizaciones:** se mantienen los marcadores de CLAUDE.md de la v1; el `--force` sustituye solamente el bloque y los archivos gestionados, con respaldos.

## Nombres comprobados

| Tipo | Convención | Ejemplo | Correcto |
|---|---|---|---|
| Coordinador | `CLAUDE.md` | `~/.claude/CLAUDE.md` | Sí |
| Agente | `atb-<rol>.md` + `name: atb-<rol>` | `atb-refactor.md` | Sí |
| Skill | `atb-<rol>/SKILL.md` + `name: atb-<rol>` | `atb-refactor/SKILL.md` | Sí |
| Referencia | Archivos auxiliares `.md` sin `SKILL.md` | `atb-shared/python-libraries.md` | Sí |
| Hook | No se suministran hooks | Delegado a Engram | Sí |
| Settings | No se suministra `settings.json` | Configuración personal intacta | Sí |

## Comprobaciones y limitaciones

- `scripts/validate.py`: comprueba el frontmatter con un parser del **subconjunto de YAML** que contiene este paquete (solo los campos y listas usados), rutas y nombres, títulos, ocho precargas, referencias locales y el bloque de `CLAUDE.md` instalado.
- `tests/test_package.py`: prueba instalación global, proyecto, `--dry-run`, idempotencia, conflictos, `--force`, backups y migración del bloque de la v1.
- No afirma validación en una instancia Windows de Claude Code ni ejecución de Engram en vivo; confirmar con `/memory`, `/agents`, `/skills`, `/mcp` y prueba real desde un repositorio.

## Ampliación v3: Context7 (29 octubre 2026)

- Documentación oficial: [Context7 para Claude Code](https://github.com/upstash/context7/blob/master/docs/clients/claude-code.mdx), [MCP clients](https://context7.com/docs/resources/all-clients), [Extensiones Claude Code](https://code.claude.com/docs/en/sub-agents).
- **Referencia:** `.claude/skills/atb-shared/context7.md`; no lleva `SKILL.md`, se carga solo por necesidad desde las ocho skills.
- **Coordinador:** `CLAUDE.md` instruye sobre contexto, versiones, disponibilidad, privacidad y fallback; no añade una herramienta de servidor inexistente.
- **Agentes:** los ocho especifican el uso condicional y la prohibición de instalar/reinstalar en ejecución.
- **Instalación:** `scripts/setup-context7.ps1` es opt-in; detecta instalaciones de plugin o MCP conocidas y permite instalar el plugin oficial a nivel user. Se necesita OAuth después de reiniciar Claude Code.
- **Separación:** no se edita `.claude.json`, `.claude/settings.json`, Engram, credenciales, hooks ni plugins durante la instalación ATB; Context7 tiene su ciclo de vida propio.
- **Límite:** no se probó conexión a Context7, OAuth ni ejecución real en Windows. La comprobación estructural no demuestra conectividad.
