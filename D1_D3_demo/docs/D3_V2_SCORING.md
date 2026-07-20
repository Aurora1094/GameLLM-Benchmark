# D3-v2 评分准则、Judge 状态与设计依据

## 1. Judge 到底有没有测试

需要区分两类测试：

1. **真实候选样本评审已经运行。** 三个正式样本都调用了匿名 Judge 组：Nova 样本有 3 个有效 Judge，DeepSeek 样本有 3 个，Qwen 样本有 2 个，因此三个样本都形成了 D3-v2 诊断分。Qwen 的第三个 Judge 失败，所以状态是 `panel_degraded`，但仍满足“至少两个有效 Judge”的规则。
2. **受控 fixture 的 Judge 校准默认不运行。** 默认命令 `--check --repeat 3`只验证 85 分工具层的三轮确定性，避免把不能保证逐字节稳定的模型响应放入“JSON 哈希完全一致”断言，也避免每次构建报告都产生至少 8×3=24 次付费调用。只有显式加入 `--include-judges` 才会运行 Judge×fixture 校准矩阵。

本次尝试运行完整 Judge fixture 校准时，当前进程没有 `AWS_ACCESS_KEY_ID` 和 `AWS_SECRET_ACCESS_KEY`，24 个裁判调用均在请求前失败，因此**不能声称 Judge fixture 校准已经完成**。现在校准入口增加了凭证预检：缺少凭证时在写入任何结果前退出并保留现有校准产物。

因此当前证据等级是：Judge 调用链、匿名化、解析、聚合和正式样本评审已有真实 API 证据；Judge 对定向 fixtures 的敏感性矩阵尚缺有效凭证下的一次完整实验。

## 2. 总分、状态与 D1 闸门

D3-v2 的诊断分为：

\[
S_{D3}=S_M+S_R+S_S+S_E+S_P+S_J,
\]

其中工具层最高 85 分，匿名 Judge 层最高 15 分：

| 子项 | 符号 | 满分 |
|---|---:|---:|
| 可维护性与结构 | `S_M` | 30 |
| 可靠性与缺陷风险 | `S_R` | 20 |
| 安全与任务约束 | `S_S` | 15 |
| 效率与资源纪律 | `S_E` | 10 |
| Python 规范与可读性 | `S_P` | 10 |
| 三模型语义评审 | `S_J` | 15 |

D1 与 D3 的测量相互独立。无论 D1 是否通过，都运行 D3 并保留诊断分；用于排行或总分的门控结果另算：

\[
S_{final}=\begin{cases}
S_{D3}, & D1=6/6,\\
0, & D1<6/6.
\end{cases}
\]

工具缺失、执行失败或版本不匹配时返回 `incomplete_tooling`，不使用 AST fallback；有效 Judge 少于两个时返回 `incomplete_judge`，不形成 100 分制 D3 总分。

## 3. 85 分确定性工具层

固定版本是 `ruff==0.15.22`、`radon==6.0.1`、`bandit==1.9.4`。配置内容和工具版本进入配置哈希；版本变化会使测量合同变化。

### 3.1 可维护性与结构 `S_M`：30 分

由四部分相加：圈复杂度 12 分、结构性问题 8 分、重复结构 5 分、可测试性 5 分。

**圈复杂度（12 分）。** Radon 给出每个函数/方法的 A--F 等级，项目映射为 A=1、B=0.8、C=0.5、D=0.25、E/F=0。若映射后的因子为 `r_i`：

\[
S_{CC}=12\,[0.1\,mean(r_i)+0.9\,min(r_i)].
\]

最差函数占 90% 权重，均值占 10%，目的是防止大量简单 helper 稀释一个极复杂主循环的风险。Radon Maintainability Index 仅落盘记录，不计分。

**结构性问题（8 分）。** Ruff 命中 `C901`、`PLR0904`、`PLR0911`--`PLR0917` 时，每条扣 1.5 分：

\[
S_{struct}=max(0,8-1.5N_{struct}).
\]

这些规则覆盖复杂结构、过多 public 方法、return/branch/argument/local/statement/boolean-expression/positional-argument 等结构负担。

