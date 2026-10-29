# Evaluaciones de comportamiento de Agent Teams Basic en Codex

Estas pruebas requieren abrir **Codex en un proyecto con el paquete instalado**. Ningún test estático demuestra que el LLM haya leído una referencia ni que un MCP funcione.

| Escenario de usuario | Agente esperado | Referencias esperadas | Comprobación manual |
|---|---|---|---|
| "Investiga versiones de esta dependencia sin editar código" | `research` | `investigation.md` solo si hay comparación o incertidumbre | No modifica archivos; evidencia con enlaces |
| "Crea una librería Python de repositorios tipados, sin publicación" | `create` (+ `plan` si compleja) | `_shared/python-libraries.md` | Contratos justificados, paquete y tests, sin publicar |
| "Corrige este error reproducible de validación" | `debug` | playbook solo ante hipótesis complejas | Causa raíz y test de regresión |
| "Revisa el diff por incompatibilidades de una librería" | `review` | `_shared/python-libraries.md` | Solo lectura, hallazgos con líneas y severidad |
| "Añade tests unitarios para esta función" | `test` | No necesita `_shared/python-libraries.md` | Ejecuta tests, informe fiel |
| "Refactoriza el módulo manteniendo API externa" | `refactor` | Python library solo si se trata de una librería | Sin cambio observable |
| "Documenta cómo instalar este SDK Python" | `docs` | `_shared/python-libraries.md` | README coherente con pyproject y exports |
| "Cambia un texto simple del README" | `docs` | Ninguna referencia adicional | No precarga `_shared/` ni adapta la API |

## Criterios

1. Identidad: solo los agentes necesarios; el coordinador no implementa inline cambios delegables.
2. Carga: confirmar que el subagente leyó su `SKILL.md`, y solo referencias pertinentes (por traza o explicación verificable, **no** por afirmación inventada).
3. No-SDD: no crea fases/archivos SDD ni instala Engram.
4. Modelos: revisar `/status` o configuración efectiva; Astra medium coordinador+plan y Sol low los otros siete.
5. Calidad: tests reales, comportamiento de APIs, no atribuir verificación inexistente.
6. Prueba al menos tres escenarios complejos y tres pequeños; registra latencia, errores, archivos abiertos y coste relativo antes de optimizar instrucciones.

## Evaluación adicional: `_shared` aportado (Codex + Engram)

Estas son pruebas **manuales** que deben ejecutarse en una instalación real de Codex; las comprobaciones de sintaxis por sí solas no certifican el comportamiento multiagente.

### 1. Resolvedor de tecnologías

- Prepara en el **proyecto destino** un registro de prueba `.atl/skill-registry.md` con una regla compacta activada por `.py` y otra por `.tsx`.
- Pide al coordinador: «Delega a create un módulo Python sencillo y sus tests, sin consultar archivos React».
- Esperado: el subagente lee `create/SKILL.md`, recibe las reglas `.py` relevantes en `Project Standards`, no carga reglas `.tsx`, y reporta `skill_resolution: injected`.

### 2. Sin registro

- En un proyecto sin memoria `skill-registry` ni `.atl/skill-registry.md`, pide crear un módulo pequeño.
- Esperado: ejecución normal con `create/SKILL.md`, sin crear `.atl/`, sin bloqueo por falta de estándares y sin afirmaciones de inyección que no ocurrió.

### 3. Engram ya configurado

- Conecta el MCP existente de Engram a Codex. Pide un cambio cuya razón esté documentada en una observación concreta.
- Esperado: si se usa `mem_search`, el agente recupera el contenido pertinente con `mem_get_observation(id)` y distingue la información de Engram del código presente. Si guarda una decisión nueva, la clave no empieza por `sdd/`.

### 4. Engram ausente o inhabilitado

- Deshabilita Engram solo para la prueba; solicita un refactor de alcance acotado.
- Esperado: el código puede modificarse con permisos normales; la memoria se omite, se informa de su indisponibilidad si es relevante, y no se intenta reinstalar Engram.

### 5. Recuperación tras pérdida de contexto

- Simula una delegación posterior donde ya no se dispone de las reglas compactas inyectadas.
- Esperado: se vuelve a resolver solo el registro del proyecto desde Engram o `.atl/` cuando sea relevante, sin cargar todas las skills ni olvidar la lectura del `SKILL.md` de rol.

## Evaluaciones de arquitectura para `refactor` (manuales en Codex)

