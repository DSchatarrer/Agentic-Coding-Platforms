from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import install
import validate


class PackageTests(unittest.TestCase):
    def test_package_structure(self):
        self.assertEqual([], validate.validate(ROOT/'.claude'))

    def test_global_dry_run_does_not_touch_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'.claude'
            logs=install.install(scope='user', config_dir=path, dry_run=True)
            self.assertTrue(any('ESCRIBIR' in s for s in logs))
            self.assertFalse(path.exists())

    def test_install_global_additive_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'.claude'
            path.mkdir()
            (path/'settings.json').write_text('{"permissions": {"allow": ["mcp__engram__*"]}}', encoding='utf-8')
            (path/'CLAUDE.md').write_text('Mis instrucciones\n',encoding='utf-8')
            (Path(tmp)/'.claude.json').write_text('{"mcpServers": {"engram": {}}}', encoding='utf-8')
            install.install(scope='user', config_dir=path)
            self.assertEqual([], validate.validate(path))
            self.assertEqual('Mis instrucciones\n\n', (path/'CLAUDE.md').read_text(encoding='utf-8').split('<!-- agent-teams-basic-claude:start -->')[0])
            self.assertIn('engram', (path/'settings.json').read_text(encoding='utf-8'))
            self.assertIn('engram', (Path(tmp)/'.claude.json').read_text(encoding='utf-8'))
            before={p.relative_to(path): p.read_bytes() for p in path.rglob('*') if p.is_file()}
            logs=install.install(scope='user', config_dir=path)
            after={p.relative_to(path): p.read_bytes() for p in path.rglob('*') if p.is_file()}
            self.assertEqual(before,after)
            self.assertFalse(any('CONFLICTO' in s for s in logs))

    def test_conflicts_preserved_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'.claude'
            (path/'agents').mkdir(parents=True)
            file=path/'agents'/'atb-create.md'
            file.write_text('personal', encoding='utf-8')
            logs=install.install(scope='user', config_dir=path)
            self.assertEqual('personal', file.read_text(encoding='utf-8'))
            self.assertTrue(any('CONFLICTO' in s for s in logs))
            install.install(scope='user', config_dir=path, force=True)
            self.assertIn('skills:',file.read_text(encoding='utf-8'))
            self.assertTrue(list(file.parent.glob('atb-create.md.bak.atb-*')))

    def test_project_scope_does_not_install_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)/'repo'
            repo.mkdir()
            install.install(scope='project', project_root=repo)
            self.assertEqual([],validate.validate(repo/'.claude'))
            self.assertTrue((repo/'.claude'/'CLAUDE.md').exists())

    def test_invalid_scope_rejected(self):
        with self.assertRaises(ValueError):
            install.install(scope='project')

    def test_replacement_only_managed_block(self):
        start='<!-- agent-teams-basic-claude:start -->'
        end='<!-- agent-teams-basic-claude:end -->'
        previous=f'Mis normas\n{start}\nVIEJO\n{end}\nNotas\n'
        snippet=(ROOT/'CLAUDE.md').read_text(encoding='utf-8')
        merged,msg=install._merge_claude(previous,snippet,True)
        self.assertTrue(merged.startswith('Mis normas\n'))
        self.assertTrue(merged.endswith('Notas\n'))
        self.assertNotIn('VIEJO',merged)
        self.assertIsNone(install._merge_claude(previous,snippet,False)[0])



