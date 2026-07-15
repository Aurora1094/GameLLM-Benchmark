# GameLLM-Benchmark

GameLLM-Benchmark 用统一的结构化 Prompt 和自动评估器，比较不同 LLM 生成单文件
`pygame` 游戏的能力。

```text
main.md + game spec
        -> Prompt 构建与快照
        -> LLM 生成单文件游戏
        -> D1 可执行性
        -> D2 功能完整性 / D3 代码质量 / D4 用户体验
        -> 本地结果与汇总
```

仓库只保存源码、配置、游戏规格、评估器和可复现实验脚本。模型输出、评分 JSON、
运行快照、图表、PDF 与打包文件均为本地产物，不提交到 Git。

## 快速开始

建议使用 Python 3.10 或更高版本：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/check_prompt_contracts.py
```

使用 AWS Bedrock 时，通过环境变量提供凭据，不要把密钥写进配置或提交记录：

```powershell
$env:AWS_ACCESS_KEY_ID = "<access-key-id>"
$env:AWS_SECRET_ACCESS_KEY = "<secret-access-key>"
$env:AWS_REGION = "us-east-1"
python run_pipeline.py
```

结果会写入 `data/raw/<run_id>/` 和 `data/scores/<run_id>/`，这些目录默认忽略。

## Prompt 架构

Prompt 由两部分组成：

- `prompts/main.md`：所有游戏共享的运行、代码质量和输出要求。
- `prompts/specs/<difficulty>/<game>.md`：窗口、颜色、完整规则和功能 checkpoint。

`prompt_builder.py` 会校验 frontmatter、尺寸、颜色、checkpoint id 和残留占位符。
最终 Prompt 只向模型暴露 checkpoint 的编号与 `desc`，内部 `id/weight` 仅供 D2 使用。

当前规格：

| 状态 | 难度 | 游戏 |
|---|---|---|
| 正式流水线，已有 D2 recipe | Easy | Pong、Snake、Flappy Bird |
| 正式流水线，已有 D2 recipe | Medium | Space Invaders |
| Prompt 与 D1/D3 demo 可用 | Medium | 2048 |
| Prompt 与 D1/D3 demo 可用 | Hard | Carrot Defense、Lode Runner-like、Farming-lite |

后四个游戏在补齐 D2 检测 recipe 前不会进入正式功能评分；若误接入会 fail-fast，
不会回退成与 spec 无关的泛化 D2 分数。

## 评估维度

| 维度 | 默认权重 | 实现 |
|---|---:|---|
| D1 Executability | `0.20` | 六级确定性流水线：语法、依赖、建窗、事件、稳定运行、可控退出 |
| D2 Functionality | `0.50` | 从同一 game spec 读取 checkpoint，按 id 对齐游戏检测 recipe |
| D3 Code Quality | `0.15` | AST/静态工具评估复杂度、复用、常量、命名、模块化和注释 |
| D4 UX | `0.15` | 视觉反馈、交互、流畅度和体验证据 |

D1 同时输出连续能力分 `passed_steps / 6` 和准入闸门 `gate_pass`。统一评估入口在
`evaluator/main_evaluator.py`：只有 D1 六步全过才执行 D2-D4。

## D1/D3 Demo

`D1_D3_demo/` 提供两条可复现路径：

```powershell
# 真实模型：默认 Pong，也可通过 --spec 切换游戏
python D1_D3_demo/run_demo.py
python D1_D3_demo/run_demo.py --spec prompts/specs/easy/snake.md

# 评分器校准：受控 D1 阶梯与 D3 定向退化样例
python D1_D3_demo/run_calibration.py --check --repeat 3 --runtime-sec 3
```

真实生成与校准结果分别写入 `D1_D3_demo/runs/` 和 `D1_D3_demo/results/`，均不提交。
详细证据结构和报告构建方法见 `D1_D3_demo/README.md`。

## 目录

| 路径 | 职责 |
|---|---|
| `config/` | 正式游戏、模型和评分权重 |
| `prompts/` | Prompt 总骨架、spec schema 和游戏规格 |
| `llm_clients/` | Bedrock、OpenAI、Anthropic、Qwen、Gemini 客户端 |
| `evaluator/` | D1-D4 自动评估实现 |
| `evaluation/` | 评分口径与游戏检测端口文档 |
| `D1_D3_demo/` | 真实生成、校准 fixtures 和报告源码 |
| `scripts/` | Prompt 校验、规格导入、重复实验和可视化 |
| `data/` | 本地模型代码与评分输出，仅保留 `.gitkeep` |
| `analysis/figures/` | 本地分析图表，仅保留 `.gitkeep` |

更完整的数据流和清理边界见 `docs/project_structure.md`。

## 常用命令

```powershell
python scripts/check_prompt_contracts.py
python run_pipeline.py
python show_results.py
python print_full_results.py --run <run_id>
python scripts/run_repeated.py --times 5 --plot
python scripts/visualize_results.py --run <run_id>
```
