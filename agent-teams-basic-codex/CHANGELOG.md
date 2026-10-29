## v7 — Auditoría de convenciones oficiales de Codex

- `AGENTS.snippet.md` sustituido por `AGENTS.md` como archivo distribuido y fuente del instalador.
- `.codex/config.example.toml` sustituido por `.codex/config.toml`.
- Eliminada la clave MCP no documentada `auth = "oauth"`; configuración Context7 con URL válida.
- Migración de una sección Context7 v6 exacta, preservando los MCP y configuración personalizada.
- Validador y pruebas de nombres reales, esquema MCP y preservación de Engram.
- Documentación de fuentes oficiales de Codex.

# Changelog

## v6 — Context7 MCP y documentación externa bajo demanda

- Añadida conexión remota oficial `[mcp_servers.context7]` a la configuración de proyecto, solo si no existía.
- Autenticación OAuth o `CONTEXT7_API_KEY` vía variable de entorno; nunca se guarda una clave real.
- Instalador no destructivo: conserva Engram, MCP existentes y los archivos del usuario; opción `--no-context7`.
- Nueva referencia `_shared/context7.md` con consultas por versión, verificaciones, condiciones y límites de seguridad.
- Los nueve especialistas enlazan directamente la referencia bajo demanda.
- Pruebas de instalación, idempotencia, configuración Context7 ya existente y referencias.

## v5 — skill-creator

- Noveno subagente Sol/low `skill-creator`, con skill propia y referencias selectivas de diseño, validación y evaluación.
- Scaffold seguro de nuevas skills con subagente opcional, validador por skill y pruebas de no sobrescritura.
- Coordinador reconoce las skills y agentes futuros sin registro estático obligatorio.
- Conserva Engram y configuración del modelo Astra/medium para coordinador y plan.

## v4 — Referencias de arquitectura basadas en fuentes originales y documentación oficial (2026-10-29)

- Reescritas y ampliadas las cuatro referencias de Clean, Hexagonal, Capas y Selección.
- Fuentes primarias Cockburn, Robert C. Martin, Fowler y guías Microsoft/AWS/Python.
- Incorporadas `architecture-migration.md` y `architecture-verification.md` con enlace directo desde `refactor/SKILL.md`.
- Ejemplos Python ejecutables y verificaciones de dependencias, contrato y migración.
- Mantiene selección contextual, carga bajo demanda, Engram y modelos previos.

# Cambios de la revisión de skills (2026-10-29)

## Revisión de las 8 skills con criterios de Anthropic

- Metadatos `name` y `description`: descripciones precisas de responsabilidades y situaciones de uso; ejemplos de uso y no uso en todas las skills.
- Procedimientos pequeños y referencias directas con condiciones explícitas de lectura; sin precarga de `_shared` ni referencias anidadas.
- Nueva guía compartida especializada para librerías Python, `ABC`, `Protocol`, empaquetado, adaptadores, tipado, tests de contrato y API estable.
- Nueva guía de mantenimiento de skills: `.agents/skills/_shared/skill-authoring.md` (no se precarga).
- Plan manual de evaluación en `EVALUACIONES.md` para comprobar en Codex el enrutamiento, la carga bajo demanda y el uso de Engram.
- Validador reforzado para metadatos, tamaño de SKILL.md, enlaces, nombres y modelos.
- Pruebas automatizadas ampliadas de 5 a 10: nuevas comprobaciones de metadatos, referencias y ejemplos Python ejecutables.

## Se conserva

- 8 subagentes sin SDD: research, plan, create, debug, test, review, refactor, docs.
- Modelos: coordinador y plan `gpt-6-astra`/medium; demás `gpt-6-sol`/low.
- Engram como MCP existente opcional, sin instalación ni reconfiguración automática.
- Instalación conservadora e idempotente; backup y bandera `--force` para actualizar conflictos de archivos.

## Fuentes

- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- https://docs.python.org/3/library/abc.html
- https://typing.python.org/en/latest/reference/protocols.html
- https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
- https://developers.openai.com/codex/subagents

## 2026-10-29 — Integración de `_shared` aportado

- Nuevo resolvedor de estándares técnicos complementarios, con prioridad de registro en Engram o `.atl/skill-registry.md` y límite de 5 bloques inyectados.
- Engram no-SDD con búsqueda→recuperación íntegra, claves deterministas y persistencia de memoria separada de permisos de edición de código.
- Handoff y modelos de rol mejorados con `skill_resolution` y protocolos de fallback por compaction.
- Informe `REVIEW_SHARED.md` que explica lo aprovechado y lo excluido de los cinco documentos originales.
- Se mantienen los 8 agentes, los modelos asignados y la referencia Python `ABC`/`Protocol`.

## 2026-10-29 — Referencias de arquitectura para refactor (v3)

- `refactor/SKILL.md`: diagnóstico previo, preservación de contratos, selección proporcional y migración incremental.
- Referencias directas bajo demanda: selección arquitectónica, Clean Architecture, Hexagonal y por capas.
- Ejemplos Python breves, antipatrones, pruebas y fuentes primarias.
- Sin SDD, sin nuevas dependencias ni cambios de modelo o integración Engram.
- Cuatro pruebas automatizadas adicionales y escenarios manuales de comportamiento.

Fuentes: https://www.informit.com/articles/article.aspx?p=2832399 · https://alistair.cockburn.us/hexagonal-architecture/ · https://learn.microsoft.com/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures · https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
