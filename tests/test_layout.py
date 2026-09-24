"""Real layout/renderer regressions: overflow, formula validity and output integrity."""
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from layout_v2 import Fonts, LayoutError, Scene, formula_image, plan_card
from render_v2 import render
from validate_outputs import validate_outputs
from test_contract import fixture
from PIL import Image


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fonts = Fonts()
        cls.theme = json.loads((SCRIPTS.parent / 'assets/theme.json').read_text())

    def card(self, blocks):
        return {'id': 'e1', 'type': 'explanation', 'title': '关系与条件', 'layout': 'concept',
                'unit_title': '排版验收', 'blocks': blocks}

    def test_six_points_are_not_silently_cut_to_four(self):
        points = ['第一步确认前提', '第二步建立关系', '第三步代入数据', '第四步完成计算', '第五步核对边界', '第六步检查结论']
        scene, report = plan_card(self.card([{'id': 'six', 'kind': 'bullets', 'items': points}]), self.fonts, self.theme)
        visible = ''.join(op[1] for op in scene.ops if op[0] == 'text')
        for text in points:
            self.assertIn(text, visible)
        self.assertEqual(report['block_ids'], ['six'])
        self.assertEqual(scene.render().size, (1200, 1600))

    def test_long_content_fails_with_card_and_block(self):
        with self.assertRaisesRegex(LayoutError, 'e1 / too-long'):
            plan_card(self.card([{'id': 'too-long', 'kind': 'paragraph', 'text': '必要条件不能被截断。' * 120}]), self.fonts, self.theme)

    def test_formula_real_fraction_and_transparent_sprite(self):
        image = formula_image(r'\frac{QK^T}{\sqrt{d_k}}', 60, '#172B40')
        self.assertGreater(image.height, 60)
        self.assertEqual(image.mode, 'RGBA')
        self.assertEqual(image.getchannel('A').getextrema()[0], 0)
        with self.assertRaises(LayoutError):
            formula_image(r'\unknowncommand{x}', 60, '#172B40')

    def test_wide_formula_is_not_scaled_down(self):
        block = {'id': 'wide', 'kind': 'formula', 'latex': '+'.join(['x_i'] * 60)}
        with self.assertRaisesRegex(LayoutError, 'formula width'):
            plan_card(self.card([block]), self.fonts, self.theme)

    def test_matrix_and_multiline_table_keep_all_content(self):
        blocks = [
            {'id': 'matrix', 'kind': 'matrix', 'cells': [[r'\frac{1}{2}', 'x_1'], ['0', r'\sqrt{2}']], 'left_label': 'A='},
            {'id': 'table', 'kind': 'table', 'headers': ['对象', '必要条件'], 'rows': [['分数', '先检查分母不为零，才能使用除法计算。'], ['结论', '最后一格必须完整显示。']], 'widths': [1, 3]}]
        scene, report = plan_card(self.card(blocks), self.fonts, self.theme)
        self.assertEqual(len([o for o in scene.ops if o[0] == 'image']), 5)
        visible = ''.join(o[1] for o in scene.ops if o[0] == 'text')
        self.assertIn('最后一格必须完整显示。', visible)
        self.assertEqual([b['id'] for b in report['blocks']], ['matrix', 'table'])

    def test_branch_flow_and_crossing_rejection(self):
        nodes = [{'id': n, 'label': n.upper()} for n in ['a', 'b', 'c', 'd']]
        diamond = {'id': 'flow', 'kind': 'flow', 'nodes': nodes, 'edges': [
            {'from': 'a', 'to': 'b', 'label': '条件一'}, {'from': 'a', 'to': 'c', 'label': '条件二'},
            {'from': 'b', 'to': 'd'}, {'from': 'c', 'to': 'd'}]}
        scene, report = plan_card(self.card([diamond]), self.fonts, self.theme)
        visible = ''.join(o[1] for o in scene.ops if o[0] == 'text')
        self.assertIn('条件一', visible)
        self.assertIn('条件二', visible)
        crossed = copy.deepcopy(diamond)
        crossed['edges'] = [{'from': 'a', 'to': 'd', 'label': '左'}, {'from': 'b', 'to': 'c', 'label': '右'}]
        with self.assertRaisesRegex(LayoutError, 'arrows cross'):
            plan_card(self.card([crossed]), self.fonts, self.theme)

    def test_missing_glyph_and_explicit_missing_font_fail(self):
        with self.assertRaisesRegex(LayoutError, 'missing glyph'):
            self.fonts.width('\U0010ffff', 48)
        with self.assertRaisesRegex(LayoutError, 'bold font not found'):
            Fonts(bold='/nonexistent/font.ttf')

    def test_font_environment_aliases_and_explicit_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            preferred = Path(tmp) / 'preferred.ttc'
            historical = Path(tmp) / 'historical.ttc'
            shutil.copyfile(self.fonts.regular, preferred)
            shutil.copyfile(self.fonts.regular, historical)
            env = {'CRASH_CARD_FONT': str(preferred), 'CRASH_FLASHCARD_FONT': str(historical),
                   'CRASH_CARD_BOLD_FONT': str(preferred), 'CRASH_FLASHCARD_BOLD_FONT': str(historical)}
            with patch.dict(os.environ, env):
                fonts = Fonts()
                self.assertEqual(fonts.regular, str(preferred.resolve()))
                self.assertEqual(fonts.bold, str(preferred.resolve()))
                explicit = Fonts(str(historical), str(historical))
                self.assertEqual(explicit.regular, str(historical.resolve()))
                self.assertEqual(explicit.bold, str(historical.resolve()))
            with patch.dict(os.environ, {**env, 'CRASH_CARD_FONT': '', 'CRASH_CARD_BOLD_FONT': ''}):
                fonts = Fonts()
                self.assertEqual(fonts.regular, str(historical.resolve()))
                self.assertEqual(fonts.bold, str(historical.resolve()))

    def test_punctuation_wrap_preserves_numbers_and_words(self):
        for word in ['27', 'InnoDB']:
            text = '甲乙丙' + word + '、后续内容'
            width = self.fonts.width('甲乙丙' + word, 48)
            lines = self.fonts.wrap(text, width, 48)
            self.assertTrue(any(word + '、' in line for line in lines), lines)
            self.assertEqual(''.join(lines), text)

    def test_valid_render_and_failed_rerender_preserves_outputs(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'pack'
            raw = json.dumps(data).encode()
            render(data, raw, out)
            self.assertEqual(validate_outputs(out, out / 'manifest.json'), [])
            before = (out / 'render-report.json').read_bytes()
            data['cards'][0]['blocks'][0]['text'] *= 1000
            with self.assertRaises(LayoutError):
                render(data, json.dumps(data).encode(), out)
            self.assertEqual((out / 'render-report.json').read_bytes(), before)

    def test_stale_unmanaged_png_not_deleted(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'pack'
            (out / 'explanation').mkdir(parents=True)
            old = out / 'explanation/personal.png'
            old.write_bytes(b'personal artifact')
            with self.assertRaisesRegex(LayoutError, 'unmanaged'):
                render(data, json.dumps(data).encode(), out)
            self.assertEqual(old.read_bytes(), b'personal artifact')

    def test_bool_version_is_not_dispatched_to_legacy(self):
        data = fixture()
        data['schema_version'] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'manifest.json'
            path.write_text(json.dumps(data))
            result = subprocess.run([sys.executable, str(SCRIPTS / 'render_cards.py'), str(path), '--output-dir', str(Path(tmp)/'out')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('must be an integer', result.stderr)


if __name__ == '__main__':
    unittest.main()
