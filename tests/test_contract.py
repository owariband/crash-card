"""Contract tests target lost content, bad references and unsafe migrations."""
from __future__ import annotations
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from v2_contract import validate, resolve_cards, export_text
from migrate_manifest import migrate


def fixture():
    return {
        'schema_version': 2, 'title': '因果解释', 'dimensions': {'width': 1200, 'height': 1600},
        'units': [{'id': 'u1', 'title': '单元', 'objective': '解释原因并说明条件', 'scope': '明确范围', 'prerequisites': [], 'source_ids': ['s1']}],
        'sources': [{'id': 's1', 'title': '一手来源', 'url': 'https://example.org/paper'}],
        'questions': [{'id': 'q1', 'unit_id': 'u1', 'title': '请解释', 'prompt': '条件改变后，结果为何改变？', 'explanation_ids': ['e1'],
                       'solution': {'blocks': [{'id': 'reason', 'kind': 'paragraph', 'text': '条件先改变机制，机制再改变结果。'}, {'id': 'boundary', 'kind': 'callout', 'text': '结论只在指定条件下成立。'}],
                                    'criteria': [{'id': 'causal', 'text': '说明条件到机制再到结果的关系。', 'required': True}],
                                    'critical_errors': ['把相关当作因果。'], 'accepted_variants': ['可以先讲结果，再倒推机制。']}}],
        'cards': [{'id': 'e1', 'type': 'explanation', 'unit_id': 'u1', 'layout': 'concept', 'blocks': [{'id': 'concept', 'kind': 'paragraph', 'text': '概念说明。'}]},
                  {'id': 'c1', 'type': 'self_check', 'unit_id': 'u1', 'layout': 'question', 'question_id': 'q1'},
                  {'id': 'a1', 'type': 'answer', 'unit_id': 'u1', 'layout': 'answer', 'question_id': 'q1', 'solution_refs': ['reason', 'boundary', '@criteria', '@errors', '@variants']}],
    }


