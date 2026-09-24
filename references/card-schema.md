# v2 manifest：同源知识、题目与解答

新卡包使用 `schema_version: 2`，画布固定 1200×1600。校验的事实来源是 `scripts/v2_contract.py`；字段与块类型严格检查，未定义字段不能假定会显示。运行与 v1 迁移见 [runtime.md](runtime.md)。

## 顶层与引用关系

| 字段 | 内容 |
|---|---|
| `schema_version` | 数字 `2` |
| `title` | 卡包名称，同时作为卡面右上系列标签；宜简短、中性，过长时标签省略 |
| `dimensions` | `{"width":1200,"height":1600}` |
| `units` | 单元：`id`, `title`, `objective`, `scope`, `prerequisites` 字符串数组，`source_ids` |
| `sources` | 来源：`id`, `title`, `url`，可选 `note` |
| `questions` | 题目与同源解答，结构见下 |
| `cards` | 用途、版式及内容引用，结构见下 |

所有 ID 使用 1–64 个 ASCII 字母、数字、点、下划线或连字符，并以字母或数字开头。`sources` 至少一项且 URL 为 HTTP(S)；每个单元至少引用一个来源、拥有一张讲解和一道题。

单元的 `objective` 写可检验的能力；`scope` 写必要范围、版本和假设。`source_ids` 引用来源 ID。来源用于追溯关键结论，脚本不验证网页内容或事实正确性。

一个题目对应一个单元，可以关联多张讲解卡；其自查卡与解答卡都引用同一 `question_id`。解答的内容保存在该题 `solution` 中，由渲染器与文字稿共同使用；口述核对直接读同一标准。

## 题目与 solution

```json
{
  "id": "q-mean",
  "unit_id": "u-mean",
  "title": "平均分配为什么这样算？",
  "prompt": "向第一次学平均数的人解释：为什么把总量除以份数，就得到每份一样多时的数量？",
  "explanation_ids": ["ex-mean"],
  "solution": {
    "blocks": [
      {"id":"result","kind":"paragraph","heading":"最短充分答案","text":"平均分配保持总量不变。每份的量乘以份数必须等于总量，所以每份的量等于总量除以份数；份数必须大于零。"},
      {"id":"reason","kind":"formula","latex":"n m = S \\quad \\Rightarrow \\quad m=\\frac{S}{n},\\quad n>0","caption":"S 是总量，n 是份数，m 是每份的量。"}
    ],
    "criteria": [
      {"id":"c-total","text":"解释平均分配保持总量不变。","required":true},
      {"id":"c-equal","text":"连起每份量×份数=总量与除法的关系，并说明份数大于零。","required":true}
    ],
    "critical_errors": ["认为平均分配后总量可以改变。"],
    "accepted_variants": ["用等分后加回原总量来解释，含义成立即可。"]
  }
}
```

`context` 可选，为题目已知条件区块数组，显示在自查卡上。只放已知数据、公式或情境，不放正在考查的结论。`prompt` 是主要任务，`title` 应帮助定位且不泄漏目标答案。

`solution.blocks` 保存完整参考解答；每个块有稳定 ID。`criteria` 保存语义核对点，至少一个为必需；`required` 区分必需与拓展。`critical_errors` 标识不能被其他答对项抵消的矛盾；`accepted_variants` 提供合理表达示例，而非穷举答案白名单。

题目可给公式来考原因，也可不给公式来考回忆。结构校验无法判断这类教学目标匹配或语义泄漏，Agent 须另行核对。

## 三类卡片

所有卡有 `id`、`type`、`unit_id`、`layout`。可用 `title` 指定标题，`depth` 标为 `core` 或 `deep`；连续卡用 `page: {"index":1,"total":2}` 等显式标记。无 page 或 total=1 时卡面页码留空；内部 ID 不显示在卡面。`layout` 是阅读结构，不改变题答数据来源。省略标题时，讲解使用单元标题，自查和解答使用题目标题。

| `type` | 内容来源 | 额外字段 |
|---|---|---|
| `explanation` | 卡内 `blocks` | `blocks` 为语义区块数组 |
| `self_check` | 指向题目的标题、prompt 与 context | `question_id` |
| `answer` | 指向题目的 solution | `question_id`, `solution_refs` |

