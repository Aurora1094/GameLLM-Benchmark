# prompts/

这里是项目和 D1/D3 demo 共用的提示词单一真源：

`main.md + specs/<difficulty>/<game>.md -> 最终模型 Prompt`

`main.md` 负责所有游戏共享的运行要求、D1/D3 开发要求和输出格式；每个 spec
负责一个游戏的完整玩法、参数和功能 checkpoint。D1/D3 demo 不再复制另一套提示词，
通过 `--spec` 直接选择这里的文件。

## 文件职责

- `main.md`：唯一的总 Prompt 骨架，同一实验条件下保持不变。
- `specs/SCHEMA.md`：spec 的字段契约与 `id/desc/weight` 边界。
- `specs/<difficulty>/<game>.md`：YAML frontmatter 加完整游戏说明。
- `builder_spec.md`：`prompt_builder.py` 的构建、校验、落盘与 D2 接线契约。
- `DESIGN_REVIEW.md`：提示词与评估维度的设计审视。
- `RELATED_WORK.md`、`references.bib`：论文写作依据。

## 当前游戏

| 难度 | spec | 规格来源 | D2 recipe |
|---|---|---|---|
| Easy | `easy/pong.md` | 原有正确示例 | 已接线 |
| Easy | `easy/snake.md` | `1. Snake 贪吃蛇 (Easy).docx` | 已接线 |
| Easy | `easy/flappy_bird.md` | `4. Flapping Bird (Easy).docx` | 已接线 |
| Medium | `medium/space_invaders.md` | `11. Space Invaders (Medium).docx` | 已接线 |
| Medium | `medium/2048.md` | `17. 2048 (Medium).docx` | 待新增检测 recipe |
| Hard | `hard/carrot_defense.md` | `23. Carrot Defense （Hard）.docx` | 待新增检测 recipe |
| Hard | `hard/lode_runner_like.md` | `24. Lode Runner-like （Hard）.docx` | 待新增检测 recipe |
| Hard | `hard/farming_lite.md` | `30. Farming-lite (Hard).docx` | 待新增检测 recipe |

所有 spec 都能用于 Prompt 生成和 D1/D3 demo。只有标记为“已接线”的游戏当前可以进入
正式 D2；其余游戏不会被伪装成已经具有 D2 能力，加入完整流水线前必须先实现同 id 的
检测 recipe。

## 构建与运行

渲染一份最终 Prompt：

```powershell
python -c "from prompt_builder import build_prompt; print(build_prompt('easy', 'snake'))"
```

让 D1/D3 demo 用指定游戏调用真实模型：

```powershell
python D1_D3_demo/run_demo.py --spec prompts/specs/easy/snake.md
python D1_D3_demo/run_demo.py --spec prompts/specs/medium/2048.md
```

从给定 DOCX 压缩包重新导入七份规格：

```powershell
python scripts/import_game_specs.py "<游戏规格说明.zip>"
```

## 不可违反的边界

1. Prompt 只渲染 checkpoint 的编号和 `desc`，绝不暴露 `id` 或 `weight`。
2. D2 从同一份 spec 读取 checkpoint，并按 `id` 对齐检测 recipe；缺 recipe 立即报错。
3. D3 的六项开发要求按评估顺序完整出现，但不向模型泄漏分值、阈值或检测实现。