class ContractTests(unittest.TestCase):
    def test_shared_solution_and_no_answer_leak(self):
        data = fixture()
        self.assertEqual(validate(data), [])
        cards = resolve_cards(data)
        self.assertNotIn('条件先改变机制', json.dumps(cards[1], ensure_ascii=False))
        self.assertEqual(cards[2]['blocks'][0]['text'], data['questions'][0]['solution']['blocks'][0]['text'])
        self.assertEqual(cards[2]['explanation_ids'], ['e1'])
        cards[2]['blocks'][0]['text'] = 'edit does not mutate source'
        self.assertNotEqual(cards[2]['blocks'][0]['text'], data['questions'][0]['solution']['blocks'][0]['text'])

    def test_uncovered_answer_and_criteria_rejected(self):
        data = fixture()
        data['cards'][2]['solution_refs'] = ['reason']
        errors = '\n'.join(validate(data))
        self.assertIn('boundary', errors)
        self.assertIn('@criteria', errors)

    def test_copy_of_answer_and_unknown_fields_rejected(self):
        data = fixture()
        data['cards'][1]['blocks'] = [{'id': 'leak', 'kind': 'paragraph', 'text': '答案'}]
        data['cards'][0]['blocks'][0]['extra_text'] = '必须保留的信息'
        errors = '\n'.join(validate(data))
        self.assertIn('copied content is forbidden', errors)
        self.assertIn('unsupported field', errors)

    def test_dimensions_and_unsafe_id(self):
        data = fixture()
        data['dimensions']['width'] = 1080
        data['cards'][0]['id'] = '../escape'
        errors = '\n'.join(validate(data))
        self.assertIn('1200 x 1600', errors)
        self.assertIn('safe ID', errors)

    def test_pagination_coverage_is_across_cards(self):
        data = fixture()
        data['cards'][2]['solution_refs'] = ['reason', '@criteria']
        data['cards'][2]['page'] = {'index': 1, 'total': 2}
        data['cards'].append({'id': 'a2', 'type': 'answer', 'unit_id': 'u1', 'layout': 'answer', 'question_id': 'q1', 'solution_refs': ['boundary'], 'page': {'index': 2, 'total': 2}})
        self.assertEqual(validate(data), [])
        data['cards'][3]['page']['index'] = 1
        self.assertIn('each index', '\n'.join(validate(data)))

    def test_flow_cycles_and_unknown_edges_rejected(self):
        data = fixture()
        data['cards'][0]['blocks'] = [{'id': 'f', 'kind': 'flow', 'nodes': [{'id': 'a', 'label': 'A'}, {'id': 'b', 'label': 'B'}], 'edges': [{'from': 'a', 'to': 'b'}, {'from': 'b', 'to': 'a'}]}]
        self.assertIn('acyclic', '\n'.join(validate(data)))
        data['cards'][0]['blocks'][0]['edges'] = [{'from': 'a', 'to': 'missing'}]
        self.assertIn('existing nodes', '\n'.join(validate(data)))

    def test_numeric_fields_disallow_nan_bool_and_misalignment(self):
        data = fixture()
        data['cards'][0]['blocks'] = [{'id': 'bar1', 'kind': 'bar', 'labels': ['甲'], 'values': [float('nan')], 'caption': '示意值'}, {'id': 'tab1', 'kind': 'table', 'headers': ['甲', '乙'], 'rows': [['1']], 'widths': [True, 1]}]
        errors = '\n'.join(validate(data))
        self.assertIn('finite non-negative', errors)
        self.assertIn('match header width', errors)
        self.assertIn('finite positive', errors)

    def test_latex_nested_braces_are_not_placeholders(self):
        data = fixture()
        data['cards'][0]['blocks'] = [{'id': 'math1', 'kind': 'formula', 'latex': r'\frac{QK^T}{\sqrt{d_k}}'}]
        self.assertEqual(validate(data), [])

    def test_invalid_list_types_are_reported(self):
        for place, field in [('card', 'depth'), ('card', 'type'), ('block', 'tone'), ('block', 'kind')]:
            data = fixture()
            target = data['cards'][0] if place == 'card' else data['cards'][0]['blocks'][0]
            target[field] = []
            self.assertTrue(validate(data), (place, field))

    def test_exports_include_every_answer_source(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as directory:
            export_text(data, directory)
            out = Path(directory)
            transcript = (out / 'transcript.md').read_text()
            answer_key = (out / 'answer-key.md').read_text()
            rubric = json.loads((out / 'oral-rubric.json').read_text())
            for b in data['questions'][0]['solution']['blocks']:
                self.assertIn(b['text'], transcript)
                self.assertIn(b['text'], answer_key)
            self.assertEqual(rubric['questions'], data['questions'])
            self.assertIn('未检验', (out / 'review.md').read_text())

    def test_migration_preserves_knowledge_and_blocks_rendering(self):
        old = {'title': '旧卡', 'caption': '范围说明', 'topics': ['主题'], 'dimensions': {'width': 1080, 'height': 1350}, 'cards': [
            {'id': 'old-e', 'type': 'explanation', 'title': '概念', 'definition': '原定义', 'points': [{'label': '原因', 'text': '原来的完整机制'}], 'table': {'headers': ['A', 'B'], 'rows': [['1', '2']]}, 'chart': {'kind': 'bar', 'labels': ['x'], 'values': [2]}, 'takeaway': '边界条件'},
            {'id': 'old-q', 'type': 'quick_check', 'title': '问题', 'prompt': '为什么？', 'blanks': ['口述'], 'answer_key': ['原来的完整答案']} ]}
        new = migrate(old)
        self.assertIs(new['migration_review_required'], True)
        for text in ('原定义', '原来的完整机制', '边界条件', '原来的完整答案'):
            self.assertIn(text, json.dumps(new, ensure_ascii=False))
        with self.assertRaisesRegex(ValueError, 'migration draft'):
            resolve_cards(new)
        new.pop('migration_review_required')
        self.assertTrue(validate(new), 'removing marker alone must not invent missing sources')

    def test_v1_validator_dispatch(self):
        old = {'title': '旧卡', 'caption': '说明', 'topics': ['主题'], 'dimensions': {'width': 1080, 'height': 1350}, 'cards': [{'id': 'e1', 'type': 'explanation', 'title': '概念', 'definition': '原定义'}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            path.write_text(json.dumps(old))
            run = subprocess.run([sys.executable, str(SCRIPTS / 'validate_manifest.py'), str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('1080x1350', run.stdout)


try:
    from PIL import Image
    HAVE_PILLOW = True
except ImportError:
    HAVE_PILLOW = False

@unittest.skipUnless(HAVE_PILLOW, 'Pillow required for output verification tests')
class OutputIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.data = fixture()
        self.manifest = self.directory / 'manifest.json'
        self.manifest.write_text(json.dumps(self.data))
        report = {'schema_version': 2, 'manifest_sha256': hashlib.sha256(self.manifest.read_bytes()).hexdigest(), 'dimensions': self.data['dimensions'], 'cards': []}
        from v2_contract import TYPE_DIRS
        for card in resolve_cards(self.data):
            relative = f"{TYPE_DIRS[card['type']]}/{card['id']}.png"
            path = self.directory / relative
            path.parent.mkdir(exist_ok=True)
            Image.new('RGB', (1200, 1600), 'white').save(path)
            report['cards'].append({'id': card['id'], 'type': card['type'], 'path': relative, 'png_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'width': 1200, 'height': 1600, 'block_ids': [b['id'] for b in card['blocks']], 'content_top': 400, 'content_bottom': 400 + len(card['blocks']) * 60, 'blocks': [{'id': b['id'], 'kind': b['kind'], 'box': [72, 400 + i * 60, 1056, 50]} for i, b in enumerate(card['blocks'])]})
        self.report = self.directory / 'render-report.json'
        self.report.write_text(json.dumps(report))

    def tearDown(self):
        self.tmp.cleanup()

    def test_good_decode_and_report(self):
        from validate_outputs import validate_outputs
        self.assertEqual(validate_outputs(self.directory, self.manifest), [])

    def test_corrupt_pixel_stream_is_rejected(self):
        from validate_outputs import validate_outputs
        path = self.directory / 'answer/a1.png'
        original = path.read_bytes()
        path.write_bytes(original[:100])
        self.assertIn('decode failed', '\n'.join(validate_outputs(self.directory, self.manifest)))

    def test_missing_block_and_changed_manifest_rejected(self):
        from validate_outputs import validate_outputs
        report = json.loads(self.report.read_text())
        report['cards'][2]['block_ids'].pop()
        self.report.write_text(json.dumps(report))
        self.manifest.write_text(json.dumps(self.data, indent=2))
        errors = '\n'.join(validate_outputs(self.directory, self.manifest))
        self.assertIn('rendered blocks', errors)
        self.assertIn('manifest_sha256', errors)

    def test_measured_missing_or_overlapping_blocks_rejected(self):
        from validate_outputs import validate_outputs
        report = json.loads(self.report.read_text())
        report['cards'][2]['blocks'][1]['box'][1] = 410
        report['cards'][0]['blocks'][0]['box'][0] = 20
        self.report.write_text(json.dumps(report))
        errors = '\n'.join(validate_outputs(self.directory, self.manifest))
        self.assertIn('overlap', errors)
        self.assertIn('safe bounds', errors)

    def test_changed_png_hash_rejected_even_when_decodable(self):
        from validate_outputs import validate_outputs
        Image.new('RGB', (1200, 1600), 'red').save(self.directory / 'answer/a1.png')
        self.assertIn('SHA256', '\n'.join(validate_outputs(self.directory, self.manifest)))


if __name__ == '__main__':
    unittest.main()