**重复结构（5 分）。** 将模块、函数和类体中的 AST 语句规范化，以连续 6 条语句为窗口；每个重复窗口组除第一次外的额外出现次数记为 `N_extra`：

\[
S_{clone}=max(0,5-N_{extra}).
\]

它是局部重复启发式，不等同于完整 clone detector。

**可测试性（5 分）。** 存在 `if __name__ == "__main__"` 得 2 分；在 dummy SDL 环境下可安全 import 得 2 分；模块顶层可执行语句不超过 3 条得 1 分。

### 3.2 可靠性与缺陷风险 `S_R`：20 分

从 20 分向下扣：

- 严重项每条扣 5 分：`F821`、`F822`、`F823`、`B012`，分别覆盖未定义名称/导出和循环控制流破坏 `finally` 等高缺陷风险。
- 中等项每条扣 2 分：`B006`、`B008`、`B023`、`BLE001`、`E722`、`TRY201`、`TRY203`，覆盖可变默认参数、默认参数函数调用、闭包循环变量绑定、宽泛/裸异常及异常处理流程问题。
- 其他以 `B`、`BLE`、`PLE`、`PLW`、`TRY` 开头且被选中的问题，每条扣 1 分。
- AST 再检查裸 `except`、`Exception` 或 `BaseException`。宽泛处理器每个扣 1 分；若处理器仅 `pass` 或 `continue`，每个再扣 2 分；该 AST 扣分合计最多 4 分。

\[
S_R=max(0,20-D_{ruff}-min(4,N_{broad}+2N_{swallowed})).
\]

### 3.3 安全与任务约束 `S_S`：15 分

Bandit 每条问题的扣分等于严重度权重乘置信度系数：

- 严重度：HIGH=6、MEDIUM=3、LOW=1；
- 置信度：HIGH=1、MEDIUM=0.75、LOW=0.5。

此外，只要出现一项禁用调用类别，额外扣 15 分；只要出现非标准库且非 pygame 的外部依赖类别，再额外扣 15 分。当前禁用前缀为 `eval`、`exec`、`compile`、`os.system`、`os.popen`、`subprocess`、`socket`、`requests`、`urllib.request`。

\[
S_S=max(0,15-D_{Bandit}-15I_{forbidden}-15I_{external}).
\]

任一禁用调用、外部依赖，或 Bandit 的 HIGH severity + HIGH confidence 问题都会设置 `critical_security_risk=true`；此时整个 D3 诊断分再执行 50 分封顶。注意“高危高置信 Bandit 问题”不一定单独把安全子项扣到 0，但一定触发总分封顶；校准中的危险调用 fixture 同时使安全子项为 0 并触发封顶。

### 3.4 效率与资源纪律 `S_E`：10 分

Ruff `PERF` 问题每条扣 1 分，最多扣 4 分。任何 `for`/`while` 循环体中出现下列调用，每个唯一的“调用名+行号”扣 2 分，最多扣 6 分：`open`、`pygame.font.Font`、`pygame.font.SysFont`、`pygame.image.load`、`pygame.mixer.Sound`、`pygame.mixer.music.load`，以及上述安全禁用调用。

\[
S_E=max(0,10-min(4,N_{PERF})-min(6,2N_{hot})).
\]

该项针对单文件 pygame 任务中常见的逐帧 I/O 和资源重复加载；它不是运行时间 benchmark，也不测 FPS、内存峰值或算法渐近复杂度。

### 3.5 Python 规范与可读性 `S_P`：10 分

计入 Ruff 的 `E/W/I/N/UP/SIM` 规则，以及 `F401/F841`。`I/UP/SIM` 每条权重 0.5，其余每条权重 1。用 Radon 的逻辑代码行 `LLOC` 归一化：

\[
density=100\frac{\sum w_i}{max(1,LLOC)},\qquad
S_P=10\,max(0,1-density/10).
\]

即每 100 个逻辑行达到 10 个加权问题时该项降为 0。普通数字数量、函数数量、注释数量和注释密度不再直接计分，避免代码规模或写作风格造成断崖式分差。

## 4. 15 分匿名 Judge 层

