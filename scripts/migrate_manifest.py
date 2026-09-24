#!/usr/bin/env python3
"""Losslessly migrate known v1 content into an explicitly unreviewed v2 draft.

The converter cannot verify sources, invent learning objectives, associate old
cards reliably or write a semantic grading rubric.  The output is deliberately
not renderable until these editorial tasks have been completed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def new_id(prefix: str, old_id: str) -> str:
    value = prefix + old_id
    return value if len(value) <= 64 else value[:51] + '-' + hashlib.sha256(value.encode()).hexdigest()[:12]


def migrate(data: dict) -> dict:
    if not isinstance(data, dict) or type(data.get('schema_version', 1)) is not int or data.get('schema_version', 1) != 1:
        raise ValueError('migration accepts v1 manifests only')
    allowed_top = {'schema_version', 'title', 'topics', 'caption', 'dimensions', 'cards'}
    if set(data) - allowed_top:
        raise ValueError(f'unknown v1 top-level fields must be reviewed manually: {sorted(set(data)-allowed_top)}')
    migrated = {
        'schema_version': 2, 'title': data['title'],
        'dimensions': {'width': 1200, 'height': 1600},
        'migration_review_required': True,
        'units': [{'id': 'legacy-unit', 'title': data['title'],
                   'objective': '待内容审核：按原主题明确能够解释或应用的目标。原主题：' + '；'.join(data['topics']),
                   'scope': data['caption'], 'prerequisites': [], 'source_ids': []}],
        'sources': [], 'questions': [], 'cards': [],
    }
    explanation_ids = [c['id'] for c in data['cards'] if c['type'] == 'explanation']
    occupied = {c['id'] for c in data['cards']}
    for card in data['cards']:
        known = {'id', 'type', 'title', 'tags'} | ({'definition', 'points', 'table', 'chart', 'takeaway'} if card['type'] == 'explanation' else {'prompt', 'blanks', 'answer_key'})
        if set(card) - known:
            raise ValueError(f"{card['id']}: unsupported v1 fields require manual migration: {sorted(set(card)-known)}")
        common = {'id': card['id'], 'unit_id': 'legacy-unit', 'title': card['title']}
        if card['type'] == 'explanation':
            blocks = []
            if card.get('definition'):
                blocks.append({'id': 'definition', 'kind': 'paragraph', 'text': card['definition']})
            if card.get('points'):
                for point in card['points']:
                    if set(point) != {'label', 'text'}:
                        raise ValueError(f"{card['id']}: unsupported point fields require manual migration")
                blocks.append({'id': 'points', 'kind': 'steps', 'items': card['points']})
            if card.get('table'):
                table = card['table']
                if set(table) - {'headers', 'rows'}:
                    raise ValueError(f"{card['id']}: unsupported table fields require manual migration")
                blocks.append({'id': 'table', 'kind': 'table', 'headers': table['headers'], 'rows': [[str(cell) for cell in row] for row in table['rows']]})
            if card.get('chart'):
                chart = card['chart']
                if set(chart) - {'kind', 'labels', 'values', 'caption'}:
                    raise ValueError(f"{card['id']}: unsupported chart fields require manual migration")
                blocks.append({'id': 'chart', 'kind': 'bar', 'labels': chart['labels'], 'values': chart['values'], 'caption': chart.get('caption', '待审核：原图数值尚未注明是示意还是测量，渲染前必须核实。')})
            if card.get('takeaway'):
                blocks.append({'id': 'takeaway', 'kind': 'callout', 'text': card['takeaway'], 'tone': 'key'})
            if card.get('tags'):
                blocks.append({'id': 'legacy-tags', 'kind': 'paragraph', 'heading': '原卡标签（审核后整合）', 'text': '、'.join(card['tags'])})
            migrated['cards'].append({**common, 'type': 'explanation', 'layout': 'concept', 'blocks': blocks})
        else:
            solution_blocks = [{'id': f'answer-{i}', 'kind': 'paragraph', 'text': answer} for i, answer in enumerate(card['answer_key'], 1)]
            context = [{'id': 'legacy-response-cues', 'kind': 'bullets', 'heading': '原题作答提示（审核是否需要保留）', 'items': card['blanks']}]
            if card.get('tags'):
                context.append({'id': 'legacy-tags', 'kind': 'paragraph', 'heading': '原卡标签（审核后整合）', 'text': '、'.join(card['tags'])})
            migrated['questions'].append({
                'id': card['id'], 'unit_id': 'legacy-unit', 'title': card['title'], 'prompt': card['prompt'],
                'context': context, 'explanation_ids': explanation_ids,
                'solution': {'blocks': solution_blocks,
                             'criteria': [{'id': 'review-rubric', 'required': True, 'text': '待人工审核拆分：说明原答案中的结论、关键理由与必要条件；此条不能直接用于口述判定。'}],
                             'critical_errors': [], 'accepted_variants': []},
            })
            migrated['cards'].append({**common, 'type': 'self_check', 'layout': 'question', 'question_id': card['id']})
            aid = new_id('answer-', card['id'])
            while aid in occupied:
                aid = new_id('a-', aid)
            occupied.add(aid)
            migrated['cards'].append({'id': aid, 'type': 'answer', 'unit_id': 'legacy-unit', 'layout': 'answer', 'question_id': card['id'], 'solution_refs': [b['id'] for b in solution_blocks] + ['@criteria']})
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', required=True, type=Path, help='new v2 draft; existing files are not overwritten')
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError(f'output already exists: {args.output}; choose a new draft path')
        result = subprocess.run([sys.executable, str(Path(__file__).parent / 'legacy' / 'validate_manifest.py'), str(args.manifest)], capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stderr.strip() or 'v1 validation failed')
        data = migrate(json.loads(args.manifest.read_text(encoding='utf-8')))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'v2 migration draft written: {args.output}')
        print('NOT RENDERABLE: review units, objectives, sources, prerequisites, card associations, answer criteria and pagination; then remove migration_review_required. No source URLs or semantic criteria were invented.')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'migration failed: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
