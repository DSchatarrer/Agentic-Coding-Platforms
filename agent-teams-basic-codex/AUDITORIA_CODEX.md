# Auditoría de convenciones de Codex — 29 octubre 2026

## Alcance

Revisión del paquete distribuido v6 contra la documentación oficial de Codex CLI y Context7. Se inspeccionaron archivos de entrada, configuración TOML, agentes, skills, referencias, MCP, scripts, README y pruebas. No se ha ejecutado Codex CLI en el equipo del usuario.

## Hallazgos y correcciones

| Elemento | En la v6 | Estado v7 | Documento oficial |
| --- | --- | --- | --- |
| Instrucciones del proyecto | Solo `AGENTS.snippet.md` dentro del ZIP; instalador creaba `AGENTS.md` | `AGENTS.md` real y fuente del instalador | AGENTS.md |
| Config del paquete | `.codex/config.example.toml`; instalador escribía `config.toml` | `.codex/config.toml` real | Configuration Reference |
| Context7 MCP | `auth = "oauth"` (no documentado) | `url` sin esa clave | Codex MCP, Context7 Codex |
| Migrar Context7 v6 | No reparaba v6 | Migra únicamente sección exacta generada por v6, conservando Engram | Configuration Reference |
| Custom agents | `.codex/agents/*.toml` | Conservado: 9 archivos con `name`, `description`, `developer_instructions` y modelo | Subagents |
| Skills | `.agents/skills/*/SKILL.md` | Conservado: 9 skills con frontmatter y referencias | Build skills |
| `_shared` | Archivos Markdown auxiliares | Conservado sin `SKILL.md` (no es otra skill) | Build skills |
| Razonamiento | `model_reasoning_effort` | Conservado: Astra medium coordinador y plan; Sol low ejecutores | Configuration Reference |
| Engram | MCP externo preexistente | Instalador no altera Engram ni configuración global | Codex MCP |
| Registro SDD/OpenSpec | No necesario | No hay fases SDD obligatorias | Diseño de este paquete |

## Precauciones

- `AGENTS.md` funciona sin instalador solo si se copia correctamente a la raíz del proyecto. Si ya existe, **no** reemplazarlo: ejecutar el instalador para conservar instrucciones previas.
- El `config.toml` local solo se aplica donde Codex permite configuración de proyecto confiable. La configuración global y las opciones CLI pueden tener precedencia.
- Context7 puede necesitar autenticación; `codex mcp login context7` depende del flujo que admita el servidor. Alternativamente, agregar manualmente `bearer_token_env_var = "CONTEXT7_API_KEY"` sin guardar la clave real en el repositorio.
- Una config Context7 personalizada no se altera, aunque difiera del ejemplo. El validador estático detecta la clave TOML `auth` no documentada, pero no prueba conexiones de red.
- Modelos sujetos a disponibilidad de cuenta/entorno; la auditoría conserva la selección solicitada. No se ha verificado la disponibilidad del usuario.
- Este paquete no incorpora una prueba de ejecución dentro de Codex CLI; los tests comprueban archivos, instalador, enlaces y Python.

## Fuentes

1. [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
2. [Codex Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
3. [Codex Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)
4. [Codex Build skills](https://learn.chatgpt.com/docs/build-skills)
5. [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp)
6. [Context7 for Codex](https://github.com/upstash/context7/blob/master/docs/clients/codex.mdx)
