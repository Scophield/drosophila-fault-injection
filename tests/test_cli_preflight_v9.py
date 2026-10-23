import argparse
import ast
from contextlib import redirect_stderr
import io
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_reproduction import check_command,declared_flags,option_supported


class Preflight(unittest.TestCase):
    def test_wrapper_validates_target_script_and_rejects_unknown_option(self):
        result=check_command('python -X utf8 tools/run_v9.py tools/analyze_task_v9_exportfix.py --root runs/x --registration runs/r.json --out audit/x')
        self.assertEqual(result['script'],'tools/analyze_task_v9_exportfix.py')
        self.assertTrue(result['wrapped'])
        with self.assertRaisesRegex(ValueError,'unsupported'):
            check_command('python tools/run_v9.py tools/analyze_task_v9_exportfix.py --not-a-real-option x')

    def test_dynamic_declarations_match_actual_argparse_options(self):
        source="""for name in ['main-build','supplement-build','out']:
    ap.add_argument('--'+name)
"""
        flags=declared_flags(ast.parse(source))
        parser=argparse.ArgumentParser()
        for name in ['main-build','supplement-build','out']:parser.add_argument('--'+name)
        expected={k for k in parser._option_string_actions if k.startswith('--') and k!='--help'}
        self.assertEqual(flags,expected)

    def test_legal_prefix_and_ambiguity_agree_with_argparse(self):
        parser=argparse.ArgumentParser();parser.add_argument('--faults')
        self.assertEqual(parser.parse_args(['--fault','F2']).faults,'F2')
        self.assertTrue(option_supported('--fault',{'--faults'}))
        parser.add_argument('--fault-model')
        with redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):parser.parse_args(['--fault','F2'])
        self.assertFalse(option_supported('--fault',{'--faults','--fault-model'}))
        self.assertFalse(option_supported('--fault',{'--faults'},allow_abbrev=False))


if __name__=='__main__':unittest.main()