可选 `layout`：`concept`、`formula`、`process`、`comparison`、`worked_example`、`misconception`，以及自查/答案的通用布局 `question`、`answer`。按结构选择主体版式；无需每个包覆盖全部选项。

解答卡引用示例：

```json
{
  "id":"ans-mean-01",
  "type":"answer",
  "unit_id":"u-mean",
  "question_id":"q-mean",
  "layout":"formula",
  "solution_refs":["result","reason","@criteria","@variants"]
}
```

`solution_refs` 中普通 ID 引用 `solution.blocks`；特殊引用 `@criteria`、`@errors`、`@variants` 分别编译核对标准、关键错误、合理表达。`@errors` 与 `@variants` 仅在对应列表非空时引用。可把解答分到多卡，但整个解答集合必须覆盖所有 solution 正文块及 `@criteria`。若使用页次，同题所有解答必须完整编号为 1 到总页数。不得在卡片上复制第二份可独立修改的答案正文。

解答完整不代表每张都能排下。按完整子问题分配引用，标明页次；渲染器遇到溢出会报错，不自动删除尾部内容。

## 语义区块

每块都要 `id`、`kind`；可加 `heading`。普通块 ID 不以 `@` 或 `__` 开头，以免与生成区块冲突。下表列各 kind 的内容字段；精确可选字段以校验器为准。

| `kind` | 内容字段 | 用途与边界 |
|---|---|---|
| `paragraph` | `text` | 连贯解释；可含多句完整因果链 |
| `callout` | `text`, 可选 `tone` 为 `key` / `caution` | 关键结论或条件，不将必要前提藏成小注释 |
| `bullets` | `items: [字符串]` | 真正并列内容，数量由内容和容量决定 |
| `formula` | `latex`, 可选 `caption` | mathtext 子集，实际排出分式、根号和上下标 |
| `matrix` | `cells: [[LaTeX 字符串]]`, 可选 `left_label`, `caption` | 等列数矩阵，用独立矩阵布局，不写 LaTeX 环境 |
| `table` | `headers`, `rows`, 可选 `widths` | 每行与表头等列；列宽用于分配相对空间 |
| `flow` | `nodes`, `edges` | 有限分支 DAG，节点 `id,label,text?`，边 `from,to,label?` |
| `steps` | `items: [{label,text}]` | 步骤与理由；不限制成四步 |
| `code` | `text` | 代码或 SQL，保持有意义的换行 |
| `bar` | `labels`, `values`, `caption` | 有依据的数值或清楚标注的示意；不虚构测量数据 |

`latex` 是 JSON 字符串，反斜杠需写为 `\\`，不再套 `$...$`。mathtext 不是完整 LaTeX；中文含义放 caption 或相邻正文，矩阵放 `matrix`。在渲染前试排实际表达式，无法支持时做含义等价的表达调整。

流程节点和边必须有有效引用且无环，分支标签说明条件，必要的图注可放相邻段落。复杂循环改用步骤/状态说明或分卡，不删边伪造可渲染的流程。块类型的支持不承诺任意尺寸都能容纳；布局预检负责报告具体卡片和块。

## 导出与学习记录

渲染导出三组 PNG、manifest、`transcript.md`、`answer-key.md`、`oral-rubric.json`、`review.md`、`sources.md` 与 `render-report.json`。核对稿与口述标准都从同一 solution 导出。输出校验完整解码 PNG，核对尺寸、哈希、引用后块 ID/类型/顺序、测量边界及文件集合；关键事实、语言质量、实际可读性仍由 Agent 检查。

通用卡包不保存用户的个人评分。口述时按 solution 标准评价，单独维护 `learning-log.md`；记录的口述状态和 PNG 是否生成是两个不同事实。

## v1 迁移

未指定 `schema_version` 或显式为 `1` 的旧 manifest 继续由 legacy 路径处理，旧 quick_check 与 explanation 数据保留可读。迁移工具将旧答案提取为 solution 并增加解答卡，但不能自动补齐事实核验、充分理由、语义标准和合理分页。

迁移结果带 `migration_review_required: true` 时禁止当成已审核成品渲染。Agent 完成内容、来源、题答关系及版式审核，补齐遗漏后才能去掉标记再校验。结构可转换不等于教学内容已无损升级。
