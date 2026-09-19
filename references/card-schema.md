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
- `explanation`: at least one of `definition`, `points`, `table`, `chart`, or `takeaway`.

Allowed card types are exactly `quick_check` and `explanation`. A table must have `headers` and `rows`; every row must have the same number of cells as the headers. A simple chart, when used, has this form:

```json
{"chart": {"kind": "bar", "labels": ["低", "中", "高"], "values": [1, 2, 3]}}
```

`chart.kind` is currently `bar`. Values must be finite non-negative numbers. Do not use chart data to imply a quantitative fact unless the user supplied the numbers or the draft clearly labels them as a qualitative scale.
