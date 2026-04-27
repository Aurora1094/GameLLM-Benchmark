# GameLLM-Benchmark

## GameUIBench（重构版）

本仓库已按“游戏任务 → Prompt 生成 → 沙箱执行 → 维度评分 → 结果汇总”的链条整理。

## 1. 你最关心的四个位置

- **Prompts 放哪**：`prompts/`（建议路径：`prompts/<difficulty>/<game>/prompt.txt`）
- **在哪运行**：项目根目录运行 `python run_pipeline.py`
- **结果放哪**：
	- 原始产物：`results/raw/`（代码、日志、截图、逐样本明细）
	- 处理后结果：`results/processed/`（汇总表、排行榜、统计）
- **打分标准放哪**：
	- 评分规则与测试规范：`evaluation/`
	- 评估实现代码：`evaluator/`
	- 权重/策略配置：`config/scoring_policy_minimal.yaml`、`config/weights.yaml`

## 2. 目录职责（简版）

- `games/`：基准任务本体（按 easy / medium / hard 分层）
- `prompts/`：每个任务对应的提示词模板
- `llm_clients/`：不同模型厂商的调用适配
- `sandbox/`：安全执行生成代码
- `evaluator/`：四维评分 + 能力映射
- `evaluation/`：评分标准、rubric、测试规范（“规则定义层”）
- `results/`：实验输出（raw/processed）
- `config/`：实验矩阵、模型、权重、运行方案
- `run_pipeline.py`：一键实验入口

## 3. 一套完整流程怎么算

1. 在 `games/<difficulty>/<game>/spec.md` 定义任务需求（功能点、约束、判定口径）
2. 在 `prompts/<difficulty>/<game>/prompt.txt` 写该任务 Prompt
3. `run_pipeline.py` 调用 `llm_clients/` 生成代码
4. 生成代码交给 `sandbox/runner.py` 安全执行并采集原始信号
5. `evaluator/main_evaluator.py` 聚合四维得分：
	 - D1 可执行性（`evaluator/dimension1_executable.py`）
	 - D2 功能正确性（`evaluator/dimension2_functionality/`）
	 - D3 代码质量（`evaluator/dimension3_code_quality.py`）
	 - D4 体验与交互（`evaluator/dimension4_ux.py`）
6. `ability_mapper.py` 将功能得分映射到能力维度（创新点）
7. 写入 `results/raw/` 和 `results/processed/`

## 4. 当前重构说明

- 已重命名：`benchmarks/ -> games/`
- 已新增：`evaluator/`、根级 `sandbox/`、根级 `run_pipeline.py`、`config.py`
- 已整理：`results/` 改为 `raw/` + `processed/`
- 已删除：`paper/`、旧 `runner/`（空骨架，避免链路混乱）
