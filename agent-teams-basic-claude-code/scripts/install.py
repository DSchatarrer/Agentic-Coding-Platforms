#!/usr/bin/env python3
"""Instala ATB para Claude Code, aditivamente, sin tocar Engram ni Context7.

Requisitos: Python 3.10+. Biblioteca estándar. Ámbito user o project.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
START = '<!-- agent-teams-basic-claude:start -->'
END = '<!-- agent-teams-basic-claude:end -->'


def _config_dir() -> Path:
    override = os.environ.get('CLAUDE_CONFIG_DIR', '').strip()
    return Path(override).expanduser() if override else Path.home() / '.claude'


def _backup(target: Path, dry_run: bool) -> str:
    suffix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    candidate = target.with_name(f'{target.name}.bak.atb-{suffix}')
    if not dry_run:
        shutil.copy2(target, candidate)
    return f'RESPALDO {target} -> {candidate}'


def _safe_parent(parent: Path, install_root: Path) -> None:
    # Safety: refuse to cross symlinks inside the managed destination layout.
    for obj in [install_root, *[p for p in parent.parents if p == install_root or install_root in p.parents], parent]:
        if obj.is_symlink():
            raise ValueError(f'Ruta simbólica inesperada en destino: {obj}')


def _dest_dir(scope: str, project_root: Path | None, config_dir: Path | None) -> Path:
    if scope == 'user':
        return (config_dir or _config_dir()).expanduser().resolve()
    if project_root is None:
        raise ValueError('Para --scope project indica --project-root "C:\\ruta\\proyecto"')
    project_root = project_root.expanduser().resolve()
    if not project_root.is_dir():
        raise ValueError(f'No existe el proyecto: {project_root}')
    return project_root / '.claude'


def _merge_claude(existing: str, snippet: str, force: bool) -> tuple[str | None, str]:
    if START in existing or END in existing:
        if existing.count(START) != 1 or existing.count(END) != 1 or existing.index(START) > existing.index(END):
            return None, 'CONFLICTO: marcadores de orquestación incompletos o duplicados; se conserva CLAUDE.md'
        prefix, tail_with_end = existing.split(START, 1)
        _, suffix = tail_with_end.split(END, 1)
        merged = prefix + snippet.rstrip('\n') + suffix
        if existing == merged:
            return existing, 'IGUAL CLAUDE.md (bloque ya actualizado)'
        if not force:
            return None, 'CONFLICTO: bloque ATB existente diferente en CLAUDE.md; revisa y usa --force para actualizar solamente ese bloque'
        return merged, 'ACTUALIZAR solo bloque de Agent Teams Basic en CLAUDE.md'
    merged = (existing.rstrip() + '\n\n' if existing.strip() else '') + snippet.rstrip() + '\n'
    return merged, 'AÑADIR bloque de orquestación a CLAUDE.md conservando lo anterior'


def install(scope: str = 'user', project_root: Path | None = None,
            dry_run: bool = False, force: bool = False,
            include_claude_md: bool = True, config_dir: Path | None = None) -> list[str]:
    dstroot = _dest_dir(scope, project_root, config_dir)
    logs: list[str] = [f'ÁMBITO {scope} | DESTINO {dstroot}']
    for root in (PACKAGE_ROOT / '.claude' / 'agents', PACKAGE_ROOT / '.claude' / 'skills'):
        for src in sorted(root.rglob('*')):
            if not src.is_file():
                continue
            dst = dstroot / src.relative_to(PACKAGE_ROOT / '.claude')
            _safe_parent(dst.parent, dstroot)
            if dst.is_symlink() or (dst.exists() and not dst.is_file()):
                logs.append(f'CONFLICTO: destino no es archivo regular: {dst}')
                continue
            if dst.exists() and dst.read_bytes() == src.read_bytes():
                logs.append(f'IGUAL {dst}')
                continue
            if dst.exists() and not force:
                logs.append(f'CONFLICTO: se conserva {dst}; usa --force para respaldar y actualizar')
                continue
            if dst.exists():
                logs.append(_backup(dst, dry_run))
            logs.append(f'ESCRIBIR {dst}')
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    if include_claude_md:
        path = dstroot / 'CLAUDE.md'
        if path.is_symlink() or (path.exists() and not path.is_file()):
            logs.append(f'CONFLICTO: CLAUDE.md no es un archivo regular: {path}')
        else:
            existing = path.read_text(encoding='utf-8') if path.exists() else ''
            snippet = (PACKAGE_ROOT / 'CLAUDE.md').read_text(encoding='utf-8')
            merged, msg = _merge_claude(existing, snippet, force)
            logs.append(msg)
            if merged is not None and merged != existing:
                if path.exists():
                    logs.append(_backup(path, dry_run))
                if not dry_run:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(merged, encoding='utf-8')
    logs.append('NO SE MODIFICA: MCPs/plugins Engram y Context7, hooks, settings.json, .claude.json, modelos globales ni otros proyectos')
    return logs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Instalar 8 subagentes + skills Claude Code (sin reinstalar Engram)')
    parser.add_argument('--scope', choices=('user', 'project'), default='user')
    parser.add_argument('--project-root', type=Path, help='Obligatorio solo para --scope project')
    parser.add_argument('--config-dir', type=Path, help='Opcional: sobreescribir destino de usuario, útil en pruebas')
    parser.add_argument('--dry-run', action='store_true', help='Solo muestra operaciones')
    parser.add_argument('--force', action='store_true', help='Reemplazar solo archivos gestionados, creando respaldo')
    parser.add_argument('--no-claude-md', action='store_true', help='No insertar orquestación en CLAUDE.md')
    args = parser.parse_args(argv)
    try:
        logs = install(args.scope, args.project_root, args.dry_run, args.force,
                       not args.no_claude_md, args.config_dir)
        for line in logs:
            print(line)
        if any('CONFLICTO:' in line for line in logs):
            print('Se detectaron conflictos; no se modificaron los archivos afectados.', file=sys.stderr)
            return 1
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
