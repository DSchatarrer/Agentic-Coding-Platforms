#!/usr/bin/env python3
"""Comprueba integridad estructural del paquete ya instalado o extraído."""
import argparse
from pathlib import Path
import re
import sys
import tomllib

REF_RE = re.compile(r'\[[^\]]+\]\(([^)]+\.md)\)')
VALID_NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')

REQUIRED = ('research', 'plan', 'create', 'debug', 'test', 'review', 'refactor', 'docs', 'skill-creator')
MODEL_COORDINATOR = ('gpt-6-astra', 'medium')
MODEL_WORKER = ('gpt-6-sol', 'low')


def validate(project_root: Path):
    project_root = Path(project_root).expanduser().resolve()
    errors = []
    agents = project_root / '.codex' / 'agents'
    skills = project_root / '.agents' / 'skills'
    for name in REQUIRED:
        afile = agents / f'{name}.toml'
        sfile = skills / name / 'SKILL.md'
        if not afile.is_file():
            errors.append(f'Falta agente: {afile}')
        else:
            try:
                data = tomllib.loads(afile.read_text(encoding='utf-8'))
                if data.get('name') != name:
                    errors.append(f'Nombre del agente incorrecto: {afile}')
                if not data.get('description') or not data.get('developer_instructions'):
                    errors.append(f'Agente incompleto: {afile}')
                if f'.agents/skills/{name}/SKILL.md' not in data.get('developer_instructions', ''):
                    errors.append(f'Agente no apunta a su skill: {afile}')
                expected = MODEL_COORDINATOR if name == 'plan' else MODEL_WORKER
                if (data.get('model'), data.get('model_reasoning_effort')) != expected:
                    errors.append(f'Modelo o razonamiento incorrecto de {name}: {afile}')
            except Exception as exc:
                errors.append(f'TOML invalido en {afile}: {exc}')
        if not sfile.is_file():
            errors.append(f'Falta skill: {sfile}')
        else:
            text = sfile.read_text(encoding='utf-8')
            # Frontmatter YAML mínimo y límites oficiales de Agent Skills (Anthropic).
            lines = text.splitlines()
            if not lines or lines[0] != '---' or '---' not in lines[1:]:
                errors.append(f'Frontmatter invalido en {sfile}')
            else:
                closing = lines[1:].index('---') + 1
                header = lines[1:closing]
                fields = {}
                for line in header:
                    if ':' in line and not line.lstrip().startswith('#'):
                        key, val = line.split(':', 1)
                        fields[key.strip()] = val.strip().strip('"\'')
                sname = fields.get('name', '')
                desc = fields.get('description', '')
                if sname != name or len(sname) > 64 or not VALID_NAME.fullmatch(sname):
                    errors.append(f'Nombre no valido en frontmatter: {sfile}')
                if not desc or len(desc) > 1024 or '<' in desc or '>' in desc:
                    errors.append(f'Descripcion no valida en frontmatter: {sfile}')
                if not any(x in desc.lower() for x in ('úsala', 'úsalo', 'usa ', 'cuando ', 'para ')):
                    errors.append(f'Descripcion sin contexto de activacion: {sfile}')
                if len(lines) - closing - 1 >= 500:
                    errors.append(f'SKILL.md supera 500 lineas: {sfile}')
                if '## Procedimiento mínimo' not in text or '## Entrega' not in text:
                    errors.append(f'Skill sin procedimiento o entrega: {sfile}')
            if not REF_RE.findall(text):
                errors.append(f'Skill sin referencias: {sfile}')
            for target in REF_RE.findall(text):
                resolved = (sfile.parent / target).resolve()
                if not resolved.is_file():
                    errors.append(f'Enlace roto: {sfile}: {target}')
    config = project_root / '.codex' / 'config.toml'
    if config.exists():
        try:
            data = tomllib.loads(config.read_text(encoding='utf-8'))
            if (data.get('model'), data.get('model_reasoning_effort')) != MODEL_COORDINATOR:
                errors.append(f'Modelo del coordinador incorrecto: {config}')
            ag = data.get('agents', {})
            if (ag.get('default_subagent_model'), ag.get('default_subagent_reasoning_effort')) != MODEL_WORKER:
                errors.append(f'Modelo predeterminado de los subagentes incorrecto: {config}')
            ctx = data.get('mcp_servers', {}).get('context7', {})
            if ctx and 'auth' in ctx:
                errors.append(f'Context7 usa una clave TOML no documentada (auth): {config}')
            if ctx and not (ctx.get('url') or ctx.get('command')):
                errors.append(f'Context7 necesita url o command: {config}')
        except (ValueError, OSError) as exc:
            errors.append(f'Config de modelos inválida: {config}: {exc}')
    # Valida las integraciones compartidas adicionales y la separación entre
    # la skill de rol, el resolvedor del coordinador y los estándares técnicos.
    for expected in ('skill-resolver.md', 'engram.md', 'handoff.md', 'loading-policy.md', 'python-libraries.md', 'context7.md'):
        if not (skills/'_shared'/expected).is_file():
            errors.append(f'Falta referencia compartida: {expected}')
    snippet = project_root / 'AGENTS.md'
    if not snippet.is_file():
        errors.append(f'Falta punto de entrada AGENTS.md: {snippet}')
    else:
        st = snippet.read_text(encoding='utf-8')
        if 'agent-teams-basic:start' in st:
            for expected in ('_shared/skill-resolver.md', '_shared/engram.md', '_shared/context7.md'):
                if expected not in st:
                    errors.append(f'Falta integración en AGENTS: {expected}')
    for afile in agents.glob('*.toml'):
        if afile.stem not in REQUIRED:
            continue
        agent = tomllib.loads(afile.read_text(encoding='utf-8'))
        instructions = agent.get('developer_instructions', '')
        if 'Project Standards (auto-resolved)' not in instructions or 'skill_resolution' not in instructions:
            errors.append(f'Agente sin soporte de estándares y handoff: {afile}')
    if (skills/'_shared'/'SKILL.md').exists():
        errors.append('_shared debe ser carpeta auxiliar, no una skill con SKILL.md')
    for link in (skills/'_shared').glob('*.md'):
        for target in REF_RE.findall(link.read_text(encoding='utf-8')):
            if not (link.parent/target).resolve().is_file():
                errors.append(f'Enlace roto compartido: {link}: {target}')
    return errors


def main():
    ap = argparse.ArgumentParser(description='Valida Agent Teams Basic')
    ap.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parent.parent)
    args = ap.parse_args()
    errors = validate(args.project_root)
    if errors:
        print('\n'.join('ERROR '+e for e in errors))
        return 1
    print('OK: 9 agentes y skills, referencias bajo demanda, Engram, Context7 MCP y modelos validados')
    return 0

if __name__=='__main__':
    sys.exit(main())
