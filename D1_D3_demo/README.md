# D1/D3 LLM Generation Demo

本目录验证真实链路：

`main.md + 选定游戏 spec -> 渲染 Prompt -> 真实 LLM 生成代码 -> 启动游戏 -> D1 闸门 -> D3 评分`

项目与 demo 共用 `prompts/`，因此新增或修正规格后不需要再同步一份 demo Prompt。
受控 Pong 变体只用于辅助校准评分器，不冒充模型生成结果。

## 真实模型入口

将 AWS 导出的凭据文件保存为项目根目录的 `aws_credentials.csv`。统一入口会自动加载，
且该文件不会进入 Git 或运行产物。

默认仍使用 Pong：

```powershell
python main.py demo --game pong
```

也可以选择任意已补齐的 spec，例如：

```powershell
python main.py demo --game snake
python main.py demo --game flappy_bird
python main.py demo --game space_invaders
python main.py demo --game 2048
python main.py demo --game carrot_defense
python main.py demo --game lode_runner_like
python main.py demo --game farming_lite
```

默认调用 `qwen.qwen3-coder-next`。没有凭据时，程序会保存最终 Prompt 和失败证据，
状态明确记录为 `credentials_missing`，不会用预制代码伪造模型成功。

## 每次运行的证据

产物位于 `D1_D3_demo/runs/<run_id>/`：

- `inputs/main.md`、`inputs/<game>.md`：本次输入快照。
- `prompts/<game>.txt`：实际发送给模型的最终 Prompt。
- `request.json`：模型、区域、采样参数和 Prompt 哈希，不保存凭据。
- `responses/model_output.txt`：模型原始文本。
- `responses/bedrock_response.json`：Bedrock 响应正文和请求元数据。
- `generated/<game>__<model>.py`：从模型响应提取的游戏代码。
- `scores/d1.json`、`scores/d3.json`：正式评估器完整输出。
- `summary.json`：游戏、真实调用状态、实际启动状态和 D1/D3 分数。
- `manifest.json`：本次全部产物的 SHA256。

D1 会在子进程中实际启动模型生成的游戏，检测建窗、事件读取、短时稳定运行，并注入
QUIT 检查干净退出。只有 D1 六步全过才执行 D3。

## 评分器校准

下面的受控样例只回答“D1/D3 这把尺子是否对定向缺陷产生预期响应”：

```powershell
python D1_D3_demo/run_calibration.py --check --repeat 3 --runtime-sec 3
```

构建方法报告：

```powershell
powershell -ExecutionPolicy Bypass -File D1_D3_demo/build_pdf.ps1
```

报告构建前，需要先完成真实模型运行，并把要汇总的 run id 填入
`D1_D3_demo/report_config.json`。仓库中的 `run_ids` 默认为空，避免把某次本地实验编号
冒充可复现输入。构建产生的 `results/`、`build/`、根目录 PDF 和 Overleaf ZIP 均被忽略。

单次生成分数不是稳定模型能力估计。正式论文实验应对每个模型和游戏重复生成，并报告
均值、标准差或 pass@k。
