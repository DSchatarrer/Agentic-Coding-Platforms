"""Pruebas de integridad e instalación con la biblioteca estándar."""
import importlib.util
import re
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent

def load(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

installer = load(ROOT/'scripts'/'install.py', 'atb_install')
validator = load(ROOT/'scripts'/'validate.py', 'atb_validate')

class PackageTests(unittest.TestCase):
    def test_original_is_valid(self):
        self.assertEqual(validator.validate(ROOT), [])

    def test_install_idempotent_and_preserves_existing_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target/'AGENTS.md').write_text('Reglas originales\n', encoding='utf-8')
            (target/'.codex').mkdir()
            (target/'.codex'/'config.toml').write_text('[mcp_servers.engram]\ncommand="engram"\n', encoding='utf-8')
            first = installer.install(target)
            self.assertTrue(any('ESCRIBIR' in line for line in first))
            self.assertEqual(validator.validate(target), [])
            original = (target/'AGENTS.md').read_text(encoding='utf-8')
            self.assertTrue(original.startswith('Reglas originales'))
            self.assertIn('agent-teams-basic:start', original)
            self.assertIn('command="engram"', (target/'.codex'/'config.toml').read_text(encoding='utf-8'))
            second = installer.install(target)
            self.assertFalse(any(x.startswith('ESCRIBIR') for x in second))
            self.assertEqual((target/'AGENTS.md').read_text(encoding='utf-8'), original)

    def test_conflict_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            (target/'.codex'/'agents').mkdir(parents=True)
            (target/'.codex'/'agents'/'research.toml').write_text('CUSTOM', encoding='utf-8')
            logs=installer.install(target)
            self.assertTrue(any('CONFLICTO' in line for line in logs))
            self.assertEqual((target/'.codex'/'agents'/'research.toml').read_text(), 'CUSTOM')

    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            installer.install(target, dry_run=True)
            self.assertEqual(list(target.iterdir()), [])

    def test_broken_ref_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            installer.install(target)
            (target/'.agents'/'skills'/'research'/'references'/'investigation.md').unlink()
            self.assertTrue(any('Enlace roto' in e for e in validator.validate(target)))


    def test_python_reference_example_runtime(self):
        """The Python library example runs, not just passes AST parsing."""
        import re
        import subprocess
        import sys
        ref = (ROOT/'.agents'/'skills'/'_shared'/'python-libraries.md').read_text(encoding='utf-8')
        blocks = re.findall(r'```python\n(.*?)```', ref, re.S)
        sections = re.split(r'(?m)^# (src/acme_data/[^\n]+)\n', blocks[0])
        self.assertEqual(len(sections), 7)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'src'/'acme_data'
            source.mkdir(parents=True)
            (source/'__init__.py').write_text('', encoding='utf-8')
            for filename, content in zip(sections[1::2], sections[2::2]):
                self.assertEqual(Path(filename).parent.name, 'acme_data')
                (source/Path(filename).name).write_text(content, encoding='utf-8')
            (source/'encoder.py').write_text(blocks[1], encoding='utf-8')
            code = """from acme_data.adapters import MemoryStore
from acme_data.service import DocumentService
from acme_data.encoder import Encoder, IdentityEncoder
x = DocumentService(MemoryStore())
x.save('k', b'v')
assert x.load('k') == b'v'
try:
    Encoder()
except TypeError:
    pass
else:
    raise AssertionError('ABC must not be instantiated')
assert IdentityEncoder().encode_checked(b'v') == b'v'
"""
            proc = subprocess.run([sys.executable, '-c', code], cwd=root, env={
                **__import__('os').environ, 'PYTHONPATH': str(root/'src')
            }, capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_anthropic_skill_metadata_and_reference(self):
        import re
        ref = ROOT/'.agents'/'skills'/'_shared'/'python-libraries.md'
        self.assertTrue(ref.is_file())
        self.assertIn('class Store(Protocol):', ref.read_text(encoding='utf-8'))
        self.assertIn('class Encoder(ABC):', ref.read_text(encoding='utf-8'))
        for name in ('create', 'plan', 'review', 'refactor', 'test', 'docs'):
            skill = ROOT/'.agents'/'skills'/name/'SKILL.md'
            text = skill.read_text(encoding='utf-8')
            self.assertLess(len(text.splitlines()), 500)
            self.assertIn('[../_shared/python-libraries.md](../_shared/python-libraries.md)', text)
            self.assertIn('## Ejemplos de activación', text)

    def test_missing_python_reference_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            installer.install(target)
            (target/'.agents'/'skills'/'_shared'/'python-libraries.md').unlink()
            self.assertTrue(any('Enlace roto' in msg for msg in validator.validate(target)))

    def test_invalid_skill_description_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            installer.install(target)
            p = target/'.agents'/'skills'/'create'/'SKILL.md'
            text = p.read_text(encoding='utf-8')
            p.write_text(re.sub(r'(?m)^description:.*$', 'description: ', text), encoding='utf-8')
            self.assertTrue(any('Descripcion no valida' in msg for msg in validator.validate(target)))

    def test_python_reference_code_examples_parse(self):
        import ast
        import re
        import tomllib
        ref = (ROOT/'.agents'/'skills'/'_shared'/'python-libraries.md').read_text(encoding='utf-8')
        code = re.findall(r'```python\n(.*?)```', ref, re.S)
        self.assertGreaterEqual(len(code), 3)
        for snippet in code:
            ast.parse(snippet)
        toml_snippets = re.findall(r'```toml\n(.*?)```', ref, re.S)
        for snippet in toml_snippets:
            tomllib.loads(snippet)

    def test_shared_patterns_adapted_without_sdd(self):
        shared = ROOT/'.agents'/'skills'/'_shared'
        resolver = (shared/'skill-resolver.md').read_text(encoding='utf-8')
        engram = (shared/'engram.md').read_text(encoding='utf-8')
        handoff = (shared/'handoff.md').read_text(encoding='utf-8')
        self.assertIn('mem_get_observation', resolver)
        self.assertIn('skill-registry', resolver)
        self.assertIn('.atl/skill-registry.md', resolver)
        self.assertIn('cinco', resolver.lower())
        self.assertIn('SKILL.md', resolver)
        self.assertIn('agent-teams/{project}/{kind}/{slug}', engram)
        self.assertIn('mem_get_observation', engram)
        self.assertIn('pueden modificar', engram)
        self.assertIn('skill_resolution', handoff)
        self.assertNotIn('openspec/changes/', engram)

    def test_install_preserves_existing_atl_skill_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            registry = target/'.atl'/'skill-registry.md'
            registry.parent.mkdir(parents=True)
            registry.write_text('# Custom register\n## Compact Rules\n- Python: pytest\n', encoding='utf-8')
            installer.install(target, force=True)
            self.assertEqual(registry.read_text(encoding='utf-8'), '# Custom register\n## Compact Rules\n- Python: pytest\n')
            self.assertFalse((target/'openspec').exists())
            self.assertEqual(validator.validate(target), [])

    def test_agent_role_skill_not_replaced_by_compact_rules(self):
        for name in validator.REQUIRED:
            agent = __import__('tomllib').loads((ROOT/'.codex'/'agents'/f'{name}.toml').read_text(encoding='utf-8'))
            instructions = agent['developer_instructions']
            self.assertIn(f'.agents/skills/{name}/SKILL.md', instructions)
            self.assertIn('Project Standards (auto-resolved)', instructions)
            self.assertIn('skill_resolution', instructions)

    def test_refactor_architecture_references_are_direct_and_targeted(self):
        skill = (ROOT/'.agents/skills/refactor/SKILL.md').read_text(encoding='utf-8')
        for stem in ('architecture-selection', 'clean-architecture',
                     'hexagonal-architecture', 'layered-architecture'):
            target = ROOT/'.agents/skills/refactor/references'/f'{stem}.md'
            self.assertTrue(target.is_file(), target)
            self.assertIn(f'](references/{stem}.md)', skill)
            self.assertIn('Abrir solo', skill)
        self.assertLess(len(skill.splitlines()), 500)

    def test_refactor_architecture_docs_have_rules_tests_and_sources(self):
        files = ROOT/'.agents/skills/refactor/references'
        expected = {
            'clean-architecture.md': ('dependencias', 'test', 'informit.com'),
            'hexagonal-architecture.md': ('puerto', 'adaptador', 'cockburn'),
            'layered-architecture.md': ('capas', 'tests', 'learn.microsoft.com'),
            'architecture-selection.md': ('migración', 'matriz', 'pruebas'),
        }
        for filename, words in expected.items():
            body=(files/filename).read_text(encoding='utf-8').lower()
            for word in words:
                self.assertIn(word, body, f'{word} missing from {filename}')

    def test_refactor_architecture_python_examples_parse(self):
        import ast
        for filename in ('clean-architecture.md', 'hexagonal-architecture.md',
                         'layered-architecture.md'):
            body=(ROOT/'.agents/skills/refactor/references'/filename).read_text(encoding='utf-8')
            snippets = re.findall(r'```python\n(.*?)```', body, re.S)
            self.assertGreater(len(snippets), 0, filename)
            for snippet in snippets:
                ast.parse(snippet)

    def test_refactor_installs_new_architectures(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            installer.install(target)
            self.assertEqual(validator.validate(target), [])
            self.assertTrue((target/'.agents/skills/refactor/references/clean-architecture.md').is_file())
            (target/'.agents/skills/refactor/references/hexagonal-architecture.md').unlink()
            self.assertTrue(any('Enlace roto' in e for e in validator.validate(target)))

    def test_architecture_source_links_and_direct_load(self):
        base = ROOT/'.agents/skills/refactor'
        skill = (base/'SKILL.md').read_text(encoding='utf-8')
        for name, key in (('architecture-selection', 'matriz'),
                          ('clean-architecture', 'dependencias'),
                          ('hexagonal-architecture', 'adaptadores'),
                          ('layered-architecture', 'capas'),
                          ('architecture-migration', 'rollback'),
                          ('architecture-verification', 'tests')):
            self.assertIn(f'](references/{name}.md)', skill)
            body=(base/'references'/f'{name}.md').read_text(encoding='utf-8')
            self.assertIn('## Índice', body)
            self.assertIn('## ', body)
            self.assertIn('https://', body)
            self.assertIn(key, body.lower())

    def test_architecture_examples_execute_without_network(self):
        import re
        files=ROOT/'.agents/skills/refactor/references'
        for name in ('clean-architecture', 'hexagonal-architecture',
                     'layered-architecture', 'architecture-verification'):
            code=re.findall(r'```python\n(.*?)```', (files/f'{name}.md').read_text(encoding='utf-8'), re.S)
            self.assertTrue(code, name)
            for snippet in code:
                namespace={'__name__': '__main__'}
                exec(compile(snippet, f'<{name}>', 'exec'), namespace)

    def test_new_refs_installed_and_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            installer.install(root)
            self.assertEqual(validator.validate(root), [])
            for name in ('architecture-migration.md','architecture-verification.md'):
                self.assertTrue((root/'.agents/skills/refactor/references'/name).exists())
            (root/'.agents/skills/refactor/references/architecture-verification.md').unlink()
            self.assertTrue(any('Enlace roto' in e for e in validator.validate(root)))



    def test_official_codex_entrypoint_names_in_package_and_install(self):
        from pathlib import Path
        import tomllib
        self.assertTrue((ROOT/'AGENTS.md').is_file())
        self.assertFalse((ROOT/'AGENTS.snippet.md').exists())
        self.assertTrue((ROOT/'.codex/config.toml').is_file())
        self.assertFalse((ROOT/'.codex/config.example.toml').exists())
        source = tomllib.loads((ROOT/'.codex/config.toml').read_text(encoding='utf-8'))
        self.assertNotIn('auth', source['mcp_servers']['context7'])
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            installer.install(target)
            self.assertEqual(validator.validate(target), [])
            self.assertEqual((target/'AGENTS.md').read_text(encoding='utf-8'),
                             (ROOT/'AGENTS.md').read_text(encoding='utf-8').rstrip()+'\n')

    def test_v6_context7_legacy_migrates_without_touching_engram(self):
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target/'.codex').mkdir()
            (target/'.codex/config.toml').write_text(
                '[mcp_servers.context7]\nurl = "https://mcp.context7.com/mcp"\n'
                'auth = "oauth"\nbearer_token_env_var = "CONTEXT7_API_KEY"\n'
                '[mcp_servers.engram]\ncommand = "engram"\n', encoding='utf-8')
            installer.install(target)
            data = tomllib.loads((target/'.codex/config.toml').read_text(encoding='utf-8'))
            self.assertEqual(data['mcp_servers']['context7'], {'url':'https://mcp.context7.com/mcp'})
            self.assertEqual(data['mcp_servers']['engram']['command'], 'engram')
            self.assertEqual(validator.validate(target), [])

    def test_context7_custom_auth_does_not_get_modified_by_installer(self):
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            (target/'.codex').mkdir()
            custom='[mcp_servers.context7]\nurl = "https://example.invalid/mcp"\n' \
                'http_headers = { Authorization = "some-test-value" }\n'
            (target/'.codex/config.toml').write_text(custom, encoding='utf-8')
            installer.install(target)
            data=tomllib.loads((target/'.codex/config.toml').read_text(encoding='utf-8'))
            self.assertEqual(data['mcp_servers']['context7']['url'],'https://example.invalid/mcp')
            self.assertEqual(data['mcp_servers']['context7']['http_headers']['Authorization'],'some-test-value')

    def test_context7_installed_as_remote_mcp_without_secrets(self):
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target/'.codex').mkdir()
            (target/'.codex/config.toml').write_text(
                '[mcp_servers.engram]\ncommand = "engram"\n'
                '[mcp_servers.my_custom]\nurl = "https://example.invalid/mcp"\n', encoding='utf-8')
            logs=installer.install(target)
            parsed=tomllib.loads((target/'.codex/config.toml').read_text(encoding='utf-8'))
            self.assertEqual(parsed['mcp_servers']['engram']['command'], 'engram')
            self.assertEqual(parsed['mcp_servers']['my_custom']['url'], 'https://example.invalid/mcp')
            ctx=parsed['mcp_servers']['context7']
            self.assertEqual(ctx['url'], 'https://mcp.context7.com/mcp')
            self.assertNotIn('auth', ctx)
            self.assertNotIn('bearer_token_env_var', ctx)
            self.assertNotIn('YOUR_API_KEY', (target/'.codex/config.toml').read_text(encoding='utf-8'))
            self.assertEqual(validator.validate(target), [])
            self.assertTrue(any('Context7 MCP remoto' in line for line in logs))

    def test_context7_installer_is_idempotent(self):
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            installer.install(target)
            first=(target/'.codex/config.toml').read_bytes()
            logs=installer.install(target)
            second=(target/'.codex/config.toml').read_bytes()
            self.assertEqual(first, second)
            self.assertTrue(any('IGUAL Context7 MCP' in log for log in logs))
            self.assertEqual(first.decode('utf-8').count('[mcp_servers.context7]'), 1)

    def test_context7_custom_configuration_is_not_overwritten(self):
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            (target/'.codex').mkdir()
            (target/'.codex/config.toml').write_text('''[mcp_servers.context7]
command = "custom-context7-executable"
args = ["--custom"]
[mcp_servers.engram]
command = "engram"
''', encoding='utf-8')
            installer.install(target, force=True)
            parsed=tomllib.loads((target/'.codex/config.toml').read_text(encoding='utf-8'))
            self.assertEqual(parsed['mcp_servers']['context7']['command'],'custom-context7-executable')
            self.assertNotIn('url', parsed['mcp_servers']['context7'])
            self.assertEqual(parsed['mcp_servers']['engram']['command'], 'engram')

    def test_context7_optional_install_flag_and_no_model_config(self):
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            installer.install(target, include_context7=False)
            data=tomllib.loads((target/'.codex/config.toml').read_text(encoding='utf-8'))
            self.assertNotIn('mcp_servers',data)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            installer.install(target, include_model_config=False)
            data=tomllib.loads((target/'.codex/config.toml').read_text(encoding='utf-8'))
            self.assertEqual(data['mcp_servers']['context7']['url'],'https://mcp.context7.com/mcp')
            self.assertNotIn('model',data)

    def test_context7_shared_reference_is_directly_linked_and_under_demand(self):
        ref = ROOT/'.agents/skills/_shared/context7.md'
        content=ref.read_text(encoding='utf-8')
        self.assertIn('resolve-library-id', content)
        self.assertIn('query-docs', content)
        self.assertIn('No envíes', content)
        for role in validator.REQUIRED:
            instructions=(ROOT/'.agents/skills'/role/'SKILL.md').read_text(encoding='utf-8')
            self.assertIn('](../_shared/context7.md)', instructions)
            self.assertIn('Abrir solo', instructions)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            installer.install(target)
            (target/'.agents/skills/_shared/context7.md').unlink()
            self.assertTrue(any('Enlace roto' in error for error in validator.validate(target)))

    def test_context7_mcp_merge_preserves_crlf_and_rejects_bad_toml(self):
        import tomllib
        before='[mcp_servers.engram]\r\ncommand = "engram"\r\n'
        after, added = installer.merge_context7_mcp(before)
        self.assertTrue(added)
        self.assertEqual(after.replace('\r\n','').find('\n'), -1)
        self.assertEqual(tomllib.loads(after)['mcp_servers']['engram']['command'], 'engram')
        with self.assertRaises(tomllib.TOMLDecodeError):
            installer.merge_context7_mcp('not valid = ???')

    def test_skill_creator_scaffold_only_skill(self):
        creator = load(ROOT/'.agents/skills/skill-creator/scripts/scaffold_skill.py', 'atb_scaffold')
        check = load(ROOT/'.agents/skills/skill-creator/scripts/validate_skill.py', 'atb_validate_new')
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            installer.install(project)
            paths = creator.create_skill(project, 'http-client',
                'Crea un cliente HTTP tipado cuando el usuario solicite integraciones API')
            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].is_file())
            self.assertFalse((project/'.codex/agents/http-client.toml').exists())
            self.assertEqual(check.validate(project, 'http-client'), [])
            self.assertNotIn('http-client', (project/'AGENTS.md').read_text(encoding='utf-8'))

    def test_skill_creator_optional_agent_and_no_clobber(self):
        creator = load(ROOT/'.agents/skills/skill-creator/scripts/scaffold_skill.py', 'atb_scaffold_with_agent')
        check = load(ROOT/'.agents/skills/skill-creator/scripts/validate_skill.py', 'atb_validate_agent')
        import tomllib
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            installer.install(project)
            paths = creator.create_skill(project, 'http-client',
                'Crea clientes HTTP y valida respuestas', with_agent=True)
            self.assertEqual(len(paths), 2)
            agent = tomllib.loads(paths[1].read_text(encoding='utf-8'))
            self.assertEqual(agent['model'], 'gpt-6-sol')
            self.assertEqual(agent['model_reasoning_effort'], 'low')
            self.assertIn('.agents/skills/http-client/SKILL.md', agent['developer_instructions'])
            self.assertEqual(check.validate(project, 'http-client'), [])
            original = paths[0].read_bytes()
            with self.assertRaises(FileExistsError):
                creator.create_skill(project, 'http-client', 'Otra descripcion', with_agent=True)
            self.assertEqual(paths[0].read_bytes(), original)

    def test_skill_creator_dry_run_rejects_bad_names_and_broken_refs(self):
        creator = load(ROOT/'.agents/skills/skill-creator/scripts/scaffold_skill.py', 'atb_scaffold_dry')
        check = load(ROOT/'.agents/skills/skill-creator/scripts/validate_skill.py', 'atb_validate_broken')
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            creator.create_skill(project, 'new-skill', 'Para una tarea concreta', dry_run=True)
            self.assertFalse((project/'.agents').exists())
            with self.assertRaises(ValueError):
                creator.create_skill(project, '../bad', 'Para una tarea concreta')
            [path] = creator.create_skill(project, 'new-skill', 'Para una tarea concreta')
            path.write_text(path.read_text(encoding='utf-8') +
                            '\n[algo](references/inexistente.md)\n', encoding='utf-8')
            self.assertTrue(any('Referencia no encontrada' in e for e in check.validate(project, 'new-skill')))

    def test_new_agent_is_installed_with_eight_existing_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            installer.install(target)
            self.assertEqual(validator.validate(target), [])
            agent = target/'.codex/agents/skill-creator.toml'
            self.assertTrue(agent.is_file())
            self.assertTrue((target/'.agents/skills/skill-creator/scripts/scaffold_skill.py').is_file())
            self.assertIn('`skill-creator`', (target/'AGENTS.md').read_text(encoding='utf-8'))

if __name__=='__main__':
    unittest.main()
