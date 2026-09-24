#!/usr/bin/env python3
"""Strict v2 content contract and the shared source for PNG/text/oral review.

Only JSON data is accepted.  validate never silently repairs, truncates or drops
content.  resolve_cards produces the complete ordered blocks a renderer must
account for.  Layout fit and factual correctness are separate review steps.
"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path
from urllib.parse import urlparse

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
LAYOUTS = {"concept", "formula", "process", "comparison", "worked_example", "misconception", "question", "answer"}
TYPES = {"explanation", "self_check", "answer"}
TYPE_DIRS = {"explanation": "explanation", "self_check": "self-check", "answer": "answer"}
BLOCK_FIELDS = {
    "paragraph": {"text"}, "callout": {"text", "tone"},
    "bullets": {"items"}, "formula": {"latex", "caption"},
    "matrix": {"cells", "left_label", "caption"},
    "table": {"headers", "rows", "widths"},
    "flow": {"nodes", "edges"}, "steps": {"items"},
    "code": {"text"}, "bar": {"labels", "values", "caption"},
}


def validate(data: object) -> list[str]:
    """Return all structural errors. An unreviewed migration is not renderable."""
    errors: list[str] = []

    def err(path, message):
        errors.append(f"{path}: {message}")

    def obj(value, path, allowed):
        if not isinstance(value, dict):
            err(path, "must be an object")
            return False
        for field in value.keys() - allowed:
            err(path, f"unsupported field {field!r}; content must not be silently ignored")
        return True

    def string(value, path, empty=False):
        if not isinstance(value, str) or (not empty and not value.strip()):
            err(path, "must be a non-empty string" if not empty else "must be a string")
            return False
        if "[TODO]" in value or "[TBD]" in value:
            err(path, "unresolved placeholder")
        return True

    def identifier(value, path):
        if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
            err(path, "must be a safe ID: 1-64 ASCII letters, digits, dot, underscore or hyphen; start with a letter/digit")
            return False
        return True

    def arr(value, path, nonempty=False):
        if not isinstance(value, list) or (nonempty and not value):
            err(path, "must be a non-empty array" if nonempty else "must be an array")
            return False
        return True

    def strings(value, path, nonempty=False):
        if arr(value, path, nonempty):
            for i, entry in enumerate(value):
                string(entry, f"{path}[{i}]")
            return True
        return False

    def number(value):
        if type(value) not in (int, float):
            return False
        try:
            return math.isfinite(value)
        except OverflowError:
            return False

    def indexed(value, path, allowed, nonempty=True):
        result = {}
        if arr(value, path, nonempty):
            for i, entry in enumerate(value):
                p = f"{path}[{i}]"
                if not obj(entry, p, allowed):
                    continue
                key = entry.get("id")
                if identifier(key, p + ".id"):
                    if key in result:
                        err(p + ".id", f"duplicate ID {key!r}")
                    else:
                        result[key] = entry
        return result

    def blocks(value, path, nonempty=True):
        seen = set()
        if not arr(value, path, nonempty):
            return
        for i, block in enumerate(value):
            p = f"{path}[{i}]"
            if not isinstance(block, dict):
                err(p, "must be an object")
                continue
            kind = block.get("kind")
            if not isinstance(kind, str) or kind not in BLOCK_FIELDS:
                err(p + ".kind", "unsupported block kind")
                continue
            obj(block, p, {"id", "kind", "heading"} | BLOCK_FIELDS[kind])
            bid = block.get("id")
            if identifier(bid, p + ".id"):
                if bid in seen:
                    err(p + ".id", f"duplicate block ID {bid!r}")
                seen.add(bid)
            if "heading" in block:
                string(block["heading"], p + ".heading")
            if "caption" in block:
                string(block["caption"], p + ".caption")
            if "tone" in block and (not isinstance(block["tone"], str) or block["tone"] not in {"key", "caution"}):
                err(p + ".tone", "must be key or caution")
            if kind in {"paragraph", "callout", "code"}:
                string(block.get("text"), p + ".text")
            elif kind == "bullets":
                strings(block.get("items"), p + ".items", True)
            elif kind == "formula":
                string(block.get("latex"), p + ".latex")
            elif kind == "matrix":
                cells = block.get("cells")
                if arr(cells, p + ".cells", True):
                    width = None
                    for ri, row in enumerate(cells):
                        if strings(row, f"{p}.cells[{ri}]", True):
                            if width is None:
                                width = len(row)
                            elif len(row) != width:
                                err(p + ".cells", "matrix rows must have equal width")
                if "left_label" in block:
                    string(block["left_label"], p + ".left_label")
            elif kind == "table":
                headers, rows = block.get("headers"), block.get("rows")
                valid_headers = strings(headers, p + ".headers", True)
                if arr(rows, p + ".rows", True):
                    for ri, row in enumerate(rows):
                        if arr(row, f"{p}.rows[{ri}]", True):
                            if valid_headers and len(row) != len(headers):
                                err(f"{p}.rows[{ri}]", "must match header width")
                            for ci, cell in enumerate(row):
                                string(cell, f"{p}.rows[{ri}][{ci}]", empty=True)
                if "widths" in block:
                    widths = block["widths"]
                    if arr(widths, p + ".widths", True):
                        if valid_headers and len(widths) != len(headers):
                            err(p + ".widths", "must have one relative width per column")
                        if any(not number(n) or n <= 0 for n in widths):
                            err(p + ".widths", "must be finite positive numbers")
            elif kind == "flow":
                nodes = indexed(block.get("nodes"), p + ".nodes", {"id", "label", "text"})
                for nid, node in nodes.items():
                    string(node.get("label"), p + f".nodes.{nid}.label")
                    if "text" in node:
                        string(node["text"], p + f".nodes.{nid}.text")
                adjacency = {nid: [] for nid in nodes}
                indegree = {nid: 0 for nid in nodes}
                edges = block.get("edges")
                seen_edges = set()
                if arr(edges, p + ".edges"):
                    for ei, edge in enumerate(edges):
                        ep = f"{p}.edges[{ei}]"
                        if not obj(edge, ep, {"from", "to", "label"}):
                            continue
                        left, right = edge.get("from"), edge.get("to")
                        if not isinstance(left, str) or left not in nodes or not isinstance(right, str) or right not in nodes:
                            err(ep, "edge must reference existing nodes")
                        else:
                            if (left, right) in seen_edges:
                                err(ep, "duplicate edge")
                            seen_edges.add((left, right))
                            adjacency[left].append(right)
                            indegree[right] += 1
                        if "label" in edge:
                            string(edge["label"], ep + ".label")
                queue = [nid for nid, degree in indegree.items() if degree == 0]
                visited = 0
                while queue:
                    nid = queue.pop()
                    visited += 1
                    for child in adjacency[nid]:
                        indegree[child] -= 1
                        if indegree[child] == 0:
                            queue.append(child)
                if visited != len(nodes):
                    err(p, "flow must be a directed acyclic graph; split an iterative cycle into one iteration plus an explicit repetition note")
            elif kind == "steps":
                if arr(block.get("items"), p + ".items", True):
                    for si, step in enumerate(block["items"]):
                        sp = f"{p}.items[{si}]"
                        if obj(step, sp, {"label", "text"}):
                            string(step.get("label"), sp + ".label")
                            string(step.get("text"), sp + ".text")
            elif kind == "bar":
                labels, values = block.get("labels"), block.get("values")
                labels_ok = strings(labels, p + ".labels", True)
                if arr(values, p + ".values", True):
                    if labels_ok and len(labels) != len(values):
                        err(p, "bar labels and values must have equal length")
                    if any(not number(v) or v < 0 for v in values):
                        err(p + ".values", "must be finite non-negative numbers")
                if string(block.get("caption"), p + ".caption"):
                    if not re.search(r"示意|测量|实测|illustrativ|measur", block["caption"], re.I):
                        err(p + ".caption", "must declare whether values are illustrative (示意) or measured (测量/实测)")

    if not obj(data, "manifest", {"schema_version", "title", "dimensions", "units", "sources", "questions", "cards", "migration_review_required"}):
        return errors
    if type(data.get("schema_version")) is not int or data["schema_version"] != 2:
        err("schema_version", "must be integer 2")
    if "migration_review_required" in data:
        if type(data["migration_review_required"]) is not bool:
            err("migration_review_required", "must be boolean")
        elif data["migration_review_required"]:
            err("migration_review_required", "migration draft requires content/source/rubric review before rendering; remove this marker only after review")
    string(data.get("title"), "title")
    dims = data.get("dimensions")
    if obj(dims, "dimensions", {"width", "height"}):
        if type(dims.get("width")) is not int or type(dims.get("height")) is not int or (dims["width"], dims["height"]) != (1200, 1600):
            err("dimensions", "v2 requires exactly 1200 x 1600 pixels")
    units = indexed(data.get("units"), "units", {"id", "title", "objective", "scope", "prerequisites", "source_ids"})
    sources = indexed(data.get("sources"), "sources", {"id", "title", "url", "note"})
    questions = indexed(data.get("questions"), "questions", {"id", "unit_id", "title", "prompt", "context", "explanation_ids", "solution"})
    cards = indexed(data.get("cards"), "cards", {"id", "type", "unit_id", "title", "layout", "depth", "blocks", "question_id", "solution_refs", "page"})
    for sid, source in sources.items():
        p = f"sources.{sid}"
        string(source.get("title"), p + ".title")
        if string(source.get("url"), p + ".url"):
            try:
                parsed = urlparse(source["url"])
                valid_url = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
            except ValueError:
                valid_url = False
            if not valid_url:
                err(p + ".url", "must be an absolute HTTP(S) source URL")
        if "note" in source:
            string(source["note"], p + ".note")
    for uid, unit in units.items():
        p = f"units.{uid}"
        for field in ("title", "objective", "scope"):
            string(unit.get(field), p + "." + field)
        strings(unit.get("prerequisites"), p + ".prerequisites")
        if strings(unit.get("source_ids"), p + ".source_ids", True):
            for sid in unit["source_ids"]:
                if isinstance(sid, str) and sid not in sources:
                    err(p + ".source_ids", f"unknown source {sid!r}")
    for qid, question in questions.items():
        p = f"questions.{qid}"
        uid = question.get("unit_id")
        if not isinstance(uid, str) or uid not in units:
            err(p + ".unit_id", "must reference an existing unit")
        for field in ("title", "prompt"):
            string(question.get(field), p + "." + field)
        if "context" in question:
            blocks(question["context"], p + ".context", False)
        if strings(question.get("explanation_ids"), p + ".explanation_ids", True):
            for cid in question["explanation_ids"]:
                ref = cards.get(cid) if isinstance(cid, str) else None
                if not ref or ref.get("type") != "explanation" or ref.get("unit_id") != uid:
                    err(p + ".explanation_ids", f"{cid!r} must reference an explanation in the same unit")
        solution = question.get("solution")
        if obj(solution, p + ".solution", {"blocks", "criteria", "critical_errors", "accepted_variants"}):
            blocks(solution.get("blocks"), p + ".solution.blocks")
            criteria = indexed(solution.get("criteria"), p + ".solution.criteria", {"id", "text", "required"})
            for rid, criterion in criteria.items():
                string(criterion.get("text"), p + f".solution.criteria.{rid}.text")
                if type(criterion.get("required")) is not bool:
                    err(p + f".solution.criteria.{rid}.required", "must be boolean")
            if criteria and not any(c.get("required") is True for c in criteria.values()):
                err(p + ".solution.criteria", "at least one criterion must be required")
            strings(solution.get("critical_errors"), p + ".solution.critical_errors")
            strings(solution.get("accepted_variants"), p + ".solution.accepted_variants")
    for cid, card in cards.items():
        p = f"cards.{cid}"
        ctype, uid = card.get("type"), card.get("unit_id")
        if not isinstance(ctype, str) or ctype not in TYPES:
            err(p + ".type", "must be explanation, self_check or answer")
        if not isinstance(uid, str) or uid not in units:
            err(p + ".unit_id", "must reference an existing unit")
        if not isinstance(card.get("layout"), str) or card["layout"] not in LAYOUTS:
            err(p + ".layout", f"must be one of {', '.join(sorted(LAYOUTS))}")
        if "title" in card:
            string(card["title"], p + ".title")
        if "depth" in card and (not isinstance(card["depth"], str) or card["depth"] not in {"core", "deep"}):
            err(p + ".depth", "must be core or deep")
        if "page" in card:
            page = card["page"]
            if obj(page, p + ".page", {"index", "total"}):
                if type(page.get("index")) is not int or type(page.get("total")) is not int or not 1 <= page["index"] <= page["total"]:
                    err(p + ".page", "requires integers 1 <= index <= total")
        if ctype == "explanation":
            blocks(card.get("blocks"), p + ".blocks")
            if "question_id" in card or "solution_refs" in card:
                err(p, "explanation cannot contain question_id or solution_refs")
        elif ctype in ("self_check", "answer"):
            if "blocks" in card:
                err(p + ".blocks", "question/answer cards compile from questions; copied content is forbidden")
            qid = card.get("question_id")
            question = questions.get(qid) if isinstance(qid, str) else None
            if not question or question.get("unit_id") != uid:
                err(p + ".question_id", "must reference a question in the same unit")
            if ctype == "self_check" and "solution_refs" in card:
                err(p, "self_check cannot contain solution_refs")
            if ctype == "answer" and strings(card.get("solution_refs"), p + ".solution_refs", True):
                solution = question.get("solution", {}) if question else {}
                if not isinstance(solution, dict):
                    solution = {}
                solution_blocks = solution.get("blocks", [])
                legal_refs = {b.get("id") for b in solution_blocks if isinstance(b, dict) and isinstance(b.get("id"), str)} if isinstance(solution_blocks, list) else set()
                legal_refs |= {"@criteria", "@errors", "@variants"}
                seen_refs = set()
                for ref in card["solution_refs"]:
                    if not isinstance(ref, str):
                        continue
                    if ref not in legal_refs:
                        err(p + ".solution_refs", f"unknown solution reference {ref!r}")
                    if ref in seen_refs:
                        err(p + ".solution_refs", f"duplicate reference {ref!r}")
                    seen_refs.add(ref)
                    if ref == "@errors" and not solution.get("critical_errors"):
                        err(p + ".solution_refs", "@errors cannot reference an empty list")
                    if ref == "@variants" and not solution.get("accepted_variants"):
                        err(p + ".solution_refs", "@variants cannot reference an empty list")
    for uid in units:
        unit_cards = [c for c in cards.values() if c.get("unit_id") == uid]
        if not any(c.get("type") == "explanation" for c in unit_cards):
            err(f"units.{uid}", "requires at least one explanation card")
        if not any(q.get("unit_id") == uid for q in questions.values()):
            err(f"units.{uid}", "requires at least one question")
    for qid, question in questions.items():
        related = [c for c in cards.values() if c.get("question_id") == qid]
        if not any(c.get("type") == "self_check" for c in related):
            err(f"questions.{qid}", "requires a self_check card")
        answers = [c for c in related if c.get("type") == "answer"]
        if not answers:
            err(f"questions.{qid}", "requires at least one answer card")
        solution = question.get("solution")
        if isinstance(solution, dict) and isinstance(solution.get("blocks"), list):
            needed = {b["id"] for b in solution["blocks"] if isinstance(b, dict) and isinstance(b.get("id"), str)} | {"@criteria"}
            covered = {ref for card in answers for ref in card.get("solution_refs", []) if isinstance(ref, str)} if all(isinstance(c.get("solution_refs", []), list) for c in answers) else set()
            if needed - covered:
                err(f"questions.{qid}", f"answer cards must cover all solution blocks and criteria; missing {sorted(needed - covered)}")
        paged = [a for a in answers if isinstance(a.get("page"), dict)]
        if paged:
            if len(paged) != len(answers) or any(a["page"].get("total") != len(answers) for a in paged) or sorted(a["page"].get("index", 0) for a in paged if type(a["page"].get("index")) is int) != list(range(1, len(answers) + 1)):
                err(f"questions.{qid}", "paged answers must provide each index 1..total exactly once, with total equal to answer card count")
    return errors


def resolve_cards(data: dict) -> list[dict]:
    """Compile the sole answer source into cards without hiding any block."""
    errors = validate(data)
    if errors:
        raise ValueError("\n".join(errors))
    units = {u["id"]: u for u in data["units"]}
    questions = {q["id"]: q for q in data["questions"]}
    result = []
    for raw in data["cards"]:
        card = copy.deepcopy(raw)
        unit = units[card["unit_id"]]
        card["unit_title"] = unit["title"]
        card["objective"] = unit["objective"]
        card.setdefault("depth", "core")
        if card["type"] == "explanation":
            card.setdefault("title", unit["title"])
        else:
            question = questions[card["question_id"]]
            card["explanation_ids"] = copy.deepcopy(question["explanation_ids"])
            card.setdefault("title", question["title"])
            if card["type"] == "self_check":
                card["blocks"] = copy.deepcopy(question.get("context", [])) + [
                    {"id": "__prompt", "kind": "callout", "heading": "请用自己的话解释", "text": question["prompt"]},
                    {"id": "__instruction", "kind": "paragraph", "text": "先闭卷作答，可口述；说清结论和理由后，再看解答核对。"},
                ]
            else:
                solution = question["solution"]
                mapping = {block["id"]: block for block in solution["blocks"]}
                mapping["@criteria"] = {"id": "@criteria", "kind": "bullets", "heading": "核对要点", "items": [c["text"] + ("" if c["required"] else "（扩展）") for c in solution["criteria"]]}
                mapping["@errors"] = {"id": "@errors", "kind": "bullets", "heading": "这些说法需要修正", "items": solution["critical_errors"]}
                mapping["@variants"] = {"id": "@variants", "kind": "bullets", "heading": "可以这样表达", "items": solution["accepted_variants"]}
                card["blocks"] = [copy.deepcopy(mapping[ref]) for ref in card["solution_refs"]]
        result.append(card)
    return result


def block_markdown(block: dict) -> str:
    """Lossless readable text representation of a validated block."""
    kind = block["kind"]
    heading = f"#### {block['heading']}\n\n" if block.get("heading") else ""
    if kind in {"paragraph", "callout"}:
        body = block["text"]
    elif kind == "code":
        fence = "`" * max(3, max((len(m.group()) + 1 for m in re.finditer(r"`+", block["text"])), default=3))
        body = f"{fence}\n{block['text']}\n{fence}"
    elif kind == "bullets":
        body = "\n".join(f"- {s}" for s in block["items"])
    elif kind == "steps":
        body = "\n".join(f"{i}. **{s['label']}**：{s['text']}" for i, s in enumerate(block["items"], 1))
    elif kind == "formula":
        body = f"$$\n{block['latex']}\n$$"
    elif kind == "matrix":
        matrix = " \\\\ ".join(" & ".join(row) for row in block["cells"])
        body = "$$\n" + block.get("left_label", "") + "\\begin{bmatrix}" + matrix + "\\end{bmatrix}\n$$"
    elif kind == "table":
        escape = lambda s: s.replace("|", r"\|").replace("\n", "<br>")
        body = "\n".join("| " + " | ".join(escape(c) for c in row) + " |" for row in [block["headers"], ["---"] * len(block["headers"]), *block["rows"]])
    elif kind == "flow":
        body = "\n".join(f"- {n['id']} · **{n['label']}**" + (f"：{n['text']}" if n.get("text") else "") for n in block["nodes"])
        body += "\n\n连接：\n" + "\n".join(f"- {e['from']} → {e['to']}" + (f"：{e['label']}" if e.get("label") else "") for e in block["edges"])
    elif kind == "bar":
        body = "\n".join(f"- {label}：{value}" for label, value in zip(block["labels"], block["values"]))
    else:
        raise ValueError(f"unsupported block kind: {kind}")
    if block.get("caption"):
        body += "\n\n" + block["caption"]
    return heading + body


def export_text(data: dict, output_dir: str | Path) -> None:
    """Export readable artifacts from the same source used for rendering/grading."""
    cards = resolve_cards(data)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    draft = [f"# {data['title']}", "全部卡片文字稿；PNG 与文字使用同一份 manifest。"]
    for card in cards:
        page = card.get("page")
        suffix = f" · {page['index']}/{page['total']}" if page else ""
        draft.append(f"## {card['id']} · {card['title']}{suffix}\n\n类型：{card['type']}；单元：{card['unit_title']}；目标：{card['objective']}")
        draft.extend(block_markdown(b) for b in card["blocks"])
    (out / "transcript.md").write_text("\n\n".join(draft) + "\n", encoding="utf-8")
    answers = [f"# {data['title']} · 解答与口述核对", "按含义、关系和条件核对；不按关键词数量、逐字相似度或口述流畅程度评分。"]
    for q in data["questions"]:
        answers.append(f"## {q['id']} · {q['title']}\n\n{q['prompt']}")
        if q.get("context"):
            answers.append("### 题目背景\n\n" + "\n\n".join(block_markdown(b) for b in q["context"]))
        answers.extend(block_markdown(b) for b in q["solution"]["blocks"])
        answers.append("### 核对标准\n\n" + "\n".join(f"- {c['id']} · {'必要' if c['required'] else '扩展'}：{c['text']}" for c in q["solution"]["criteria"]))
        for field, title in (("critical_errors", "需要修正的错误"), ("accepted_variants", "可接受的表达")):
            if q["solution"][field]:
                answers.append("### " + title + "\n\n" + "\n".join("- " + s for s in q["solution"][field]))
        answers.append("补学卡：" + "、".join(q["explanation_ids"]))
    (out / "answer-key.md").write_text("\n\n".join(answers) + "\n", encoding="utf-8")
    sources = [f"# {data['title']} · 来源"]
    for source in data["sources"]:
        sources.append(f"- {source['id']} · [{source['title']}]({source['url']})" + ("：" + source["note"] if source.get("note") else ""))
    sources.append("## 单元与来源\n\n" + "\n".join(f"- {u['id']} · {u['title']}：" + "、".join(u["source_ids"]) for u in data["units"]))
    (out / "sources.md").write_text("\n\n".join(sources) + "\n", encoding="utf-8")
    review = [f"# {data['title']} · 复习与自检", "先看单元目标，闭卷口述或回答自查题，再用解答卡核对。当前仅记录“未检验（已讲待检）”，尚未根据你的实际回答判定掌握。"]
    for unit in data["units"]:
        related = [c for c in cards if c["unit_id"] == unit["id"]]
        review.append(f"## {unit['title']}\n\n目标：{unit['objective']}\n\n范围：{unit['scope']}\n\n前置：" + ("；".join(unit["prerequisites"]) or "无额外前置要求") + "\n\n卡片：" + "、".join(c["id"] for c in related))
    review.append("## 口述反馈\n\n逐项标为正确、部分正确、错误、尚未覆盖或待确认；解释依据并针对最阻塞理解的一项补讲，再用变式问题复测。看过答案后的复述属于有提示完成；新情境独立回答后才可记录当场独立通过。")
    (out / "review.md").write_text("\n\n".join(review) + "\n", encoding="utf-8")
    (out / "oral-rubric.json").write_text(json.dumps({"schema_version": 2, "title": data["title"], "questions": data["questions"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
