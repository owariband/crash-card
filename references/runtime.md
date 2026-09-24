# 本地运行与兼容路径

## v2 主路径

v2 需要 Python 3.10+，在各平台使用同一套 Python / Pillow 渲染，Matplotlib mathtext 排数学公式，fontTools 检查实际字体的字符覆盖。依赖版本由 Skill 根目录的 `requirements.txt` 固定；不依赖浏览器、联网公式服务或本机 LaTeX。中文字体需要在本机可用，检查和绘制必须使用同一字体。本轮已在 macOS 实测；Windows/Linux 使用相同 Python 路径，但本轮未在这两个平台运行，不能宣称跨平台验收通过。

先按 [output-storage.md](output-storage.md) 确定本次 `OUTPUT_DIR`，以实际读取的 Skill 目录为 `SKILL_ROOT`。两者均使用绝对路径，命令可在任意工作目录执行。先使用已有且满足依赖的 Python 环境，将解释器的绝对路径设为 `CARD_PYTHON`。缺少包时，在用户工作目录建立虚拟环境并按 requirements 安装；安装只提供运行条件，渲染过程不联网。下面的路径替换为实际值；`OUTPUT_DIR` 是已按目录规则确定的批次，不用示例路径改写持久配置：

```sh
SKILL_ROOT="/absolute/path/to/crash-card"
OUTPUT_DIR="/absolute/path/to/chosen-root/batch"
CARD_VENV="/absolute/path/to/venv"
python3 -m venv "$CARD_VENV"
CARD_PYTHON="$CARD_VENV/bin/python"
"$CARD_PYTHON" -m pip install -r "$SKILL_ROOT/requirements.txt"
"$CARD_PYTHON" "$SKILL_ROOT/scripts/check_environment.py"
"$CARD_PYTHON" "$SKILL_ROOT/scripts/validate_manifest.py" "$OUTPUT_DIR/manifest.json"
"$CARD_PYTHON" "$SKILL_ROOT/scripts/render_cards.py" "$OUTPUT_DIR/manifest.json" --output-dir "$OUTPUT_DIR"
"$CARD_PYTHON" "$SKILL_ROOT/scripts/validate_outputs.py" "$OUTPUT_DIR" --manifest "$OUTPUT_DIR/manifest.json"
```

Windows 使用虚拟环境中的 `Scripts/python.exe`；已有合适环境时直接用该解释器执行后四条。不要为制卡修改全局环境配置。

环境预检实际检查中文字符、分式、根号、上下标和 PNG 解码；manifest 校验检查字段、引用与覆盖关系。输出校验完整解码 PNG，核对尺寸、manifest/PNG 哈希、块 ID/类型/顺序、实际测量边界及文件集合。视觉与知识审查仍按 SKILL 执行，不能把成功退出当作知识正确或手机可读的证据。

v2 输出 `explanation/`、`self-check/`、`answer/` 三组 PNG，尺寸均为 1200×1600；旁侧导出 `manifest.json`、`transcript.md`、`answer-key.md`、`oral-rubric.json`、`sources.md`、`review.md` 和 `render-report.json`。v2 不生成 SVG。生成过程不判断用户掌握程度，不自动把输入语音转成文字。

## 字体、公式与溢出

字体应覆盖实际中文、标点与符号。缺字报告需要换用有覆盖的本地字体或选择准确的等价表示；不能接受方框占位。用 `--font-path` 指定常规字体，`--font-bold-path` 指定可选粗体；支持 `.ttf`、`.otf` 和 `.ttc` 的第一个 face。这两个参数也适用于环境预检。未指定参数时优先读取 `CRASH_CARD_FONT` / `CRASH_CARD_BOLD_FONT`，并兼容旧 `CRASH_FLASHCARD_FONT` / `CRASH_FLASHCARD_BOLD_FONT`，再查找系统字体。具体参数可查 `"$CARD_PYTHON" "$SKILL_ROOT/scripts/render_cards.py" --help`。

`render_cards.py --renderer auto`（默认）或 `--renderer pillow` 执行 v2；帮助中的 `swift`、`svg` 只用于 v1，v2 会明确拒绝它们。

公式字段接受 mathtext 子集，矩阵使用独立 `matrix` 区块；完整 LaTeX 环境、中文嵌在数学字符串和任意扩展命令不属于运行承诺。复杂公式先做能力样张，核对真实上下标、分式和根号；原始 LaTeX 文本不算完成的公式图片。

布局采用测量后绘制，超出容量返回卡片/区块定位。先调整内容组织或分页，重新校验再渲染；不要删除关键条件或将字缩到不可读。失败后保留可审核的 manifest 与具体原因，PNG 未齐全时明确属于未完成。

## v1 兼容与迁移

未指定 `schema_version` 或显式为 `1` 的旧 manifest 由兼容入口交给 `scripts/legacy/`。旧路径继续使用原有 Swift/AppKit、Pillow 或 SVG 适配器；旧主题保留在 `assets/theme-v1.json`。这些适配器不宣称支持新版公式、三类卡和无截断布局。

需要旧路径环境诊断时执行 `"$CARD_PYTHON" "$SKILL_ROOT/scripts/legacy/check_environment.py"`。旧 macOS PNG 路径需要 Swift/AppKit，旧 Windows/Linux Pillow 路径使用原依赖；SVG-only 不能满足 PNG 交付。

使用新文件路径显式迁移，脚本拒绝覆盖已有输出：

```sh
"$CARD_PYTHON" "$SKILL_ROOT/scripts/migrate_manifest.py" "/absolute/path/to/v1-manifest.json" --output "/absolute/path/to/v2-draft.json"
```

迁移后得到的是待审核草稿。检查并补写来源、定义、机制、必要条件、解答标准和分页，然后去掉 `migration_review_required` 标记，按 v2 流程重新校验和渲染。迁移不会自动证明旧答案充分或将固定区块变成合适的教学结构。

使用新的 v2 输出目录，避免旧 `quick-check/` PNG 与新版混淆。修改 manifest 后重新渲染再校验；报告绑定精确输入字节，不能用旧报告证明修改后的内容已经绘制。
