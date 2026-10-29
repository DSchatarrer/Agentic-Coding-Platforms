#!/usr/bin/env python3
"""Instala Agent Teams Basic sin borrar otros agentes, skills o ajustes MCP/Engram.

Python >= 3.11; solo biblioteca estándar.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import tomllib

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
START = '<!-- agent-teams-basic:start -->'
END = '<!-- agent-teams-basic:end -->'
MODEL_KEYS_ROOT = {'model': 'gpt-6-astra', 'model_reasoning_effort': 'medium'}
MODEL_KEYS_AGENTS = {
    'enabled': True,
    'default_subagent_model': 'gpt-6-sol',
    'default_subagent_reasoning_effort': 'low',
}
TABLE = re.compile(r'^\s*\[{1,2}[^\]\r\n]+\]{1,2}\s*(?:#.*)?$')
KEY = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=')


def _backup(target: Path, dry_run: bool):
    backup = target.with_name(target.name + '.bak.' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    if not dry_run:
        shutil.copy2(target, backup)
    return f'RESPALDO {target} -> {backup}'


def _toml_value(value):
    return 'true' if value is True else 'false' if value is False else f'"{value}"'


def _table_ranges(lines):
    """Extract exact TOML section boundaries without touching unknown entries."""
    indices = [i for i, line in enumerate(lines) if TABLE.match(line.rstrip('\r\n'))]
    root_end = indices[0] if indices else len(lines)
    agents_start = None
    agents_end = None
    for pos, i in enumerate(indices):
        if re.match(r'^\s*\[agents\]\s*(?:#.*)?$', lines[i].rstrip('\r\n')):
            agents_start = i + 1
            agents_end = indices[pos + 1] if pos + 1 < len(indices) else len(lines)
            break
    return root_end, agents_start, agents_end


def _update_section(lines, start, end, desired, newline):
    # Process each key separately and recompute boundaries at caller level.
    original_section = lines[start:end]
    result = list(original_section)
    for key, value in desired.items():
        replacement = _toml_value(value)
        found = None
        for i, line in enumerate(result):
            m = KEY.match(line)
            if m and m.group(1) == key:
                found = i
                break
        if found is None:
            if result and not result[-1].endswith(('\n', '\r')):
                result[-1] += newline
            result.append(f'{key} = {replacement}{newline}')
            continue
        line = result[found].rstrip('\r\n')
        existing = re.match(r'^([ \t]*' + re.escape(key) + r'\s*=\s*)("[^"]*"|\'[^\']*\'|true|false)([ \t]*(?:#.*)?)$', line)
        prefix = existing.group(1) if existing else f'{key} = '
        comment = existing.group(3) if existing else ''
        result[found] = f'{prefix}{replacement}{comment}{newline}'
    return lines[:start] + result + lines[end:]


def merge_model_config(existing: str) -> str:
    """Only change 5 model/agent keys. Preserve MCPs, comments and all other TOML.

    Raise ValueError instead of modifying unsupported or malformed TOML.
    """
    data = tomllib.loads(existing)
    if 'agents' in data and not isinstance(data['agents'], dict):
        raise ValueError('`agents` no es una tabla TOML')
    if re.search(r'(?m)^\s*agents\s*=', existing):
        raise ValueError('`agents` es una tabla inline; no se modifica automáticamente')
    newline = '\r\n' if '\r\n' in existing else '\n'
    lines = existing.splitlines(keepends=True)
    root_end, _, _ = _table_ranges(lines)
    lines = _update_section(lines, 0, root_end, MODEL_KEYS_ROOT, newline)
    _, agents_start, agents_end = _table_ranges(lines)
    if agents_start is None:
        if lines and not lines[-1].endswith(('\n', '\r')):
            lines[-1] += newline
        lines.extend([newline, '[agents]' + newline])
        agents_start, agents_end = len(lines), len(lines)
    lines = _update_section(lines, agents_start, agents_end, MODEL_KEYS_AGENTS, newline)
    new = ''.join(lines)
    parsed = tomllib.loads(new)
    if parsed.get('model') != 'gpt-6-astra' or parsed.get('model_reasoning_effort') != 'medium':
        raise ValueError('El modelo coordinador no se ha configurado')
    agent_settings = parsed.get('agents', {})
    for key, value in MODEL_KEYS_AGENTS.items():
        if agent_settings.get(key) != value:
            raise ValueError(f'El ajuste {key} no se ha configurado')
    return new



CONTEXT7_SECTION = """[mcp_servers.context7]
url = "https://mcp.context7.com/mcp"
"""


def merge_context7_mcp(existing: str) -> tuple[str, bool]:
    """Añade solo Context7 si falta, conservando el resto del TOML original.

    La autenticación se configura luego con OAuth o variable de entorno.
    Devuelve (texto, changed); respeta cualquier conexión personalizada.
    Migra solo una configuración heredada exacta que fue generada por v6.
    """
    data = tomllib.loads(existing)
    servers = data.get('mcp_servers', {})
    if not isinstance(servers, dict):
        raise ValueError('`mcp_servers` no es una tabla TOML')
    if 'context7' in servers:
        ctx = servers['context7']
        if not isinstance(ctx, dict):
            raise ValueError('`mcp_servers.context7` no es una tabla TOML')
        # Corrige únicamente la configuración exacta que produjo nuestra v6.
        # No modifica configuraciones personalizadas, incluso si contienen auth.
        legacy_keys = {'url', 'auth', 'bearer_token_env_var'}
        if (set(ctx) == legacy_keys and
                ctx['url'] == 'https://mcp.context7.com/mcp' and
                ctx['auth'] == 'oauth' and
                ctx['bearer_token_env_var'] == 'CONTEXT7_API_KEY'):
            newline = '\r\n' if '\r\n' in existing else '\n'
            lines = existing.splitlines(keepends=True)
            section_start = None
            section_end = len(lines)
            for i, line in enumerate(lines):
                if line.strip() == '[mcp_servers.context7]':
                    section_start = i
                    continue
                if section_start is not None and i > section_start and TABLE.match(line):
                    section_end = i
                    break
            if section_start is None:
                raise ValueError('Context7 legado no usa una tabla normal: corregir manualmente')
            edited = []
            for i, line in enumerate(lines):
                if section_start < i < section_end and re.match(r'^\s*(?:auth|bearer_token_env_var)\s*=', line):
                    continue
                edited.append(line)
            result = ''.join(edited)
            tomllib.loads(result)
            return result, True
        return existing, False
    newline = '\r\n' if '\r\n' in existing else '\n'
    prefix = existing.rstrip() + (newline * 2 if existing.strip() else '')
    merged = prefix + CONTEXT7_SECTION.replace('\n', newline)
    config = tomllib.loads(merged)
    if config['mcp_servers']['context7']['url'] != 'https://mcp.context7.com/mcp':
        raise ValueError('No se ha podido añadir Context7 MCP')
    return merged, True


def install(project_root: Path, dry_run=False, force=False, include_agents_md=True, include_model_config=True, include_context7=True):
    project_root = Path(project_root).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        raise ValueError(f'El directorio no existe: {project_root}')
    logs = []
    for source_base in (PACKAGE_ROOT / '.codex' / 'agents', PACKAGE_ROOT / '.agents' / 'skills'):
        for src in sorted(source_base.rglob('*')):
            if not src.is_file():
                continue
            dst = project_root / src.relative_to(PACKAGE_ROOT)
            if dst.is_file() and dst.read_bytes() == src.read_bytes():
                logs.append(f'IGUAL {dst}')
                continue
            if dst.exists() and not force:
                logs.append(f'CONFLICTO (se conserva) {dst}; usa --force para actualizar con respaldo')
                continue
            if dst.exists():
                logs.append(_backup(dst, dry_run))
            logs.append(f'ESCRIBIR {dst}')
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    if include_model_config:
        target = project_root / '.codex' / 'config.toml'
        try:
            existing = target.read_text(encoding='utf-8') if target.exists() else ''
            merged = merge_model_config(existing)
        except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
            logs.append(f'CONFLICTO config.toml no modificado: {exc}')
        else:
            if existing == merged:
                logs.append('IGUAL .codex/config.toml (modelos ya aplicados)')
            else:
                if target.exists():
                    logs.append(_backup(target, dry_run))
                logs.append('CONFIGURAR .codex/config.toml: Astra/medium coordinador, Sol/low subagentes por defecto; preservado resto de TOML/MCP')
                if not dry_run:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(merged, encoding='utf-8')

    if include_context7:
        target = project_root / '.codex' / 'config.toml'
        try:
            existing = target.read_text(encoding='utf-8') if target.exists() else ''
            merged, added = merge_context7_mcp(existing)
        except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
            logs.append(f'CONFLICTO Context7 MCP no modificado: {exc}')
        else:
            if not added:
                logs.append('IGUAL Context7 MCP (configuración existente conservada)')
            else:
                if target.exists():
                    logs.append(_backup(target, dry_run))
                logs.append('CONFIGURAR Context7 MCP remoto (alta o migración v6): URL oficial, sin claves incrustadas; Engram intacto')
                if not dry_run:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(merged, encoding='utf-8')

    if include_agents_md:
        target = project_root / 'AGENTS.md'
        snippet = (PACKAGE_ROOT / 'AGENTS.md').read_text(encoding='utf-8').strip()
        existing = target.read_text(encoding='utf-8') if target.exists() else ''
        if START in existing or END in existing:
            if existing.count(START) != 1 or existing.count(END) != 1 or existing.index(START) > existing.index(END):
                logs.append('CONFLICTO marcadores AGENTS.md mal formados; no se modifica.')
            else:
                head, remainder = existing.split(START, 1)
                _, tail = remainder.split(END, 1)
                merged = head + snippet + tail
                if merged == existing:
                    logs.append('IGUAL AGENTS.md (bloque previamente instalado)')
                elif not force:
                    logs.append('CONFLICTO AGENTS.md (bloque existente distinto); usa --force para actualizarlo')
                else:
                    logs.append('ACTUALIZAR bloque gestionado de AGENTS.md')
                    if not dry_run:
                        logs.append(_backup(target, dry_run))
                        target.write_text(merged, encoding='utf-8')
        else:
            joined = (existing.rstrip() + '\n\n' if existing.strip() else '') + snippet + '\n'
            logs.append('AÑADIR bloque a AGENTS.md (conservando contenido original)')
            if not dry_run:
                target.write_text(joined, encoding='utf-8')
    return logs


def main():
    ap = argparse.ArgumentParser(description='Instalador Agent Teams Basic + asignación de modelos por agente')
    ap.add_argument('--project-root', required=True, type=Path, help='Ruta de proyecto destino')
    ap.add_argument('--dry-run', action='store_true', help='Solo mostrar acciones')
    ap.add_argument('--force', action='store_true', help='Actualizar conflictos de agentes/skills con respaldo')
    ap.add_argument('--no-agents-md', action='store_true', help='No insertar bloque de orquestación')
    ap.add_argument('--no-model-config', action='store_true', help='No modificar los modelos del .codex/config.toml')
    ap.add_argument('--no-context7', action='store_true', help='No añadir el MCP Context7 al .codex/config.toml')
    args = ap.parse_args()
    try:
        for log in install(args.project_root, args.dry_run, args.force, not args.no_agents_md, not args.no_model_config, not args.no_context7):
            print(log)
    except (OSError, ValueError) as exc:
        ap.exit(2, str(exc) + '\n')

if __name__ == '__main__':
    main()
