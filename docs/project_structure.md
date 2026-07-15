# Project Structure

## 1. Source of Truth

| Path | Responsibility |
|---|---|
| `prompts/main.md` | 所有游戏共享的 Prompt 骨架与 D1/D3 开发要求 |
| `prompts/specs/<difficulty>/<game>.md` | 游戏规则、参数和 D2 checkpoint 单一真源 |
| `prompt_builder.py` | spec 校验、占位符渲染、Prompt 快照和 checkpoint 加载 |
| `config/games.yaml` | 正式启用游戏与 prompt-only 游戏分组 |
| `config/models.yaml` | 模型名称和 provider |
| `config/weights.yaml` | 四个维度的默认权重 |

最终 Prompt 不作为维护源提交。每次运行都由 `main.md + spec` 重新构建，并在对应
run 目录保存精确快照。

## 2. Runtime Flow

```text
config/games.yaml
        |
        v
prompts/main.md + prompts/specs/<difficulty>/<game>.md
        |
        v
prompt_builder.py -> llm_clients/* -> generated game.py
        |                                  |
        |                                  v
        +---------------------------> evaluator D1-D4
                                           |
                                           v
                              data/scores/<run_id>/
```

正式 D2 必须同时获得生成 Prompt 所用的 spec 路径。评估器从该文件读取 checkpoint id、
desc 和 weight，再按 id 选择检测 recipe。不存在 profile 或 recipe 时立即失败。

## 3. Evaluation Layers

| Path | Responsibility |
|---|---|
| `evaluator/dimension1/` | 六级确定性执行流水线与 D1 gate |
| `evaluator/dimension2_functionality/` | spec 驱动的游戏功能检测端口 |
| `evaluator/dimension3/` | 六项 AST/静态代码质量指标 |
| `evaluator/dimension4/` | 用户体验与视觉交互证据 |
| `evaluator/main_evaluator.py` | D1 gate、D2-D4 调度与总分 |
| `evaluation/` | 评分口径和检测端口说明 |

## 4. Demo

`D1_D3_demo/run_demo.py` 调用真实模型、启动生成游戏并保存可审计证据；
`run_calibration.py` 使用受控 fixtures 验证 D1 阶梯和 D3 定向响应。两条路径复用正式
Prompt builder 与正式 D1/D3 评估器，不维护复制版本。

`D1_D3_demo/docs/`、`build_pdf.ps1` 和 `build_overleaf.ps1` 是报告源码和构建脚本。
所有 `runs/`、`results/`、`build/`、`rendered/`、`tmp/` 与下载工具均为本地产物。

## 5. Generated Data

| Path | Generated content |
|---|---|
| `data/raw/<run_id>/` | 模型生成的 Python 文件 |
| `data/scores/<run_id>/` | 单任务评分与 summary |
| `analysis/figures/<run_id>/` | 图表、矩阵与 CSV |
| `D1_D3_demo/runs/<run_id>/` | Prompt、响应、代码、评分和 manifest |
| `D1_D3_demo/results/` | 校准与报告中间表 |

这些目录只保留本地数据，不进入 Git；仓库中仅用 `.gitkeep` 保留主流水线输出目录。

## 6. Validation

```powershell
python scripts/check_prompt_contracts.py
python -m py_compile prompt_builder.py run_pipeline.py D1_D3_demo/run_demo.py
python D1_D3_demo/run_calibration.py --check --repeat 3 --runtime-sec 3
```