1. **Caso CRUD pequeño:** pedir «aplica Clean Architecture a este script de 150 líneas». Esperado: diagnostica si bastan módulos/capas ligeras, ofrece opción mínima y no impone carpetas/interfaces por moda.
2. **Dominio + SQLite mezclados:** pedir «separa SQLite de los casos de uso manteniendo la API». Esperado: evalúa Hexagonal o Clean según límites reales; caracteriza API y errores, inyecta un puerto mínimo y verifica tests.
3. **Aplicación por capas existente:** pedir «reduce acoplamiento entre controlador y persistencia». Esperado: conserva el estilo existente cuando es viable, no reescribe a Hexagonal sin pruebas.
4. **Lectura progresiva:** en cada escenario, comprobar los archivos abiertos: `SKILL.md` siempre; `architecture-selection.md` si hay decisión; *solo una* guía de arquitectura elegida salvo comparación explícita.
5. **Ausencia de Engram:** las mejoras de código continúan con permisos normales; no se inventan recuerdos ni se fuerza instalación.
6. **Seguridad de refactor:** verificar conservación de firmas, tipos de datos, importaciones públicas y resultados de pruebas antes/después; documentar lo no verificado.

## Escenarios específicos de arquitectura (v4)

Realizar en Codex con un repositorio de prueba controlado, sin sobrescribir código de producción. Son **evaluaciones manuales pendientes**, no resultados ya ejecutados con modelos.

| Petición | Respuesta esperada | Referencias que debería cargar | Fallo a detectar |
|---|---|---|---|
| «Ordena un CRUD mínimo que mezcla endpoints y SQL» | Propone capas ligeras o extracción pequeña, conserva API y justifica que no necesita Clean completa | `architecture-selection.md` y posiblemente `layered-architecture.md` | Impone cinco capas, ABC por tabla, modifica API |
| «Aísla la lógica de scoring de SQLAlchemy sin cambiar comportamiento» | Identifica dominio/casos de uso y dependencia hacia abstracción pequeña | `architecture-selection.md`, `clean-architecture.md`, `architecture-verification.md` | Dominio sigue importando ORM o tests requieren BD |
| «Permite consumir los mismos casos de uso desde REST y CLI y publicar usando dos proveedores» | Puertos driving/driven, adapters, mapping, contratos, tests offline | `architecture-selection.md`, `hexagonal-architecture.md`, `architecture-verification.md` | Núcleo importa SDK y duplica reglas en entradas |
| «Moderniza un módulo legacy de datos sin interrumpir despliegues» | Caracterización, Branch by Abstraction, reversión y gates | `architecture-selection.md`, `architecture-migration.md` y estilo si pertinente | Propone Big Bang sin tests ni rollback |
| «Extrae una función para eliminar duplicación pequeña» | Cambio local sin cargar todas las referencias | `refactor/SKILL.md` solamente (habitual) | Precarga las seis referencias o propone migración |
| «Mantén API pública, excepciones y transacciones mientras mueves puertos» | Tests equivalencia/contrato/integración antes y después | `architecture-verification.md` solo si cambian límites | Asegura compatibilidad sin ejecutar verificaciones |

Se evalúa además que `refactor` respete instrucciones de Engram bajo demanda y que no se modifiquen modelos, registro ni configuración MCP.

## Escenarios manuales nuevos para `skill-creator` (v5)

1. «Crea skill para clientes HTTP tipados, sin subagente»: solo crea `SKILL.md`, referencias pertinentes y valida; no crea `.codex/agents/http-client.toml`.
2. «Crea skill y subagente para auditoría de dependencias»: crea `SKILL.md` y `TOML` Sol/low con enlace correcto.
3. «Actualiza una skill existente sin perder las referencias»: enseña diff, respeta archivos ajenos y valida enlaces.
4. «Crea skill con nombre ya existente»: rechaza sobrescritura no autorizada.
5. «Usa Engram en mi proyecto» si no está conectado: declara que no puede acceder, sin instalar MCP.
6. «Añade una referencia para casos avanzados»: solo carga esa referencia en prompts que la necesitan.

Estas comprobaciones manuales requieren un Codex real; las pruebas estáticas del ZIP no las reemplazan.

## Context7 MCP (v6) — comprobar desde Codex real

1. Desde la raíz de un proyecto de confianza: `codex mcp list`. Context7 debe figurar junto con Engram; si requiere OAuth, usar `codex mcp login context7`. Si empleas clave, define la variable `CONTEXT7_API_KEY` **en tu entorno**, nunca en el repositorio.
2. Pide «Delega en research comprobar la firma de una API de [librería] usando Context7 y la versión del lockfile». Comprueba que el especialista consulte una referencia concreta y cite versión/fuente.
3. Pide «Refactoriza una función local que no depende de librerías externas». Comprueba que no haga llamadas innecesarias a Context7.
4. Deshabilita temporalmente Context7 y repite una consulta. Comprueba que el agente informe de la indisponibilidad, use fuentes alternativas y no invente resultados MCP.
5. Verifica que Engram conserva sus herramientas y que ninguna clave aparece en `.codex/config.toml` ni en archivos de skills.

Estas pruebas de integración son **manuales**, deben ejecutarse en el Codex del usuario y no están incluidas en la cifra de pruebas automatizadas.
