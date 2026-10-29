# ATB — Coordinador de subagentes para Claude Code (v3 + Context7)

Arquitectura de **8 subagentes reutilizables** y 8 skills, con referencias sobre Python (`Protocol`, `ABC`), testing, depuración y refactor incremental (Clean Architecture, Hexagonal y Capas). Engram y Context7 son **externos**: este paquete no los instala automáticamente ni los configura por su cuenta. No impone SDD/OpenSpec.

> **Aclaración oficial:** el nombre histórico «Agent Teams Basic» del ZIP original **no** significa que se active la función *Agent Teams* de Claude Code (varias sesiones coordinadas). Este paquete usa subagentes individuales a través de la herramienta `Agent`. Claude Code es el coordinador de la sesión principal.

## Punto de entrada: `CLAUDE.md`

**`CLAUDE.md` es el archivo de instrucciones real** (no `CLAUDE.snippet.md`). Está en la raíz de este paquete como fuente. Al instalarlo, el script inserta solamente el bloque administrado en la ruta de Claude Code correspondiente:

- Global: `%USERPROFILE%\.claude\CLAUDE.md`, para **todos** tus proyectos.
- Por proyecto: `C:\Ruta\Proyecto\.claude\CLAUDE.md`. También es una ubicación oficial admitida. Puede coexistir con `C:\Ruta\Proyecto\CLAUDE.md`.

El script usa los comentarios `<!-- agent-teams-basic-claude:start -->` y `<!-- agent-teams-basic-claude:end -->` para delimitar la sección, preservando tus instrucciones anteriores. **Conservamos los mismos marcadores que la v1** para actualizar sin duplicaciones. Claude Code elimina esos comentarios HTML al cargar el contexto, pero sí lee el texto dentro del bloque.

### Estructura

```text
agent-teams-basic-claude-code-v3/
├── CLAUDE.md                       # Instrucciones fuente del coordinador (canónicas)
├── .claude/
│   ├── agents/
│   │   ├── atb-research.md
│   │   ├── atb-plan.md
│   │   ├── atb-create.md
│   │   ├── atb-debug.md
│   │   ├── atb-test.md
│   │   ├── atb-review.md
│   │   ├── atb-refactor.md
│   │   └── atb-docs.md
│   └── skills/
│       ├── atb-research/SKILL.md
│       ├── atb-plan/SKILL.md
│       ├── atb-create/SKILL.md
│       ├── atb-debug/SKILL.md
│       ├── atb-test/SKILL.md
│       ├── atb-review/SKILL.md
│       ├── atb-refactor/SKILL.md
│       ├── atb-docs/SKILL.md
│       └── atb-shared/*.md         # Referencias auxiliares (incl. Context7), NO una novena skill
├── scripts/install.py              # Instalador aditivo, dry-run, backups
├── scripts/setup-context7.ps1      # Opt-in: comprobar o instalar plugin Context7 global
├── scripts/validate.py             # Auditor estático: nombres/frontmatter/enlaces/entrada
├── tests/test_package.py
├── docs/CONFIGURATION-AUDIT.md     # Matriz de validación frente a documentación oficial
└── CHANGELOG.md
```

Las skills llevan el mismo nombre que el agente para que `skills: [atb-rol]` pueda precargarlas. El directorio `atb-shared` no tiene `SKILL.md` deliberadamente; contiene referencias consultadas bajo demanda.

## Instalación GLOBAL en Windows (recomendada)

Requisitos: Python 3.10+ y Claude Code. **Usa PowerShell en la carpeta extraída del ZIP.** No lo ejecutes desde `C:\Windows\System32`.

```powershell
# Simular sin modificar archivos
py -3 .\scripts\install.py --scope user --dry-run

# Instalar para cualquier proyecto
py -3 .\scripts\install.py --scope user

# Verificar archivos y que CLAUDE.md incluye el bloque nuevo
py -3 .\scripts\validate.py --scope user

# Pruebas internas del paquete
py -3 -m unittest discover -s tests -v
```

