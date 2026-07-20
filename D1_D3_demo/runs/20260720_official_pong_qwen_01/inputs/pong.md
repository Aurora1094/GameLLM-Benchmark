---
game_name: Pong
difficulty: easy
params:
  window_size: [800, 600]
  player_color: "#FFFFFF"
  round_time_sec: 120
checkpoints:
  - id: paddle_control
    desc: 玩家用上下方向键控制己方球拍上下移动，球拍不超出屏幕边界
    weight: 1
  - id: ball_bounce
    desc: 球碰到上下墙壁和球拍时正确反弹，方向与速度变化合理
    weight: 1
  - id: scoring
    desc: 球越过一侧边界时对方得分，并在画面上实时显示双方比分
    weight: 1
  - id: opponent_ai
    desc: 对手球拍能自动追踪球的位置进行防守，构成可玩的对抗
    weight: 1
  - id: win_condition
    desc: 任一方达到目标分数时本局结束，并显示胜负结果
    weight: 1
---
经典乒乓对战：两块竖直球拍分居屏幕左右，一颗球在中间往返。
玩家控制左侧球拍，目标是让球越过对手一侧得分，先达到目标分数者获胜。
