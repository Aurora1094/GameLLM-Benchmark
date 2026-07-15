# GameBench D1/D3 Demo Goal

## 核心目标

建立一条真实、可复核的 D1/D3 主链：

```text
main.md + pong.md
        -> 渲染最终 Prompt
        -> 真实 LLM 生成单文件 pygame 游戏
        -> 保存模型原始响应与生成代码
        -> 实际启动生成游戏
        -> D1 六级流水线与准入闸门
        -> D1 6/6 后执行 D3 六项代码质量评分
        -> 汇总证据与哈希
```

项目测量对象是 LLM 的游戏生成能力。人工构造的 Pong 基线和退化版本只能用于验证
评分器，不得替代真实模型调用，也不得被表述为模型生成结果。

## 主 Demo

主入口是 `D1_D3_demo/run_demo.py`，默认：

- 游戏：`prompts/specs/easy/pong.md`
- Prompt 骨架：`prompts/main.md`
- Provider：AWS Bedrock
- 模型：`qwen.qwen3-coder-next`
- D1：`evaluator.dimension1.dimension1_executable.evaluate_dimension1`
- D3：`evaluator.dimension3.dimension3_code_quality.evaluate_dimension3_code_quality`

主 demo 必须：

1. 使用 `prompt_builder.py` 渲染最终 Prompt，不能维护另一份 Pong Prompt。
2. 把实际发送的 Prompt、main/spec 快照和请求参数落盘。
3. 调用真实模型并保存模型原始文本、Bedrock 响应正文与请求元数据。
4. 从模型文本提取 Python 源码并原样落盘；即使语法错误也保留，交给 D1 判定。
5. D1 在子进程中实际启动生成代码，检查语法、pygame、窗口、事件、稳定运行和 QUIT。
6. 只有 D1 6/6 时才执行 D3；否则明确记录 `skipped_d1_gate`。
7. `summary.json` 必须区分 `llm_api` 与 `response_replay`，不得把回放或 fixture 标成真实生成。
8. manifest 不得保存 AWS secret，但必须保存每个输入和输出产物的 SHA256。

## 主 Demo 产物

每次真实运行写入 `D1_D3_demo/runs/<run_id>/`：

- `inputs/main.md`、`inputs/pong.md`
- `prompts/pong.txt`
- `request.json`
- `responses/model_output.txt`
- `responses/bedrock_response.json`
- `generated/<game>__<model>.py`
- `scores/d1.json`
- `scores/d3.json`
- `summary.json`
- `manifest.json`

没有凭据时允许停在 `credentials_missing`，并保留已经渲染的 Prompt 和失败证据；
但该状态不能被称为“真实生成 demo 已跑通”。

## D1 契约

D1 不使用 LLM，按有依赖关系的顺序机械测量：

1. Python 语法正确。
2. 导入 pygame。
3. 创建窗口并返回 Surface。
4. 主循环读取事件。
5. 在观察窗口内稳定运行。
6. 注入 QUIT 后干净退出。

```text
D1_score = pipeline_steps_passed / 6
D1_gate = 1 if pipeline_steps_passed == 6 else 0
```

未完全跑通的生成仍保留 D1 能力梯度，但不能进入 D3。

## D3 契约

D3 仅对通过 D1 闸门的真实生成代码执行，满分 100：

- 复杂度控制：15
- 代码复用：20
- 常量使用：15
- 命名规范：15
- 模块划分：20
- 注释质量：15

D3 必须同时保存每项原始静态证据，不能只输出总分。

## 辅助校准

`D1_D3_demo/run_calibration.py` 是 supporting calibration，不是主 demo。它使用：

- D1 的 0--6 级受控样例。
- 一个 Pong 参考实现与六个 D3 定向退化版本。

它回答“评估器在已知缺陷上是否按预期响应”，用于检查阶梯性、敏感性、特异性和
确定性。其结果位于 `D1_D3_demo/results/`，方法文档为 `GameBench_D1_D3.pdf`。

参考 `GB-D4-main.zip` 的是 known-groups calibration 结构，不导入 D4 的 LLM Judge
或实现代码。

## 运行接口

真实模型生成：

```powershell
python D1_D3_demo/run_demo.py
```

评分器辅助校准：

```powershell
python D1_D3_demo/run_calibration.py --check --repeat 3 --runtime-sec 3
```

构建方法文档：

```powershell
powershell -ExecutionPolicy Bypass -File D1_D3_demo/build_pdf.ps1
```

## 成功标准

- 至少一次运行的 `generation.origin` 为 `llm_api` 且模型调用成功。
- 最终 Prompt、模型原文和生成代码均已落盘并有 SHA256。
- D1 确实对子进程中的模型生成代码执行，而不是对人工 fixture 执行后冒充生成。
- D1 输出完整六级证据；D3 严格服从 D1 闸门。
- 真实运行的 summary 能明确回答：模型、Prompt、生成文件、是否实际启动、D1 级别和 D3 分数。
- 辅助校准仍保持全部自动断言通过，并与主 demo 清楚分离。
- 不保存或打印 AWS secret。

## 结论边界

一次真实生成只证明端到端链路闭合，并提供一个样本分数，不足以代表模型稳定能力。
正式论文实验应对每个模型和游戏重复生成，报告均值、标准差、置信区间或 pass@k。

辅助校准只能支持评分器的内部一致性和初步构念效度，不证明 D3 与专家评分高度相关，
也不证明当前阈值与权重唯一最优。

## 完成定义

只有在主 demo 完成至少一次真实 LLM 调用、保存真实生成代码、实际执行 D1、按闸门
执行或跳过 D3，并且整条证据链可由 summary/manifest 复核时，主目标才算完成。