class VersionTwoRegressionTests(unittest.TestCase):
    def test_canonical_entry_filename(self):
        self.assertTrue((ROOT/'CLAUDE.md').is_file())
        self.assertFalse((ROOT/'CLAUDE.snippet.md').exists())

    def test_different_prior_block_detected_and_force_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'.claude'
            dest.mkdir()
            p = dest/'CLAUDE.md'
            old = 'Reglas propias\n\n'+install.START+'\n## Antes v1\n'+install.END+'\nFinal\n'
            p.write_text(old, encoding='utf-8')
            logs = install.install(scope='user', config_dir=dest, force=False)
            self.assertTrue(any('CONFLICTO:' in x for x in logs))
            self.assertEqual(old,p.read_text(encoding='utf-8'))
            logs = install.install(scope='user', config_dir=dest, force=True)
            new = p.read_text(encoding='utf-8')
            self.assertIn('Reglas propias\n\n',new)
            self.assertIn('Final\n',new)
            self.assertEqual(1,new.count(install.START))
            self.assertIn('Coordinación de subagentes',new)
            self.assertEqual([],validate.validate(dest,require_claude_md=True))
            self.assertTrue(any('RESPALDO' in x for x in logs))

    def test_validate_requires_coordinator_at_installed_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/'.claude'
            install.install(scope='user', config_dir=dst, include_claude_md=False)
            self.assertEqual([],validate.validate(dst))
            self.assertTrue(any('CLAUDE.md' in x for x in validate.validate(dst, require_claude_md=True)))

    def test_malformed_legacy_markers_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'.claude'
            dest.mkdir()
            file=dest/'CLAUDE.md'
            file.write_text('Original\n'+install.START+'\nAlgo sin cierre',encoding='utf-8')
            logs=install.install(scope='user', config_dir=dest, force=True)
            self.assertTrue(any('CONFLICTO:' in x for x in logs))
            self.assertEqual('Original\n'+install.START+'\nAlgo sin cierre',file.read_text(encoding='utf-8'))

    def test_engram_and_other_config_are_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            dest=root/'.claude'
            dest.mkdir()
            settings=dest/'settings.json'
            mcps=root/'.claude.json'
            settings.write_bytes(b'{"custom":true,"permissions":{"allow":["mcp__engram__mem_search"]}}')
            mcps.write_bytes(b'{"mcpServers":{"engram":{"command":"C:\\\\engram\\\\engram.exe"}}}')
            before=(settings.read_bytes(),mcps.read_bytes())
            install.install(scope='user',config_dir=dest,force=True)
            self.assertEqual(before,(settings.read_bytes(),mcps.read_bytes()))

    def test_cli_nonzero_on_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'.claude'
            (dest/'agents').mkdir(parents=True)
            (dest/'agents'/'atb-create.md').write_text('Custom',encoding='utf-8')
            rc=install.main(['--scope','user','--config-dir',str(dest)])
            self.assertEqual(1,rc)

    def test_all_frontmatter_parses_as_yaml(self):
        try:
            import yaml
        except ImportError:
            self.skipTest('PyYAML opcional no instalado')
        for p in [*(ROOT/'.claude/agents').glob('*.md'),*(ROOT/'.claude/skills').glob('atb-*/SKILL.md')]:
            txt=p.read_text(encoding='utf-8')
            header=yaml.safe_load(txt.split('---',2)[1])
            self.assertIsInstance(header,dict,p)
            self.assertTrue(header['name'].startswith('atb-'))



class Context7VersionThreeTests(unittest.TestCase):
    def test_context7_policy_is_optional_external_and_linked(self):
        reference = ROOT/'.claude/skills/atb-shared/context7.md'
        self.assertTrue(reference.is_file())
        self.assertFalse((ROOT/'.claude/skills/atb-shared/SKILL.md').exists())
        self.assertIn('Context7 (opcional, MCP externo)', (ROOT/'CLAUDE.md').read_text(encoding='utf-8'))
        for role in validate.REQUIRED:
            agent = (ROOT/'.claude/agents'/f'atb-{role}.md').read_text(encoding='utf-8')
            skill = (ROOT/'.claude/skills'/f'atb-{role}'/'SKILL.md').read_text(encoding='utf-8')
            self.assertIn('Context7:',agent,role)
            self.assertIn('atb-shared/context7.md',skill,role)

    def test_context7_plugin_not_installed_automatically(self):
        installer = (ROOT/'scripts/install.py').read_text(encoding='utf-8')
        self.assertNotIn('plugin install',installer)
        self.assertNotIn('mcp add',installer)
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            dest = base/'.claude'
            dest.mkdir()
            settings = dest/'settings.json'
            mcps = base/'.claude.json'
            settings.write_bytes(b'{"permissions":{"allow":["mcp__engram__*"]}}')
            mcps.write_bytes(b'{"mcpServers":{"engram":{"command":"engram"},"context7":{"url":"https://mcp.context7.com/mcp"}}}')
            before = (settings.read_bytes(), mcps.read_bytes())
            install.install(scope='user', config_dir=dest,force=True)
            self.assertEqual(before, (settings.read_bytes(), mcps.read_bytes()))
            self.assertEqual([],validate.validate(dest,require_claude_md=True))

    def test_context7_setup_requires_explicit_install_switch(self):
        script = (ROOT/'scripts/setup-context7.ps1').read_text(encoding='utf-8')
        self.assertIn('param([switch]$Install)',script)
        self.assertIn('if (-not $Install)',script)
        self.assertIn('context7@context7-marketplace --scope user',script)

    def test_v2_upgrade_preserves_other_claude_instructions(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td)/'.claude'
            dest.mkdir()
            target = dest/'CLAUDE.md'
            old = 'Mi contenido personalizado\n\n'+install.START+'\nAntiguo v2\n'+install.END+'\nMi posdata\n'
            target.write_text(old,encoding='utf-8')
            logs = install.install(scope='user',config_dir=dest,force=True)
            now = target.read_text(encoding='utf-8')
            self.assertIn('Mi contenido personalizado',now)
            self.assertIn('Mi posdata',now)
            self.assertIn('Context7 (opcional, MCP externo)',now)
            self.assertNotIn('Antiguo v2',now)
            self.assertTrue(any('RESPALDO' in l for l in logs))
            self.assertEqual([],validate.validate(dest,require_claude_md=True))

if __name__ == '__main__':
    unittest.main()