Judge 固定为 Nova、DeepSeek、Qwen，温度 0。三者只看到相同的匿名源代码和评分请求，看不到候选模型名、D1、工具分或其他 Judge 结果。每个响应必须是严格 JSON，四项均为整数，并为每项给出非空理由和有效源码行号：

| 现行项目 | 满分 | Prompt 中的判断边界 |
|---|---:|---|
| 职责与抽象 | 5 | 只评价职责组织与抽象质量；函数/类数量多不自动加分 |
| 语义可读性 | 4 | 评价控制流、状态与意图是否易于理解，不以冗长为优 |
| 注释有效性 | 3 | 解释意图/约束的注释有价值；复述代码的注释无价值 |
| 可修改/可测试性 | 3 | 评价结构是否便于局部修改、隔离和测试 |

单个 Judge 最多重试 2 次，即最多 3 次请求。有效 Judge 少于 2 个则不计分；否则：

\[
S_J=mean(total_j),\quad range=max(total_j)-min(total_j).
\]

极差大于 4 分时标记 `high_disagreement`；同时报告样本标准差、每个 Judge 总分和四项均值。若仅两个 Judge 有效，D3 状态为 `panel_degraded`，但仍可形成分数。

**现行限制：** schema v2 Prompt 只定义了四个项目、满分和上述定性边界，没有为每个整数档位定义行为锚点。因此它实现的是“有结构、有证据的语义评审”，还不是经过人类标注校准的完整 anchored rubric。以后若加入逐档锚点，必须提升评估器版本、重跑 Judge，并禁止与现有结果混排。

## 5. 文献与设计依据的对应关系

| 设计部分 | 参考依据 | 实际支撑范围 |
|---|---|---|
| 质量维度组织 | [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) | 提供产品质量特征/子特征的参考模型，用于组织维护性、可靠性、安全性和性能效率等构念；不规定本项目权重 |
| 源码静态度量 | [ISO/IEC 5055:2021](https://www.iso.org/standard/80623.html) | 支撑从架构和编码实践违规形成自动化源码质量措施；不等于本项目已通过 ISO 合规认证 |
| 圈复杂度 | [McCabe, 1976](https://doi.org/10.1109/TSE.1976.233837)；[Radon 定义](https://radon.readthedocs.io/en/latest/intro.html) | 支撑基于控制流图的圈复杂度及 Radon 的具体实现；本项目的 90% 最差值权重是自定义聚合 |
| Python 静态问题 | [Ruff Rules](https://docs.astral.sh/ruff/rules/)；[Bandit](https://bandit.readthedocs.io/en/latest/) | 支撑规则含义与 AST 安全扫描机制；扣 5/2/1 分和安全严重度权重是项目操作化选择 |
| LLM 生成代码的多证据评价 | [Liu et al., 2023](https://arxiv.org/abs/2307.12596) | 研究同时考察生成代码的正确性、风格、可维护性和静态分析问题，支撑“不以单一指标代替代码质量” |
| LLM 语义评分 | [ICE-Score, 2024](https://aclanthology.org/2024.findings-eacl.148/) | 支撑在缺少唯一参考实现/测试 oracle 时用指令化 LLM 做代码质量评估；不能证明本项目四项量表天然有效 |
| 多模型裁判组 | [Replacing Judges with Juries, 2024](https://arxiv.org/abs/2404.18796) | 支撑使用不同模型家族的 panel 降低单 Judge 和同家族偏差；本项目等权平均、至少两个有效和极差阈值是自定义规则 |
| 不采用参考相似度主分 | [CodeBLEU, 2020](https://arxiv.org/abs/2009.10297) | CodeBLEU 融合 token、AST 和 data-flow 的候选--参考匹配；本 Demo 没有唯一标准实现，pygame 又有大量语义等价写法，因此不进入主分 |

最重要的边界是：**30/20/15/10/10/15 权重、具体扣分、50 分封顶、Judge 极差阈值 4，都不是 ISO 或论文直接给出的数字。**它们是当前 Demo 为可解释、可复现和任务约束而设定的操作化方案。正式迁移前仍需用更大规模、多游戏类型的代码样本和人类盲评标签检验区分度、相关性、重测稳定性及裁判家族偏差。
