# D1 / D3-v2 Demo

本目录先行验证新的 D3 方法，不修改正式 `run_pipeline.py`、共享
`evaluator/dimension3`、根级生成 Prompt 或正式 D1–D4 评分。Demo 的 D3 schema v2
与正式流水线旧 D3 不能直接比较，也不能混合排行。

运行链如下：

```text
真实 LLM 生成代码
  → 正式 D1 六级测量
  → Demo-local Ruff / Radon / Bandit / AST
  → Nova / DeepSeek / Qwen 匿名 Judge
  → D3-v2 诊断分
  → 应用 D1 闸门得到最终分
```

## 安装固定工具

```powershell
python -m pip install -r D1_D3_demo/requirements-d3-v2.txt
```

版本固定为 Ruff 0.15.22、Radon 6.0.1、Bandit 1.9.4。缺失或版本不一致时返回
`incomplete_tooling`，不会使用 AST fallback 伪造分数。

## D3-v2 分数

完整评分公式、Judge 当前证据状态与参考文献对应关系见
[`docs/D3_V2_SCORING.md`](docs/D3_V2_SCORING.md)。

| 子项 | 分值 |
|---|---:|
| 可维护性与结构 | 30 |
| 可靠性与缺陷风险 | 20 |
| 安全与任务约束 | 15 |
| 效率与资源纪律 | 10 |
| Python 规范与可读性 | 10 |
| 三模型语义评审 | 15 |

Radon Maintainability Index 只记录，不计分。旧版独立的魔法数字、函数数量和注释密度
分数已删除。禁用调用或任务外部依赖会令安全分归零；它们以及 Bandit 的高危高置信问题
都会将最终 D3 总分封顶为 50。Bandit 高危高置信问题本身不一定单独把安全子项扣到 0。

Judge 固定为 `amazon.nova-pro-v1:0`、`deepseek.v3.2`、
`qwen.qwen3-coder-next`，温度为 0、等权平均。Judge 看不到候选模型名称、D1 分数、
工具分数或其他 Judge 结果。至少两个 Judge 的严格 JSON 输出有效才形成总分；极差超过
4 分会记录 `high_disagreement`。

D1 与 D3 的“测量”相互独立：D1 未达到 6/6 时仍照常运行 D3 工具和 Judge，并保存
完整 D3-v2 诊断分。D1 只在最后应用总分公式；闸门关闭时
`scores.d1_gated_final.score` 为 0，原始 D3 诊断分不会被覆盖或丢失。语法本身无法解析
或工具不完整时，D3 仍会执行并明确返回 `invalid_input` 或 `incomplete_tooling`。

## 真实生成

默认仍使用现有 Pong Prompt：

```powershell
python D1_D3_demo/run_demo.py --model qwen.qwen3-coder-next
python D1_D3_demo/run_demo.py --model deepseek.v3.2
python D1_D3_demo/run_demo.py --model amazon.nova-pro-v1:0
```

也可继续使用项目统一入口。AWS 凭据只从环境或统一入口加载，不写入运行产物。没有凭据
时会保存 Prompt 和失败证据，并明确记录 `credentials_missing`。

每个新 run 位于 `D1_D3_demo/runs/<run_id>/`，主要产物包括：

- `scores/d1.json`、`scores/d3_tools.json`、`scores/d3.json`
- `prompts/d3_judge.txt`
- `judges/<model>/request.json`
- `judges/<model>/raw_response.txt`
- `judges/<model>/parsed_score.json`
- `summary.json`、`manifest.json`、`manifest.sha256`

Manifest 索引 Prompt、代码、工具结果、三份 Judge 证据和 summary 的 SHA256；sidecar
校验 manifest 本身。现有 run 不会原地修改。通过 `--model-output-file` 重评旧响应时会
建立新的 `response_replay` run，该结果不能进入正式报告。`--skip-judges` 只用于本地
工具调试，生成的 `tools_only` run 同样不具备报告资格。

## 校准

默认校准不调用 API，也不产生模型费用：

```powershell
python D1_D3_demo/run_calibration.py --check --repeat 3 --runtime-sec 3
```

它要求原有 D1 0–6 阶梯不变、所有 D3 fixtures 先通过 D1、三轮工具 JSON 哈希完全
一致、各定向缺陷的目标子项发生最大降分，并验证安全封顶、普通数字/注释数量不再导致
断崖降分以及配置/工具版本变化会改变配置哈希。非目标项的全部变化会写入降分矩阵。

显式加入付费 Judge 校准：

```powershell
python D1_D3_demo/run_calibration.py --check --repeat 3 --include-judges
```

该路径额外落盘 Judge×fixture 矩阵、均值、标准差、极差和高分歧标记。它要求当前进程
已经设置 `AWS_ACCESS_KEY_ID` 和 `AWS_SECRET_ACCESS_KEY`；缺少凭证时会在修改既有
校准产物前退出。默认 tools-only 校准与 Judge fixture 校准是两份不同的证据：前者验证
静态评分确定性，后者验证语义量表对受控缺陷的敏感性。真实候选样本仍必须包含至少两个
有效 Judge 才能进入正式 Demo 报告。

## 聚合与报告

在 `report_config.json` 的 `candidates[].run_ids` 中分别填写真实 Nova、DeepSeek、Qwen
run。然后运行：

```powershell
python D1_D3_demo/aggregate_live_runs.py
powershell -ExecutionPolicy Bypass -File D1_D3_demo/build_pdf.ps1
```

聚合器只接受 `origin=llm_api`、D3 schema v2、固定工具完整、至少两个 Judge 有效且
manifest 全部通过校验的 run。报告构建不会主动调用 Judge API，并且不读取旧 D3 六项
字段。仓库仅跟踪 `report_config.json` 引用的三份官方验证 run；其他本地 runs 仍由
`.gitignore` 排除，避免把临时或回放结果冒充正式数据。

单次生成分数不是稳定的模型能力估计。正式实验仍应扩展到多个游戏、多次独立生成，并
报告均值、标准差、分歧和 pass@k。
