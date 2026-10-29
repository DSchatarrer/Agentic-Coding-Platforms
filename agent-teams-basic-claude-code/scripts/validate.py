#!/usr/bin/env python3
"""Validación estática estricta ATB para Claude Code. Solo biblioteca estándar.

Valida el subconjunto de YAML que utiliza el paquete. No pretende analizar YAML general.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ('research', 'plan', 'create', 'debug', 'test', 'review', 'refactor', 'docs')
SHARED = ('engram', 'context7', 'skill-resolver', 'python-libraries', 'handoff',
          'loading-policy', 'models', 'safety', 'skill-authoring')
START = '<!-- agent-teams-basic-claude:start -->'
END = '<!-- agent-teams-basic-claude:end -->'
REF_RE = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
ALLOWED_AGENT_FIELDS = {'name', 'description', 'model', 'effort', 'color',
                        'skills', 'permissionMode', 'disallowedTools'}
ALLOWED_SKILL_FIELDS = {'name', 'description'}


def _frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        raise ValueError('El frontmatter YAML no comienza en la primera línea')
    try:
        end = lines.index('---', 1)
    except ValueError:
        raise ValueError('Falta cierre --- del frontmatter') from None
    values: dict[str, str | list[str]] = {}
    current = None
    for ln in lines[1:end]:
        if not ln.strip():
            continue
        if ln.startswith('  - '):
            if current != 'skills' or not isinstance(values.get(current), list):
                raise ValueError(f'Elemento de lista fuera de skills: {ln}')
            values[current].append(ln.strip()[2:].strip())
            continue
        if ln[0].isspace() or ':' not in ln:
            raise ValueError(f'Línea YAML no soportada: {ln}')
        key, val = ln.split(':', 1)
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', key):
            raise ValueError(f'Campo YAML incorrecto: {key}')
        if key in values:
            raise ValueError(f'Campo YAML duplicado: {key}')
        current = key
        if key == 'skills':
            if val.strip():
                raise ValueError('skills debe ser una lista de guiones en líneas siguientes')
            values[key] = []
        else:
            v = val.strip()
            if v.startswith(('"', "'")) and v.endswith(v[:1]) and len(v) >= 2:
                v = v[1:-1]
            if not v:
                raise ValueError(f'Campo vacío: {key}')
            values[key] = v
    return values


def _check_links(file: Path, errors: list[str]) -> None:
    for match in REF_RE.finditer(file.read_text(encoding='utf-8')):
        target = match.group(1).split('#',1)[0]
        if not target or target.startswith(('http://', 'https://', 'mailto:', '#')):
            continue
        if not (file.parent / target).resolve().is_file():
            errors.append(f'Enlace local roto en {file}: {target}')


def _check_claude_md(file: Path, errors: list[str], strict_content: bool = False) -> None:
    if not file.is_file():
        errors.append(f'Falta CLAUDE.md en {file}')
        return
    contents = file.read_text(encoding='utf-8')
    if contents.count(START) != 1 or contents.count(END) != 1 or contents.index(START) >= contents.index(END):
        errors.append(f'CLAUDE.md sin bloque ATB válido: {file}')
        return
    if strict_content:
        reference = (PACKAGE_ROOT/'CLAUDE.md').read_text(encoding='utf-8')
        block = contents.split(START, 1)[1].split(END, 1)[0]
        refblock = reference.split(START, 1)[1].split(END, 1)[0]
        if block != refblock:
            errors.append(f'Bloque de coordinación ATB obsoleto o modificado en {file}. Actualiza con --force tras revisarlo.')


def validate(target: Path, require_claude_md: bool = False) -> list[str]:
    target = Path(target).expanduser().resolve()
    errors: list[str] = []
    names: set[str] = set()
    for role in REQUIRED:
        name = f'atb-{role}'
        agent = target/'agents'/f'{name}.md'
        skill = target/'skills'/name/'SKILL.md'
        if not agent.is_file():
            errors.append(f'Falta subagente {agent}')
        else:
            try:
                raw = agent.read_text(encoding='utf-8')
                header = _frontmatter(raw)
                unknown = set(header) - ALLOWED_AGENT_FIELDS
                if unknown:
                    errors.append(f'Frontmatter desconocido en {agent}: {sorted(unknown)}')
                if header.get('name') != name or not header.get('description'):
                    errors.append(f'Nombre o descripción incorrectos: {agent}')
                if header.get('name') in names:
                    errors.append(f'Nombre de agente repetido: {name}')
                names.add(name)
                if header.get('skills') != [name]:
                    errors.append(f'El agente debe precargar exactamente {name}: {agent}')
                if header.get('model') != ('opus' if role == 'plan' else 'sonnet'):
                    errors.append(f'Modelo inesperado: {agent}')
                if header.get('effort') != ('medium' if role == 'plan' else 'low'):
                    errors.append(f'Esfuerzo inesperado: {agent}')
                if role in ('research', 'plan', 'review'):
                    if header.get('permissionMode') != 'plan':
                        errors.append(f'Falta plan mode en {agent}')
                    denied = set(str(header.get('disallowedTools','')).split(', '))
                    if not {'Write','Edit','NotebookEdit'} <= denied:
                        errors.append(f'Falta denylist de editores: {agent}')
                if 'Context7:' not in raw:
                    errors.append(f'Agente sin regla Context7: {agent}')
                if not raw.split('---',2)[-1].strip():
                    errors.append(f'Sin instrucciones de agente: {agent}')
                _check_links(agent, errors)
            except (OSError, UnicodeError, ValueError) as e:
                errors.append(f'{agent}: {e}')
        if not skill.is_file():
            errors.append(f'Falta skill {skill}')
        else:
            try:
                raw = skill.read_text(encoding='utf-8')
                h = _frontmatter(raw)
                if set(h) - ALLOWED_SKILL_FIELDS:
                    errors.append(f'Campos no previstos en skill {skill}: {sorted(set(h)-ALLOWED_SKILL_FIELDS)}')
                if h.get('name') != name or not h.get('description'):
                    errors.append(f'Nombre o descripción incorrectos: {skill}')
                if f'# {name}' not in raw:
                    errors.append(f'Título de skill desalineado: {skill}')
                if '## Procedimiento mínimo' not in raw or '## Entrega' not in raw:
                    errors.append(f'Falta procedimiento/entrega: {skill}')
                if '[../atb-shared/context7.md]' not in raw:
                    errors.append(f'Skill sin política Context7: {skill}')
                if len(raw.splitlines()) > 500:
                    errors.append(f'Skill demasiado larga: {skill}')
                _check_links(skill, errors)
            except (OSError, UnicodeError, ValueError) as e:
                errors.append(f'{skill}: {e}')
    shared = target/'skills'/'atb-shared'
    for item in SHARED:
        if not (shared/f'{item}.md').is_file():
            errors.append(f'Falta recurso: {shared/item}.md')
    if (shared/'SKILL.md').exists():
        errors.append('atb-shared solo contiene referencias; no es una skill')
    for file in shared.glob('*.md'):
        _check_links(file, errors)
    if require_claude_md:
        _check_claude_md(target/'CLAUDE.md', errors, strict_content=True)
    return errors


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description='Validar archivos de subagentes, skills y CLAUDE.md')
    p.add_argument('--scope', choices=('package','user','project'), default='package')
    p.add_argument('--project-root', type=Path)
    p.add_argument('--config-dir', type=Path)
    p.add_argument('--no-claude-md', action='store_true', help='Validar sólo agentes y skills')
    a = p.parse_args(argv)
    if a.scope == 'package':
        base=PACKAGE_ROOT/'.claude'
    elif a.scope == 'user':
        base = a.config_dir or (Path(os.environ['CLAUDE_CONFIG_DIR']).expanduser() if os.environ.get('CLAUDE_CONFIG_DIR') else Path.home()/'.claude')
    else:
        if not a.project_root:
            p.error('--project-root es necesario con --scope project')
        base=a.project_root/'.claude'
    failures=validate(base, require_claude_md=(a.scope!='package' and not a.no_claude_md))
    if a.scope=='package' and not a.no_claude_md:
        _check_claude_md(PACKAGE_ROOT/'CLAUDE.md', failures)
    for error in failures:
        print('ERROR:', error)
    if failures:
        return 1
    print(f'OK: CLAUDE.md, 8 subagentes, 8 skills, referencias (Engram y Context7 externos) | {base}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
