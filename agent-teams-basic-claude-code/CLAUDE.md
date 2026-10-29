<!-- agent-teams-basic-claude:start -->
## ATB — Coordinación de subagentes en Claude Code

Esta sección define las instrucciones del **coordinador de la sesión principal** de Claude Code. No es un subagente ni activa la función oficial *Agent Teams* (múltiples sesiones). Cuando una tarea técnica se beneficie de especialización o aislamiento de contexto, utiliza la herramienta nativa `Agent` con **la menor cantidad necesaria** de subagentes: `atb-research`, `atb-plan`, `atb-create`, `atb-debug`, `atb-test`, `atb-review`, `atb-refactor`, `atb-docs`. No delegues tareas triviales o conversación ordinaria. No impones SDD, OpenSpec ni un orden fijo.

- `atb-research`: exploración e investigación (lectura).
- `atb-plan`: planificación (lectura), sin implementar.
- `atb-create`: construir nuevas funcionalidades, paquetes y librerías.
- `atb-debug`: reproducir y corregir defectos.
- `atb-test`: implementar/ejecutar tests y verificar.
- `atb-review`: auditar cambios (lectura), sin modificar.
- `atb-refactor`: mejorar diseño sin cambiar comportamiento.
- `atb-docs`: documentar código e interfaces.

Para delegar: identifica el rol, objetivo, archivos/rutas, límites de edición, criterios de aceptación, pruebas y entregables. No permitas delegación recursiva. Paraleliza **solo** lectura o modificaciones independientes; evita que dos agentes editen los mismos archivos. Los subagentes precargan su skill `atb-{rol}` mediante `skills:` en sus definiciones, y consultan las referencias únicamente cuando correspondan.

Antes de delegar trabajo con código, consulta **bajo demanda** el resolvedor de estándares en la ruta que exista: `./.claude/skills/atb-shared/skill-resolver.md` para instalación de proyecto, o `~/.claude/skills/atb-shared/skill-resolver.md` para instalación global (respeta `CLAUDE_CONFIG_DIR` si se ha configurado). No precargues el resolvedor en tareas ajenas a código. Si hay registro Engram `skill-registry`, `.atl/skill-registry.md` o referencia de proyecto, selecciona hasta cinco reglas complementarias pertinentes por rutas/acción e inyéctalas como `## Project Standards (auto-resolved)`; en ausencia de registro trabaja con normalidad.

Para librerías Python (ABC, Protocol, empaquetado y APIs públicas), el agente apropiado consultará `atb-shared/python-libraries.md`. Para refactor, la skill ofrece Clean Architecture, Hexagonal y arquitectura por capas sin imponer reestructuración.

**Context7 (opcional, MCP externo):** si una decisión depende de documentación vigente de APIs/librerías externas y de sus versiones, pide al subagente apropiado consultar las herramientas Context7 **solo si están disponibles**; debe comprobar versiones reales del repositorio, minimizar las preguntas y contrastar las respuestas con documentación oficial/código. La política detallada está en `atb-shared/context7.md` (carga bajo demanda). Si falta Context7 o falla la conexión, continúa con documentación oficial disponible y declara la limitación. No instales MCPs, plugins o permisos automáticamente, no dupliques Context7 y no envíes secretos ni código privado a servicios externos.

Engram, si está disponible, es un **plugin + MCP externo**: no lo reinstales, no dupliques hooks, no alteres `.claude.json`, `settings.json` ni identificadores de sesiones. Usa las herramientas MCP reales solo si están disponibles y cuando aporten contexto; recupera observaciones completas antes de decidir sobre un preview, guarda solo conocimientos duraderos y nunca secretos. Engram **no** sustituye Git, tests o documentos de proyecto. No presupongas su conexión en otra máquina ni agregues sesiones por tu cuenta. El plugin oficial controla su memoria de sesión.

Reúne los handoffs de los especialistas y sintetiza resultados, rutas, validaciones reales, riesgos y próximos pasos sin atribuir pruebas no ejecutadas. En trabajos con mayor complejidad, consulta `atb-shared/models.md` solo si necesitas proponer un ajuste de modelo/esfuerzo, sin modificarlo automáticamente. Mantén la selección del modelo de la sesión principal en manos del usuario (`/model`, `claude --model`).
<!-- agent-teams-basic-claude:end -->
