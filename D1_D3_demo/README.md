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

## 维度内容与评分准则

### D1：可执行性六级流水线

D1 复用正式评估器，回答“生成的 pygame 程序能否被实际启动、维持运行并受控退出”。
六级检查存在先后依赖，不是六个可任意相加的特征：前一级失败时，后续依赖步骤不能被
视为已通过。

| 级别 | 检查内容 | 判定方式 |
|---:|---|---|
| 1 | Python 语法正确 | 解析源码，确认不存在 `SyntaxError` |
| 2 | 依赖初始化完成 | 在评测环境中成功导入并初始化 pygame |
| 3 | 创建显示窗口 | 检测 `pygame.display.set_mode` 返回有效 Surface |
| 4 | 存在事件处理 | 检测 `pygame.event.get/poll` 等事件读取结构 |
| 5 | 短时运行稳定 | 在 dummy SDL 子进程中运行指定时间，无崩溃或提前退出 |
| 6 | 进程可控退出 | 注入 QUIT 事件后在超时内干净退出 |

D1 输出 `pipeline_steps_passed`（0--6）和 `gate_pass`。只有达到 6/6 才打开最终得分闸门；
但 D1 失败不会阻止 D3 诊断测量。

### D3-v2：源码内部质量

D3-v2 诊断分由 85 分确定性工具层和 15 分匿名语义层组成：

$$
S_{D3}=S_M+S_R+S_S+S_E+S_P+S_J.
$$

| 子项 | 符号 | 分值 | 主要证据 |
|---|---:|---:|---|
| 可维护性与结构 | `S_M` | 30 | Radon 圈复杂度、Ruff 结构规则、AST 重复、导入安全 |
| 可靠性与缺陷风险 | `S_R` | 20 | Ruff 缺陷规则、宽泛异常和异常吞噬 |
| 安全与任务约束 | `S_S` | 15 | Bandit、禁用调用、任务外部依赖 |
| 效率与资源纪律 | `S_E` | 10 | Ruff PERF、循环内文件和 pygame 资源加载 |
| Python 规范与可读性 | `S_P` | 10 | Ruff 规范问题密度 |
| 三模型语义评审 | `S_J` | 15 | 匿名 Nova、DeepSeek、Qwen Judge |

完整公式、Judge 当前证据状态和参考文献对应关系另见
[`docs/D3_V2_SCORING.md`](docs/D3_V2_SCORING.md)。以下是代码中实际执行的评分合同。

#### 1. 可维护性与结构：30分

由圈复杂度 12 分、结构问题 8 分、重复结构 5 分和可测试性 5 分组成。

- 圈复杂度：Radon 等级映射为 A=1、B=0.8、C=0.5、D=0.25、E/F=0。若各函数映射值
  为 `r_i`，则 `S_CC = 12 × [0.1 × mean(r_i) + 0.9 × min(r_i)]`。最复杂函数占
  90% 权重，避免大量简单 helper 稀释一个复杂主循环。
- 结构问题：`C901`、`PLR0904`、`PLR0911`--`PLR0917` 每条扣 1.5 分，最低 0 分。
- 重复结构：在模块、函数和类体内比较连续 6 条规范化 AST 语句；每个重复窗口除首次外
  每次扣 1 分，最低 0 分。
- 可测试性：存在 `if __name__ == "__main__"` 得 2 分；dummy SDL 下可安全 import
  得 2 分；模块顶层可执行语句不超过 3 条得 1 分。

Radon Maintainability Index 只记录，不计分。函数数量、魔法数字、注释数量和注释密度
不再直接参与评分。

#### 2. 可靠性与缺陷风险：20分

从 20 分向下扣：

- `F821/F822/F823/B012` 每条扣 5 分；
- `B006/B008/B023/BLE001/E722/TRY201/TRY203` 每条扣 2 分；
- 其他选中的 `B/BLE/PLE/PLW/TRY` 问题每条扣 1 分；
- 裸 `except` 或捕获 `Exception/BaseException` 每个扣 1 分；若处理器仅包含
  `pass/continue`，每个再扣 2 分；AST 异常处理扣分合计最多 4 分。

