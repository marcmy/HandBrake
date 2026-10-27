"""Exercise real version generation without starting configure's toolchain probes."""
import ast
import datetime
import fnmatch
import re
import time
import unittest
from pathlib import Path
from types import SimpleNamespace


class Action:
    def __init__(self, *args):
        pass


class ProjectVersionTests(unittest.TestCase):
    def test_package_versions_preserve_identity_without_path_separators(self):
        path = Path(__file__).resolve().parents[1] / 'make' / 'configure.py'
        tree = ast.parse(path.read_text())
        project = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Project')
        env = dict(Action=Action, fnmatch=fnmatch, re=re, time=time, now=time.gmtime(0),
                   AbortError=RuntimeError, options=SimpleNamespace(snapshot=False),
                   arch=SimpleNamespace(mode=SimpleNamespace(mode='arm64')))
        exec(compile(ast.fix_missing_locations(ast.Module(body=[project], type_ignores=[])), str(path), 'exec'), env)
        for host in ['x86_64-unknown-linux-gnu', 'aarch64-apple-darwin']:
            env['host_tuple'] = SimpleNamespace(spec=host)
            for branch in ['custom', 'codex/modernize-maintenance-20261026', 'feature/nested/topic', '']:
                with self.subTest(host=host, branch=branch):
                    env['repo'] = SimpleNamespace(date=datetime.datetime(2026, 10, 26), tag='1.11.0',
                                                 type='developer', branch=branch, shorthash='abc1234', hash='a' * 40)
                    obj = env['Project']()
                    obj._action()
                    self.assertNotIn('/', obj.version)
                    self.assertNotIn('/', obj.debversion)
                    self.assertEqual(env['repo'].branch, branch)
                    if branch == 'custom':
                        self.assertEqual(obj.version, '20261026000000-abc1234-custom')
            env['repo'].type = 'release'
            obj = env['Project']()
            obj._action()
            self.assertEqual(obj.version, '1.11.0')
            self.assertEqual(obj.debversion, '1.11.0')


if __name__ == '__main__':
    unittest.main()
