# prompt_builder 契约（Codex 实现任务书）

目标：读 `main.md` 骨架 + 对应 `specs/<difficulty>/<game>.md`，渲染出
最终 prompt。骨架是不变量，spec 是唯一变量。

## 输入
- `main.md`：唯一骨架，含占位符。
- `specs/<difficulty>/<game>.md`：YAML frontmatter（见 SCHEMA.md）+ 可选自由文本。

## 处理步骤
1. 解析 spec 的 frontmatter 与自由文本正文。
2. 组装占位符值：
   - `{game_name}` ← `game_name`
   - `{window_size}` ← 由 `params.window_size` 格式化为 `"800x600"`
   - `{player_color}` ← `params.player_color`
   - `{round_time_sec}` ← `params.round_time_sec`
   - `{game_description}` ← spec 正文自由文本（无则空串，但需正文存在性校验）
   - `{checkpoints_rendered}` ← `checkpoints[].desc` 渲染成编号多行清单
     （仅 desc，不含 id / weight）
3. 用值替换 main.md 中的占位符，得到最终 prompt。

## 硬性契约（务必实现，直接影响基准效度）
1. **占位符缺值 = 报错退出**，禁止静默留空。
   否则某游戏漏 checkpoint 会生成残缺 prompt，模型因"未被告知"而低分，
   却被误读为模型能力不足 —— 污染分数归因。
2. **骨架不变量**：同一难度下所有游戏、所有模型，替换前的 main.md 必须
   逐字节一致。builder 不得按游戏/模型改写骨架文案。
   （依据：Sclar et al. 2024，保义的格式扰动即可造成巨大分数漂移。）
3. **落盘留档**：把每个 (game[, model]) 渲染后的**最终 prompt 原文**写入
   该次 run 的产物目录（如 `runs/<run_id>/prompts/<game>.txt`）。
   分数必须能对着真实用过的 prompt 复核；main.md 改版后也能追溯版本。
4. **单一真源接线**：`evaluator/dimension2_functionality` 从**同一个 spec 文件**
   读 `checkpoints`（按 `id` 对齐打分），不得另建功能清单。

## 校验（builder 启动时做，fail-fast）
- frontmatter 必填字段齐全、类型正确（见 SCHEMA.md）。
- `window_size` 为两个正整数；`checkpoints` 非空且 id 本文件内唯一。
- main.md 中出现的每个占位符都能在组装出的值里找到对应键。
- 组装完成后扫一遍最终 prompt，确认无残留 `{...}` 占位符。

## 建议接口（示意，Codex 可按现有代码风格调整）
```python
def build_prompt(main_path: str, spec_path: str) -> str:
    """渲染最终 prompt。任一占位符缺值抛异常。"""

def load_checkpoints(spec_path: str) -> list[dict]:
    """给 D2 评估器复用的同源读取，返回 [{id, desc, weight}, ...]。"""
```
两个函数读同一个 spec 文件，是"单一真源"的落地点。