最终为 `max(0, 20 - Ruff扣分 - AST异常扣分)`。

#### 3. 安全与任务约束：15分

Bandit 每条问题的扣分为“严重度权重 × 置信度系数”：

- 严重度：HIGH=6、MEDIUM=3、LOW=1；
- 置信度：HIGH=1、MEDIUM=0.75、LOW=0.5。

出现任一禁用调用类别额外扣 15 分；出现非标准库且非 pygame 的任务外部依赖再扣
15 分。禁用调用包括 `eval`、`exec`、`compile`、`os.system`、`os.popen`、
`subprocess`、`socket`、`requests` 和 `urllib.request`。

禁用调用、任务外部依赖或 Bandit HIGH+HIGH 问题都会设置
`critical_security_risk=true`，并将整个 D3 诊断分封顶为 50。Bandit HIGH+HIGH 本身
不一定单独把安全子项扣到 0。

#### 4. 效率与资源纪律：10分

- Ruff `PERF` 问题每条扣 1 分，最多扣 4 分；
- `for/while` 循环内每个唯一“调用名+行号”的资源加载扣 2 分，最多扣 6 分；
- 检查 `open`、字体、图片、声音加载和上述安全禁用调用。

该项只检测单文件 pygame 中常见的逐帧 I/O 和重复资源加载，不替代真实 FPS、运行时间、
内存峰值或算法复杂度 benchmark。

#### 5. Python规范与可读性：10分

计入 Ruff 的 `E/W/I/N/UP/SIM` 以及 `F401/F841`。`I/UP/SIM` 每条权重 0.5，其他
每条权重 1。以 Radon 逻辑代码行 `LLOC` 归一化：

```text
density = 100 × 加权问题数 / max(1, LLOC)
S_P = 10 × max(0, 1 - density / 10)
```

即每 100 个逻辑行达到 10 个加权问题时，该项为 0。

#### 6. 三模型匿名Judge：15分

固定 Judge 为 `amazon.nova-pro-v1:0`、`deepseek.v3.2`、
`qwen.qwen3-coder-next`，温度为 0。三者只看到匿名源码，看不到候选模型名称、D1、工具
分数或其他 Judge 输出。

| Judge 子项 | 分值 |
|---|---:|
| 职责与抽象 | 5 |
| 语义可读性 | 4 |
| 注释有效性 | 3 |
| 可修改/可测试性 | 3 |

Judge 必须返回严格 JSON，并为每项提供非空理由和有效源码行号。单个 Judge 最多重试
2 次；至少 2 个 Judge 有效才计分，`S_J` 为有效总分的等权平均。极差大于 4 分标记
`high_disagreement`；只有 2 个 Judge 有效时状态为 `panel_degraded`，但仍可形成总分。

### D1闸门与结果状态

D3 诊断分和门控最终分必须同时报告：

```text
D1 = 6/6  → d1_gated_final = D3诊断分
D1 < 6/6  → d1_gated_final = 0，但D3诊断分仍保留
```

| 状态 | 含义 |
|---|---|
| `completed` | 工具完整且三个 Judge 均有效 |
| `panel_degraded` | 工具完整，只有两个 Judge 有效，仍形成 D3 分数 |
| `incomplete_judge` | 有效 Judge 少于两个，不形成 100 分制总分 |
| `tools_only` | 只完成 85 分工具层，仅用于调试，不进入正式报告 |
| `incomplete_tooling` | 工具缺失、失败或版本不符，不允许 AST fallback |
| `invalid_input` | 文件不存在或语法无法解析 |

正式排行只使用 `origin=llm_api`、D3 schema v2、工具完整且至少两个 Judge 有效的 run。

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
