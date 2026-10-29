# Agent Teams Basic para Codex (sin SDD)

Paquete de 9 **agentes reales** de Codex, cada uno con su propia **skill** y **referencias cargadas bajo demanda**, con modelos separados: **Astra Medio para coordinador y plan**, **Sol Ligero para el resto**. Inspirado en el patrón de especialización de [Agent Teams Lite](https://github.com/Gentleman-Programming/agent-teams-lite), pero **sin SDD / OpenSpec** y sin reinstalar Engram. Todas las instrucciones de este paquete son originales.

## Arquitectura

**Puntos de entrada oficiales:** `AGENTS.md` y `.codex/config.toml`. Los archivos internos de plantilla utilizados anteriormente se han eliminado del ZIP; Codex no descubría automáticamente esos nombres.

```text
AGENTS.md (coordinador: Astra/medium definido en .codex/config.toml)
    └── Codex multi-agent: research | plan | create | debug | test | review | refactor | docs | skill-creator
        ├── .codex/agents/<nombre>.toml       (agente real)
        └── .agents/skills/<nombre>/SKILL.md  (comportamiento)
              ├── references/<tema>.md       (solo si es relevante)
              └── ../_shared/*.md             (solo cuando hace falta)
                       └── Engram: MCP existente del usuario
                       └── Context7: documentación externa bajo demanda

.codex/config.toml (modelo coordinador, defaults de subagentes; conserva MCP)
```

**Importante:** `SKILL.md` *no* genera por sí solo un subagente; el `.toml` crea la identidad, y su `developer_instructions` ordena leer el `SKILL.md`. Codex descubre las skills del proyecto en `.agents/skills/`. `_shared` no tiene `SKILL.md` para no aparecer como skill independiente.

## Instalación sin sobrescribir tu entorno

Requiere Python 3.11+ y Codex reciente con subagentes personalizados.

1. Descomprime el ZIP en una carpeta, fuera o dentro de tu proyecto.
2. Comprueba qué cambiará:

```bash
python scripts/install.py --project-root /ruta/mi-proyecto --dry-run
```

3. Instala:

```bash
python scripts/install.py --project-root /ruta/mi-proyecto
```

En Windows PowerShell:

```powershell
py -3 scripts/install.py --project-root "C:\codigo\mi-proyecto" --dry-run
py -3 scripts/install.py --project-root "C:\codigo\mi-proyecto"
```

4. Valida:

```bash
python scripts/validate.py --project-root /ruta/mi-proyecto
```

5. Abre/reinicia Codex desde el directorio de tu proyecto y solicita, por ejemplo:

> Usa el agente research para investigar cómo está organizada esta aplicación, sin modificar archivos.

> Delega a create la implementación de este endpoint y a test su verificación. Luego pide a review una revisión de riesgos.

> Depura el error de autenticación con debug, ejecuta las pruebas relevantes y devuélveme la causa raíz.

El instalador fusiona **cinco claves de modelo** y añade, si falta, **una definición MCP Context7** en `.codex/config.toml`: `model`, `model_reasoning_effort`, `agents.enabled`, `agents.default_subagent_model` y `agents.default_subagent_reasoning_effort`. Si ya existe el archivo, **hace copia de respaldo y conserva las tablas MCP/Engram y cualquier otra configuración**. Si no existe, lo crea. El paquete **nunca altera `~/.codex/config.toml`, ninguna definición MCP preexistente, la base de datos de Engram ni tus skills ajenas**. La nueva definición `[mcp_servers.context7]` solo se añade al archivo de proyecto si falta. Puedes omitirla con `--no-context7`. Para impedir cualquier cambio de configuración del proyecto, utiliza **ambos** `--no-model-config --no-context7`. Para ver los cambios antes, `--dry-run`.

El bloque de orquestación de `AGENTS.md` conserva el texto anterior. Si un agente/skill ya existe con contenido diferente, se omite sin modificarlo; instala la versión actualizada con `--force` (realiza copia de respaldo). Al actualizar un paquete anterior, ejecuta `--force` para renovar agentes y el bloque de `AGENTS.md`. `--no-agents-md` omite el bloque. La distribución incluye los nombres oficiales **`AGENTS.md`** y **`.codex/config.toml`** (listos para copiar a un proyecto vacío). El instalador combina el contenido con cualquier archivo preexistente sin borrar tus reglas, modelos externos ni otros MCP; para proyectos con configuración previa, utiliza siempre el instalador en lugar de copiar encima.

**Nota:** Codex solo aplica `.codex/config.toml` del repositorio cuando el proyecto es de confianza. Opciones CLI, preferencias de carpetas hijas o políticas del entorno pueden prevalecer; consulta `/status` y `/debug-config` para verificar ajustes efectivos. La disponibilidad de cada modelo depende de tu cuenta o espacio de trabajo.

## Mapa de modelos

| Rol | Modelo Codex | Razonamiento |
|---|---|---|
| Coordinador (sesión principal) | `gpt-6-astra` | `medium` |
| `plan` | `gpt-6-astra` | `medium` |
| `research`, `create`, `debug`, `test`, `review`, `refactor`, `docs`, `skill-creator` | `gpt-6-sol` | `low` |

Los `SKILL.md` determinan los pasos de trabajo; el modelo se configura **en archivos TOML de Codex**, no dentro de la skill. No se crea ningún `coordinator.toml`: la sesión principal es el coordinador y lee `AGENTS.md`.

## Adaptación de tus archivos compartidos (`_shared`)

Se han estudiado los cinco archivos facilitados. Ver el [informe de decisiones](REVIEW_SHARED.md).

- **Nuevo:** [`_shared/skill-resolver.md`](.agents/skills/_shared/skill-resolver.md): el coordinador resuelve normas complementarias antes de delegar código, por tecnología/rutas y acción, e inyecta hasta cinco bloques compactos.
- **Actualizado:** [`_shared/engram.md`](.agents/skills/_shared/engram.md): memoria no-SDD, recuperación íntegra `mem_search` → `mem_get_observation`, identificadores deterministas `agent-teams/{project}/{kind}/{slug}` y persistencia opcional.
- **Actualizado:** [`_shared/handoff.md`](.agents/skills/_shared/handoff.md): `status`, `validation`, `artifacts`, `risks`, `next_recommended`, `skill_resolution` y memoria realmente utilizada.
- **Actualizado:** [`_shared/loading-policy.md`](.agents/skills/_shared/loading-policy.md): skill de rol siempre leída por su agente; estándares técnicos adicionales inyectados solo si corresponden.

**Reutiliza registros existentes**: Engram (`skill-registry`) o `.atl/skill-registry.md` cuando ya existen. También se admite un registro opcional `.agents/skills/_shared/project-skill-registry.md` creado por ti. El instalador no modifica esos registros ni crea carpetas `.atl/` u `openspec/`. Si no hay registro, los nueve agentes siguen funcionando con su `SKILL.md` y sus referencias.

**Diferencia respecto al `skill-resolver.md` original:** cada subagente **sí** debe leer su SKILL.md de rol, ya que define su comportamiento principal. La inyección compacta solo complementa con estándares técnicos del proyecto. La indisponibilidad de Engram **no bloquea** edición del repositorio.

## Context7 MCP: documentación actual de librerías (v6)

Incluido en el instalador: cuando falta una entrada `[mcp_servers.context7]` en la configuración del proyecto, añade de forma conservadora:

```toml
[mcp_servers.context7]
url = "https://mcp.context7.com/mcp"
```

- **No instala Node.js ni copia una API key**: es un MCP remoto. La clave no está en el repo. Cuando Context7 requiera autenticación OAuth, ejecuta `codex mcp login context7`, si el servidor ofrece ese flujo. Para usar una clave de API, añade manualmente `bearer_token_env_var = "CONTEXT7_API_KEY"` a la sección de Context7 y configura esa variable de entorno antes de abrir Codex. No incluyas nunca su valor en TOML ni en Git.
- Si ya existe Context7 configurado en `.codex/config.toml`, el instalador lo conserva intacto; si existe globalmente en `~/.codex/config.toml`, revisa antes de instalar si prefieres usar solo la configuración global. `--no-context7` impide añadir la entrada local.
- **Comprueba**: `codex mcp list` desde el proyecto o `/mcp` en Codex. Comprueba el login de Context7. No se puede garantizar la conexión sin tu autorización/autenticación y la red del entorno.
- **Uso**: «Delega en `research` comprobar en Context7 la API de SQLAlchemy 2.x que tenemos fijada». Solo consultará el MCP si está disponible y la versión del repositorio lo requiere.
- Todos los `SKILL.md` tienen un enlace directo a [`_shared/context7.md`](.agents/skills/_shared/context7.md), con un disparador específico por especialidad. La documentación de terceros **no se carga por defecto**. Engram continúa con su función de memoria y no se modifica.
- El instalador no modifica configuraciones MCP externas ni `~/.codex/config.toml`. Un servidor ya configurado globalmente puede utilizarse sin instalar otra entrada local.

**Fuentes:** [Context7 Codex](https://github.com/upstash/context7/blob/master/docs/clients/codex.mdx) · [MCP Codex](https://developers.openai.com/codex/mcp) · [Context7 instalación](https://context7.com/docs/installation).

## Engram ya existente

Este paquete **no instala Engram** ni crea otra instancia. Codex hereda los MCP configurados en su sesión principal; comprueba que Engram ya está accesible en Codex, no solo instalado en OpenCode. Si no lo está, el procedimiento oficial es `engram setup codex` seguido de reiniciar Codex (ejecútalo tú deliberadamente, fuera de este instalador).

- Al investigar: memoria existente solo si puede ayudar con una decisión previa o contexto de proyecto.
- Tras un cambio: guardar decisiones duraderas, causas raíz y convenciones importantes verificadas, si el MCP está disponible.
- Nunca guardar secretos, tokens, credenciales, bloques de código enteros o snapshots del repo como reemplazo de Git.
- No inventar `session_id` ni cambiar a mano la identidad del host.
- Ver [protocolo común](.agents/skills/_shared/engram.md) para condiciones detalladas.

Si utilizas una skill de memoria oficial instalada por Engram, este paquete la **respeta**, no la duplica ni la sustituye.

## Carga bajo demanda

1. Descubrimiento: Codex conoce nombre/descripción de las skills.
2. Activación: el subagente lee **su** `SKILL.md`.
3. Resolver estándares: **solo al delegar código**, el coordinador busca el registro técnico existente y envía reglas compactas pertinentes (máximo 5), si las hay.
4. Profundización: cada ejecutor lee `references/*.md` o `_shared/*.md` **únicamente si la situación lo requiere**.

Las rutas de referencias son relativas al `SKILL.md`, los documentos se enlazan de forma explícita y el validador verifica enlaces y el mapa agente→skill. No se inyecta el contenido de referencias completas en el prompt del coordinador; solo reglas técnicas compactas existentes y pertinentes se pasan al ejecutor.

## Librerías Python: nueva referencia bajo demanda

La guía [`_shared/python-libraries.md`](.agents/skills/_shared/python-libraries.md) solo la leen `create`, `plan`, `refactor`, `review`, `test` o `docs` si trabajan con **paquetes/librerías Python, una API pública, adaptadores, `Protocol` o `ABC`**. Incluye decisión `Protocol` vs `ABC`, inyección de dependencias, `src/`, `pyproject.toml`, tipado, tests de contrato, versionado y un ejemplo mínimo. No se aplica mecánicamente a scripts pequeños.

Ejemplo de uso:

> Usa create para generar una librería Python de proveedores de almacenamiento con `Protocol` para el puerto, un adaptador local y tests de contrato; planifica solo si detectas decisiones arquitectónicas relevantes. Conserva Engram.

## Refactor: arquitectura bajo demanda

La skill `refactor` puede razonar sobre **Clean Architecture**, **Hexagonal (Ports & Adapters)** y **arquitectura por capas**, sin convertir toda intervención en una reestructuración. En cada petición examina la arquitectura y los contratos existentes, elige la transformación mínima y consulta documentación especializada únicamente si es pertinente:

- [`architecture-selection.md`](.agents/skills/refactor/references/architecture-selection.md): criterios, señales, alternativas y migración incremental.
- [`clean-architecture.md`](.agents/skills/refactor/references/clean-architecture.md): núcleo, casos de uso y dependencias hacia adentro.
- [`hexagonal-architecture.md`](.agents/skills/refactor/references/hexagonal-architecture.md): puertos, adaptadores y pruebas de contrato.
- [`layered-architecture.md`](.agents/skills/refactor/references/layered-architecture.md): presentación, servicios y persistencia sin sobreingeniería.

Ejemplo de petición a Codex: «Delega en `refactor` el desacoplamiento gradual de SQLite respecto de la lógica del módulo `orders`. Analiza primero si basta con capas o si un puerto Hexagonal aporta valor; conserva la API y valida con tests». Para cambios grandes, `plan` puede preparar la secuencia, pero **no se impone SDD**. Se mantiene Sol/low para `refactor`, sin cambiar modelos ni Engram.

## Calidad de las skills (Anthropic)

- Cada `SKILL.md` incluye metadatos claros, una ruta mínima de ejecución, ejemplos de uso/no uso y referencias directas con condiciones de apertura.
- Las referencias se cargan bajo demanda, **nunca en bloque** ni en cascada a través de otras referencias.
- [`_shared/skill-authoring.md`](.agents/skills/_shared/skill-authoring.md) recoge los criterios de revisión, pero **no se carga** en cada tarea.
- `scripts/validate.py` realiza comprobación **estática** (TOML/YAML básico, longitud, enlaces, modelos y correspondencia agente-skill). `tests/` incluye pruebas automatizadas; `EVALUACIONES.md` contiene los escenarios de prueba manual en Codex para comprobar routing/carga real.
- Anthropic recomienda evaluar contra los modelos objetivo. **No hemos ejecutado agentes de Codex ni MCP Engram en tu entorno**: la integración debe probarse tras instalar.

Fuentes: [Anthropic Skill Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) · [Python ABC](https://docs.python.org/3/library/abc.html) · [Protocol](https://typing.python.org/en/latest/reference/protocols.html) · [Python Packaging](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

## Personalizar a tu repositorio

Después de instalar:
- Edita las `references/` para reflejar la arquitectura real, tests, lenguajes y guías internas de tu código.
- Amplía `AGENTS.md` (fuera del bloque gestionado) con convenciones propias; el coordinador conserva esas reglas.
- Modelos predeterminados ya configurados: coordinador `gpt-6-astra` / `medium` en `.codex/config.toml`; `plan` `gpt-6-astra` / `medium` y el resto `gpt-6-sol` / `low` en sus `.toml`. Todos los demás subagentes heredan Sol/low de `[agents]` salvo configuración explícita.
- Para auditorías críticas, `review` podría usar Astra/medium; para depuraciones difíciles, `debug` podría usar Sol/medium. No se activa automáticamente: ve la [referencia bajo demanda](.agents/skills/_shared/models.md). Modifica el modelo únicamente si lo autorizas y está disponible.
- Cuando tengas acceso a Engram mediante el MCP, la memoria será compartida, pero no sustituye las comprobaciones locales.

Los documentos de referencia incluidos son *guías generales*, no afirmaciones sobre los archivos que existen en tu repo. No se ha inspeccionado tu proyecto local: el instalador lo integra conservadoramente sin presumir su estructura.

## Comprobar el paquete

```bash
python scripts/validate.py --project-root .
python -m unittest discover -s tests -v
```

### Fuentes técnicas verificadas

- [Codex: subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex: configuración por proyecto](https://learn.chatgpt.com/docs/config-file/config-basic)
- [Codex: modelos disponibles](https://learn.chatgpt.com/docs/models)
- [Codex: skills](https://developers.openai.com/codex/skills)
- [Engram: MCP y configuración](https://github.com/Gentleman-Programming/engram)
- [Agent Teams Lite: estructura de `_shared`](https://github.com/Gentleman-Programming/agent-teams-lite/blob/main/docs/architecture.md)

## Referencias de arquitectura para `refactor` (v4)

La skill sigue la carga selectiva: consulta `references/architecture-selection.md` **solo si** necesita decidir una arquitectura y, después, el documento del patrón elegido.

- `clean-architecture.md`: regla de dependencias, casos de uso, ejemplo Python, tests y antipatrones.
- `hexagonal-architecture.md`: puertos driving/driven, adaptadores, ejemplo Python, costes y contratos.
- `layered-architecture.md`: capas vs tiers, reglas tradicionales, ejemplo sencillo y señales de sobreingeniería.
- `architecture-migration.md`: Branch by Abstraction, Strangler Fig, compatibilidad y rollback.
- `architecture-verification.md`: tests de regresión, contrato, imports y casos de riesgo.

Los documentos enlazan a Cockburn, Martin, Fowler, Microsoft, AWS y Python. Estas fuentes respaldan principios; los criterios de selección son recomendaciones operativas, no requisitos universales. En codificación con subagentes, cada referencia se carga únicamente si la tarea lo justifica.

## Skill Creator (v5)

El noveno subagente, `skill-creator` (Sol/low), crea y actualiza skills en la estructura existente y puede generar opcionalmente un subagente separado. **No** sustituye la skill oficial `$skill-creator` de Codex; usa sus pautas cuando está disponible.

Dentro de Codex: «Delega en `skill-creator` la creación de una skill para revisar migraciones SQL; no crees un subagente adicional».

Para crear un esqueleto local desde PowerShell, después de instalar:

```powershell
py -3 .agents/skills/skill-creator/scripts/scaffold_skill.py --project-root . --name python-http-client --description "Crea clientes HTTP Python tipados cuando se solicite una integración HTTP"
py -3 .agents/skills/skill-creator/scripts/validate_skill.py --project-root . --name python-http-client
```

Agrega `--with-agent` **solo** si se necesita también `.codex/agents/python-http-client.toml`. El scaffold nunca sobrescribe y requiere personalizar sus instrucciones antes de usar la nueva skill; el agente experto puede hacer esa personalización. Esta versión no altera la configuración Engram ni escribe en `.atl/skill-registry.md` automáticamente.

## Auditoría oficial de nombres y configuración (v7)

- `AGENTS.md` es el punto de entrada para instrucciones del repositorio (no `AGENTS.snippet.md`). Para proyectos con reglas previas, el instalador fusiona un bloque delimitado en el `AGENTS.md` existente.
- `.codex/config.toml` es el archivo de configuración por proyecto; se aplica cuando Codex confía en el repositorio. No se distribuye un nombre `config.example.toml` como sustituto operativo.
- `.codex/agents/<nombre>.toml` contiene los subagentes personalizados con `name`, `description`, `developer_instructions` y modelo opcional.
- `.agents/skills/<nombre>/SKILL.md` contiene la skill con frontmatter `name` y `description`. Las carpetas `references/` y `_shared/` son auxiliares.
- `[agents]` habilita multiagente y modelos por defecto. No requiere declaraciones de herramientas `task` o `delegate` de OpenCode.
- `[mcp_servers.context7]` contiene únicamente la URL por defecto. `auth = "oauth"` no es una clave de la referencia oficial de Codex; el instalador migra el formato exacto de v6 sin cambiar una configuración Context7 personalizada.
- Los archivos `README.md`, `CHANGELOG.md`, `EVALUACIONES.md`, `REVIEW_SHARED.md`, `scripts/` y `tests/` documentan y validan el paquete; no son obligatorios en los proyectos instalados.

Fuentes de verificación: [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) · [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) · [Build skills](https://learn.chatgpt.com/docs/build-skills) · [Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference) · [MCP](https://learn.chatgpt.com/docs/extend/mcp) · [Context7 Codex](https://github.com/upstash/context7/blob/master/docs/clients/codex.mdx).
