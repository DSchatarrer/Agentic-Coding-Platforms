# Revisión de los cinco ficheros `_shared` aportados por el usuario

Objetivo: adaptar patrones útiles de Agent Teams Lite a **ocho subagentes reales de Codex con skills ligeras, referencias bajo demanda y Engram existente**, sin activar SDD/OpenSpec.

| Fuente aportada | Decisión | Ubicación / transformación |
|---|---|---|
| `skill-resolver.md` | Adaptado | `_shared/skill-resolver.md`. Registro opcional (`Engram`, `.atl/skill-registry.md`, registro del proyecto), coincidencia por tecnología + acción, máximo 5 bloques, inyección de reglas compactas. **Diferencia deliberada:** el ejecutor sí lee su SKILL.md de rol; solo las skills técnicas adicionales pueden llegar compactadas. |
| `engram-convention.md` | Adaptado | `_shared/engram.md`. Dos pasos buscar→recuperar íntegramente, namespacing no-SDD `agent-teams/{project}/{kind}/{slug}`, upserts solo si herramientas compatibles, no IDs inventados. |
| `persistence-contract.md` | Reutilizado parcialmente | `_shared/engram.md`. Persistencia de memoria en `auto|off`, distinta de permisos/guardado de código. Se descartan modos `openspec/hybrid` que corresponden a artefactos SDD. |
| `sdd-phase-common.md` | Extraídas prácticas transversales | `_shared/handoff.md`, `.codex/agents/*.toml`. Límite ejecutor/coordinador, resultados estructurados, recuperación completa. No se copian fases, DAG ni artefactos SDD. |
| `openspec-convention.md` | No incorporado | Su árbol `openspec/changes`, delta specs y archivado solo aplican a SDD. No se crearán. |

## Decisiones importantes

- El `skill-resolver` original decía «los subagentes no deben leer SKILL.md». Eso es válido en su arquitectura de inyección completa, **no en esta**, donde cada agente especializado obtiene su comportamiento principal del SKILL.md correspondiente.
- El `persistence-contract` original asociaba `none` con «no editar archivos». Eso aplica a artefactos documentales SDD, pero **bloquearía incorrectamente** `create`, `debug`, `test`, `refactor` y `docs`; aquí la ausencia de Engram **no limita** operaciones autorizadas sobre código.
- Un registro de skills técnicas es una capacidad **opcional**. Si ya mantienes `.atl/skill-registry.md` o memorias `skill-registry` en Engram, el coordinador puede reutilizarlos. El instalador no los sobrescribe ni genera registros específicos de una tecnología que no conoce.
- Los archivos proporcionados son documentación de referencia, no una configuración de Engram ejecutable. Solo tu instalación real puede confirmar el contrato de herramientas MCP.