- Se respeta `CLAUDE_CONFIG_DIR` si está definido.
- No se sobrescriben archivos con el mismo nombre y distinto contenido: se informa **CONFLICTO** y el CLI devuelve código **1**.
- Para actualizar desde v1 o v2, revisa primero el `--dry-run`; si indica conflicto, ejecuta `--force` **solo después de revisar lo que se reemplazará**. El instalador respalda cada archivo sustituido y el `CLAUDE.md` previo.
- El instalador **no toca** `.claude.json`, `settings.json`, hooks, Engram MCP, bases de datos, plugins ni otras skills/agentes con nombres diferentes.

### Actualización de v1 o v2 → v3

Si ya instalaste la v1 o `agent-teams-basic-claude-code-v2`, utiliza este procedimiento:

```powershell
py -3 .\scripts\install.py --scope user --dry-run
# Revisa los CONFLICTO: esperados en archivos atb-* y bloque de CLAUDE.md
py -3 .\scripts\install.py --scope user --force
py -3 .\scripts\validate.py --scope user
```

No hace falta desinstalar primero. Los nombres de agente/skill y los marcadores en `CLAUDE.md` se mantienen para que la actualización sea reconocida por el script. **No edites ni borres Engram ni los plugins existentes.**

### Solo un proyecto

```powershell
py -3 .\scripts\install.py --scope project --project-root "C:\Codigo\MiProyecto" --dry-run
py -3 .\scripts\install.py --scope project --project-root "C:\Codigo\MiProyecto"
py -3 .\scripts\validate.py --scope project --project-root "C:\Codigo\MiProyecto"
```

**Importante:** la instalación por proyecto añade un `\.claude\CLAUDE.md`, no sustituye el `CLAUDE.md` de la raíz del repositorio. Claude Code puede cargar ambos y concatenar las instrucciones; resuelve contradicciones a favor de las restricciones de mayor prioridad, manteniendo los límites indicados por el usuario. Si no quieres agregar el bloque de coordinación, utiliza `--no-claude-md` al instalar y también al validar; en ese caso los agentes seguirán disponibles pero **la orquestación no quedará configurada automáticamente**.

## Arranque y comprobaciones en Claude Code

Después de la instalación, **reinicia Claude Code** y entra en cualquier proyecto:

```powershell
cd "C:\Codigo\MiProyecto"
claude
```

Dentro de Claude Code:

```text
/memory    # Comprobar qué CLAUDE.md se ha cargado
/agents    # Consultar subagentes
/skills    # Consultar skills disponibles
/mcp       # Comprobar Engram y Context7, y autenticar Context7
```

Ejemplo de petición:

```text
Usa el subagente atb-research para analizar la estructura del repositorio.
Después, delega a atb-plan las opciones de mejora. No modifiques archivos.
```

Los agentes se identifican por sus frontmatter `name: atb-...`; sus archivos están en `agents/`. Las skills están en `skills/atb-.../SKILL.md` y se pueden invocar mediante `/atb-create`, etc. **Invocar una skill no implica automáticamente lanzar un subagente.**

### Modelos y permisos

| Agente | Modelo | Esfuerzo | Modo |
|---|---|---|---|
| `atb-plan` | `opus` | `medium` | `permissionMode: plan` |
| `atb-research`, `atb-review` | `sonnet` | `low` | `permissionMode: plan` |
| Los cinco agentes de escritura | `sonnet` | `low` | permisos de la sesión |

Los alias de modelo, el esfuerzo y la política de permisos dependen también de tu versión y configuración del host. El modo `plan` no es un sandbox garantizado en todas las configuraciones: si la sesión principal opera en ciertos modos de permisos permisivos, la precedencia descrita por Claude puede modificar ese comportamiento. No utilices prompts como controles de seguridad irrompibles.

El coordinador usa **Context7 solo para documentación externa que dependa de la librería/versión**. Si no está conectado, los agentes continúan con las fuentes disponibles e indican la limitación. Aplica **carga progresiva**: los subagentes precargan su propia skill; abren las referencias detalladas solo cuando la tarea lo requiere. La selección opcional de estándares adicionales del proyecto se explica en `atb-shared/skill-resolver.md`.

