---
name: crash-flashcard
description: Create concise Chinese autumn-recruiting knowledge flashcards from a user's requirements and self-explanation. Identify and correct the knowledge first, present a reviewable draft, and render confirmed content as separate quick-check or explanation PNG cards with a short social caption.
metadata:
  short-description: 秋招知识点速记卡片生成与 PNG 渲染
---

# Crash Flashcard

This skill turns a short content request or a long spoken explanation into a compact, reviewable set of Chinese study cards. The workflow is stateful:

`RECEIVE → PARSE → KNOWLEDGE_CHECK → DRAFT → WAIT_CONFIRM → RENDER → VALIDATE → DELIVER`

## Operating rules

1. Parse two inputs separately when both are present:
   - `request`: what the user wants included and how concise it should be.
   - `attempt`: the user's current explanation or understanding.
2. When `attempt` is a long oral explanation, identify the underlying knowledge point before drafting. Give a concrete judgement for each claim: `正确`, `部分正确`, `错误`, or `无法判断`. Explain the correction briefly and write a corrected baseline. Do not silently rewrite a misconception.
3. Produce a text draft first. The draft must contain the knowledge baseline, card plan, proposed short caption, and any assumptions. Stop and wait for an explicit confirmation such as `确认`, `生成`, `开始制作`, or an equivalent instruction. A request to revise the draft returns to `DRAFT`.
4. Render only after confirmation. Never infer confirmation from a request that merely asks for a draft or asks what the cards might look like.
5. Keep the two card modes separate. A single PNG has exactly one `type`; batches are written to separate `quick-check/` and `explanation/` directories. Do not put a fill-in exercise and a teaching explanation on the same card.
6. Use the user's requested facts as the source of truth for scope. If a technical claim is uncertain, label it and ask for a source or leave it as `无法判断`; do not invent statistics, citations, or interview experience.
7. Keep each card information-dense but scannable. Prefer short lines, tables, and simple relationship diagrams only when they make the knowledge easier to recall. Do not add decoration that competes with the content.

## Draft format

Use this structure in the response:

```text
【识别的知识点】...
【对原述的判断】
- 原述：...
  判断：正确 / 部分正确 / 错误 / 无法判断
  说明：...
【纠正后的知识基线】...
【卡片草稿】
- quick_check/001: 标题；题干；填空数；答案（仅草稿展示）
- explanation/001: 标题；定义；核心关系；例子或易错点
【简介文案草稿】...
【待确认假设】...
```

If the user only supplies a concise topic request, omit the oral-explanation judgement section and state that no self-explanation was provided.

## Card modes

Read [references/card-schema.md](references/card-schema.md) before building the manifest.

- `quick_check`: a self-test card. Show a question, short prompt, and one or more blanks. Keep answers in the manifest's `answer_key`; never leak them into the rendered card. Use for definitions, contrasts, mappings, and interview recall.
- `explanation`: a compact teaching card. Use a definition, core relation, example, and/or common mistake. Use a table or a simple bar/flow diagram only when it improves recall.

Default to 1080×1350 px, 4:5 portrait PNG, with a light background, high contrast text, generous margins, and a small footer label. Respect an explicit platform or dimension request.

## Rendering workflow

After confirmation:

1. Create a manifest that follows [references/card-schema.md](references/card-schema.md). Keep raw user prose out of the rendered card unless it is explicitly requested.
2. Run `python3 scripts/validate_manifest.py path/to/manifest.json`.
3. Run `python3 scripts/render_cards.py path/to/manifest.json --output-dir path/to/output`. The renderer writes SVG source beside each PNG so the result remains inspectable and editable. On macOS it uses the local Swift/AppKit rasterizer and never downloads a renderer.
4. Run `python3 scripts/validate_outputs.py path/to/output --manifest path/to/manifest.json`.
5. Deliver the PNGs, `intro.md`, and `manifest.json`. Mention any cards that could only be emitted as SVG because a local raster converter was unavailable.

The scripts are deterministic helpers. Do not automatically install Python, Node, browser, fonts, or third-party packages. If Swift/AppKit is missing, report the exact command that failed and retain the inspectable SVG; the PNG render is then incomplete and must not be presented as finished.

## Completion criteria

The task is complete only when the draft was explicitly confirmed, every manifest card passed schema checks, each rendered card has the requested dimensions and a non-empty file, quick-check answers are absent from card text, explanation cards contain no unresolved placeholders, and the caption matches the requested topics.
