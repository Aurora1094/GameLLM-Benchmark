# 游戏 spec 文件规范 (specs/<difficulty>/<game>.md)

每个游戏一个文件，提供 main.md 占位符所需的**值**，同时作为
维度二 (D2 Functionality) 评估器的**打分靶子**。这两处读同一份数据
——单一真源 (single source of truth)。禁止在评估器里另建一份功能清单。

## 结构：YAML frontmatter + 可选自由描述

```markdown
---
game_name: <string>          # 注入 {game_name}
difficulty: easy|medium|hard # 组织与 D3 难度分档用
params:
  window_size: [W, H]        # 注入 {window_size}，可反哺 D1 窗口检测
  player_color: "#RRGGBB"    # 注入 {player_color}
  round_time_sec: <int>      # 注入 {round_time_sec}
checkpoints:                 # 注入 {checkpoints_rendered}，同时是 D2 靶子
  - id: <snake_case_id>      # 稳定 id，评估器按 id 对齐打分
    desc: <一句话功能描述>    # 面向模型的行为描述，勿写评分细节
    weight: <int, 可选>       # D2 内部权重，缺省为 1
---
<可选：补充玩法背景 / 画面氛围的自由文本，注入 {game_description}>
```

## 字段约束（builder 应校验）
- `game_name` / `difficulty` / `params.*` / `checkpoints` 为必填。
- `params.window_size` 必须是两个正整数。
- `checkpoints` 至少 1 条；每条 `id` 在本文件内唯一、跨版本稳定
  （id 是评估器对齐的键，改 id = 破坏历史可比性）。
- `desc` 用**行为语言**写"要实现什么"，不写"我们会怎么打分"。

## checkpoints_rendered 的渲染约定
builder 把 checkpoints 列表渲染成对模型友好的多行编号清单，例如：
```
1. 玩家用上下方向键控制己方球拍上下移动
2. 球碰到上下墙壁和球拍时正确反弹
3. 球越过一侧边界时对方得分，并实时显示比分
4. 任一方达到目标分数时本局结束并显示结果
```
渲染只做 desc 的编号拼接，**不注入 weight/id**（那是评估器内部信息）。