## Engram (sin modificaciones)

Tu instalación existente `engram@engram` + `engram` MCP global es independiente. Para comprobarla:

```powershell
claude plugin list
claude mcp list
```

No copies el binario al repositorio y no reinstales Engram. El paquete consulta memoria solo cuando las herramientas están disponibles y es relevante; no presupone herramientas ni sesiones. Ninguna prueba está incluida que requiera una conexión real a Engram.

## Context7 (complemento global opcional, sin duplicar MCP)

Context7 ofrece documentación actualizada de librerías mediante el plugin oficial de Upstash en Claude Code. **La v3 incluye las instrucciones de uso y su política de seguridad, pero el MCP no estará conectado hasta que instales y autentiques el plugin en tu equipo.** Esto preserva la independencia del paquete y no altera tu Engram.

### Paso 1. Comprobar antes de instalar

```powershell
claude plugin list
claude mcp list
# Alternativa que solo comprueba; no escribe configuración
.\scripts\setup-context7.ps1
```

Si Context7 ya aparece instalado como plugin o MCP, **no instales otra copia**. Continúa con la comprobación de conexión.

### Paso 2. Instalación global si aún falta

```powershell
# Opción recomendada: script voluntario que comprueba duplicados
.\scripts\setup-context7.ps1 -Install
```

O bien ejecuta **una sola vez** los comandos oficiales equivalentes en PowerShell:

```powershell
claude plugin marketplace add upstash/context7
claude plugin install context7@context7-marketplace --scope user
```

**No ejecutes ambas vías.** Al terminar, reinicia Claude Code y, **dentro de Claude**, ejecuta `/mcp`, elige Context7 y completa OAuth en el navegador. La vía plugin no requiere Node.js ni una API key local. Si necesitas CI/headless o token explícito consulta la [guía oficial](https://github.com/upstash/context7/blob/master/docs/clients/claude-code.mdx), pero **no añadas un segundo MCP** si ya funciona el plugin.

### Paso 3. Uso de Context7 por los subagentes

- El coordinador delega consultas a `atb-research`, `atb-plan`, `atb-create`, `atb-debug`, `atb-test`, `atb-review`, `atb-refactor` o `atb-docs` **solo cuando una API o versión externa lo requiera**.
- La referencia `.claude/skills/atb-shared/context7.md` explica cuándo usar las herramientas que de verdad estén disponibles, cómo verificar versiones fijadas, qué datos no enviar y cómo trabajar si Context7 falla.
- **Context7** es documentación externa; **Engram** conserva conocimiento del proyecto. No comparten ni reemplazan sus funciones.
- Prueba real: desde un proyecto ejecuta `claude` y solicita: `Usa atb-research para consultar en Context7 la documentación de la versión de FastAPI fijada en este repositorio. No modifiques archivos.` (ajusta la librería a tu proyecto).

Fuentes: [Context7 + Claude Code](https://github.com/upstash/context7/blob/master/docs/clients/claude-code.mdx), [MCP de Context7](https://context7.com/docs/resources/all-clients), [subagentes Claude Code](https://code.claude.com/docs/en/sub-agents).

## Diagnóstico y límites

```powershell
py -3 .\scripts\validate.py --scope user
# Si hay dudas de reconocimiento YAML en la CLI y dispones de una versión reciente:
claude plugin validate "$HOME\.claude\agents"
```

`validate.py` comprueba un **subconjunto limitado de YAML** utilizado por este paquete con la biblioteca estándar; no es un validador YAML general ni sustituye al cargador real de Claude Code. Opcionalmente puedes ejecutar `claude --debug` y revisar las advertencias de frontmatter. En esta entrega se comprueban los archivos y el instalador mediante pruebas locales; **no se ha ejecutado Claude Code en tu Windows**.

Para detalles de la revisión completa y enlaces de referencia, consulta [docs/CONFIGURATION-AUDIT.md](docs/CONFIGURATION-AUDIT.md).
