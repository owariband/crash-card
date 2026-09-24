# Card manifest schema

The renderer consumes one JSON manifest. The schema is intentionally small so the model can author it reliably and a human can edit it.

```json
{
  "title": "事务并行问题速记",
  "topics": ["隔离级别", "并行事务问题"],
  "caption": "一组用来快速回忆事务隔离与并行问题的秋招速记卡。",
  "dimensions": {"width": 1080, "height": 1350},
  "cards": [
    {
      "id": "qc-001",
      "type": "quick_check",
      "title": "隔离级别解决什么问题？",
      "prompt": "从低到高填写四种隔离级别，并写出它们主要避免的问题。",
      "blanks": ["____", "____"],
      "answer_key": ["读未提交、读已提交、可重复读、串行化", "脏读、不可重复读、幻读"],
      "tags": ["数据库", "面试高频"]
    },
    {
      "id": "ex-001",
      "type": "explanation",
      "title": "三类并行事务问题",
      "definition": "多个事务交错执行时，一个事务可能读到另一个事务不同阶段的数据。",
      "points": [
        {"label": "脏读", "text": "读到了尚未提交、后来可能回滚的数据。"},
        {"label": "不可重复读", "text": "同一事务两次读取同一行，结果不同。"},
        {"label": "幻读", "text": "同一条件两次查询，行集合发生变化。"}
      ],
      "table": {
        "headers": ["问题", "核心含义", "常见控制方式"],
        "rows": [
          ["脏读", "读到未提交数据", "读已提交及以上"]
        ]
      },
      "takeaway": "隔离级别越高，并发可见性越保守，通常吞吐和并发度也会下降。",
      "tags": ["数据库", "并发"]
    }
  ]
}
```

Required fields:

- Manifest: `title`, `topics`, `caption`, `dimensions`, `cards`.
- Every card: `id`, `type`, `title`.
- `quick_check`: `prompt`, `blanks`, and `answer_key`; `blanks` and `answer_key` must both be non-empty arrays.
- Each quick-check answer must be a non-empty string; the two arrays must have equal lengths. The validator permits at most 6 blanks. For consistent SVG/PNG content, prefer at most 5 (normally 1 for an open explanation question).
- `explanation`: at least one of `definition`, `points`, `table`, `chart`, or `takeaway`.

`points` supports at most 5 items in the validator; prefer at most 4 for SVG/PNG consistency. These are compatibility limits, not a target density. Split crowded cards instead of filling every available slot.

Allowed card types are exactly `quick_check` and `explanation`. A table must have `headers` and `rows`; every row must have the same number of cells as the headers. A simple chart, when used, has this form:

```json
{"chart": {"kind": "bar", "labels": ["低", "中", "高"], "values": [1, 2, 3]}}
```

`chart.kind` is currently `bar`. Values must be finite non-negative numbers. Do not use chart data to imply a quantitative fact unless the user supplied the numbers or the draft clearly labels them as a qualitative scale.

## Feynman-style open questions without a schema change

The `quick_check` type supports an open response: place the question in `prompt`, use a short neutral response label in `blanks`, and keep the complete reference answer in the corresponding `answer_key` string. The current badge may still say “快速填空”; the image is static, not an editable form or flip card.

```json
{
  "id": "qc-mean-why",
  "type": "quick_check",
  "title": "平均数的算法为什么成立？",
  "prompt": "请向第一次学平均数的人解释：为什么把总和除以个数，就得到了每份一样多时的数值？",
  "blanks": ["写下你的解释"],
  "answer_key": ["平均分配不改变总量。设每份为 m，共 n 份，总和为 S，则 n×m=S，所以 m=S÷n；数据个数 n 必须大于零。"],
  "tags": ["算术平均数", "机制解释"]
}
```

This example tests the reason for a stated algorithm. If the target is recalling the algorithm itself, omit that formula from the prompt. Neutral response labels such as “说明理由” or “写出判断” should not contain key answer concepts. One response slot may contain multiple required semantic checkpoints in its answer string; it still counts as one task.

The manifest is the answer source of truth. For companion Markdown formats and learning records, follow [workflow.md](workflow.md#交付与复习包). The renderer only generates card images and SVG sources; the assistant authors the companion files.

Do not invent fields such as `rubric`, `review_state`, `back` or new card types and assume they will render. `tags` is metadata, not a visible progress display. Keep the existing manifest contract and place learning records in the companion Markdown files.

## Validation and layout boundaries

- `validate_manifest.py` checks full answer strings against visible `title`, `prompt` and `blanks`. It does not detect paraphrased or partial answer leakage. Inspect all visible content semantically; simple answers such as a digit can also accidentally match a title, so use a neutral title and keep numbering in the ID when needed.
- Answers are not rendered on quick-check cards, but remain readable in `manifest.json`. Explanation images may reveal them. Deliver these groups separately, and label the independent answer file clearly.
- The renderer limits the number of lines and items and can truncate long content. SVG and PNG adapters have different limits; SVG is an inspection source, not proof of identical visible content. Inspect every requested PNG after rendering; split overflowing cards, update the manifest and answer mapping, then render again.
- `validate_outputs.py` checks PNG existence, signature, dimensions and unexpected PNG files. It does not check language, factual correctness, clipping or answer leakage.
- The transaction examples above illustrate the file structure. For actual technical cards, verify the relevant database/standard/version before treating isolation behavior or performance trade-offs as unconditional facts.
