from __future__ import annotations

from dataclasses import dataclass


CRITERIA = (
    "rule_completeness",
    "state_evolution",
    "interaction_validity",
    "goal_feedback_alignment",
    "constraint_termination",
)


@dataclass(frozen=True)
class StaticCheck:
    name: str
    patterns: tuple[str, ...]
    mode: str = "any"
    regex: bool = False


@dataclass(frozen=True)
class TestPort:
    port_id: str
    name: str
    target: str
    criteria: tuple[str, ...]
    static_checks: tuple[StaticCheck, ...]
    runtime_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class GameProfile:
    game_id: str
    display_name: str
    test_ports: tuple[TestPort, ...]


def kw(name: str, *patterns: str, mode: str = "any") -> StaticCheck:
    return StaticCheck(name=name, patterns=tuple(patterns), mode=mode, regex=False)


def rx(name: str, *patterns: str, mode: str = "any") -> StaticCheck:
    return StaticCheck(name=name, patterns=tuple(patterns), mode=mode, regex=True)


GAME_PROFILES: dict[str, GameProfile] = {
    "easy_snake": GameProfile(
        game_id="easy_snake",
        display_name="Snake Easy",
        test_ports=(
            TestPort(
                "direction_control",
                "Direction control",
                "Arrow-key input changes snake direction.",
                ("interaction_validity",),
                (
                    kw("input keys", "K_UP", "K_DOWN", "K_LEFT", "K_RIGHT", "pygame.K_"),
                    kw("direction state", "direction", "dx", "dy", "velocity", "snake_dir"),
                ),
                ("input_effective",),
            ),
            TestPort(
                "food_growth",
                "Food consumption growth",
                "Eating food increases length or body segments.",
                ("rule_completeness", "state_evolution"),
                (
                    kw("food object", "food", "apple"),
                    kw("eat collision", "collide", "collision", "eat", "head"),
                    kw("growth state", "append", "length", "grow", "body"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "score_feedback",
                "Score feedback",
                "Food events update and display score.",
                ("goal_feedback_alignment", "rule_completeness"),
                (
                    kw("score state", "score"),
                    rx("score update", r"score\s*(\+?=|=)\s*score|score\s*\+=", r"score\s*=\s*score\s*\+"),
                    kw("score draw", "font.render", "blit", "draw", "Score"),
                ),
                ("feedback_visible",),
            ),
            TestPort(
                "wall_or_self_end",
                "Wall or self collision end",
                "Boundary or self collision ends the game.",
                ("constraint_termination", "rule_completeness"),
                (
                    kw("boundary", "WIDTH", "HEIGHT", "wall", "boundary"),
                    kw("self collision", "self", "body", "snake[1:]", "in snake"),
                    kw("end state", "game_over", "Game Over", "running = False", "quit"),
                ),
                ("terminated",),
            ),
        ),
    ),
    "easy_flappy_bird": GameProfile(
        game_id="easy_flappy_bird",
        display_name="Flappy Bird Easy",
        test_ports=(
            TestPort(
                "flap_input",
                "Flap input",
                "Space or key input changes vertical velocity.",
                ("interaction_validity",),
                (
                    kw("flap key", "K_SPACE", "KEYDOWN", "pygame.key"),
                    kw("vertical velocity", "velocity", "vel_y", "bird_y", "jump", "flap"),
                ),
                ("input_effective",),
            ),
            TestPort(
                "gravity_motion",
                "Gravity motion",
                "Bird position evolves under gravity every frame.",
                ("state_evolution",),
                (
                    kw("gravity", "gravity", "GRAVITY"),
                    rx("vertical update", r"(bird_y|y|velocity|vel_y)\s*[+\-*/]?="),
                    kw("frame loop", "while", "clock.tick", "FPS"),
                ),
                ("state_changed",),
            ),
            TestPort(
                "pipe_scoring",
                "Pipe pass scoring",
                "Passing pipes updates score and feedback.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("pipes", "pipe", "pipes"),
                    kw("score", "score"),
                    kw("feedback", "font.render", "blit", "Score"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "collision_end",
                "Collision and bounds end",
                "Pipes or screen bounds trigger failure.",
                ("constraint_termination",),
                (
                    kw("collision", "colliderect", "collision", "hit"),
                    kw("bounds", "HEIGHT", "ground", "top", "bottom"),
                    kw("end state", "game_over", "Game Over", "running = False"),
                ),
                ("terminated",),
            ),
        ),
    ),
    "easy_dodge_blocks": GameProfile(
        game_id="easy_dodge_blocks",
        display_name="Dodge Blocks Easy",
        test_ports=(
            TestPort(
                "player_movement",
                "Player movement",
                "Arrow or WASD input moves the player.",
                ("interaction_validity",),
                (
                    kw("movement keys", "K_LEFT", "K_RIGHT", "K_UP", "K_DOWN", "WASD", "pygame.key"),
                    rx("position update", r"(player|x|y|rect)\.?(x|y)?\s*[+\-]?="),
                ),
                ("input_effective",),
            ),
            TestPort(
                "falling_obstacles",
                "Falling obstacles",
                "Blocks spawn or move over time.",
                ("state_evolution",),
                (
                    kw("obstacles", "block", "obstacle", "enemy"),
                    rx("motion update", r"(speed|velocity|y)\s*[+\-]?="),
                    kw("loop timing", "clock.tick", "FPS", "while"),
                ),
                ("state_changed",),
            ),
            TestPort(
                "avoidance_rule",
                "Avoidance collision rule",
                "Collision with blocks changes life or game state.",
                ("rule_completeness", "constraint_termination"),
                (
                    kw("collision", "colliderect", "collision", "hit"),
                    kw("life or end", "lives", "health", "game_over", "Game Over"),
                ),
                ("state_changed", "terminated"),
            ),
            TestPort(
                "survival_feedback",
                "Survival feedback",
                "Score, time, or lives are visible to the player.",
                ("goal_feedback_alignment",),
                (
                    kw("feedback state", "score", "time", "lives", "survive"),
                    kw("feedback draw", "font.render", "blit", "HUD"),
                ),
                ("feedback_visible",),
            ),
        ),
    ),
    "easy_pong": GameProfile(
        game_id="easy_pong",
        display_name="Pong Easy",
        test_ports=(
            TestPort(
                "paddle_control",
                "Paddle control",
                "Input moves the controlled paddle.",
                ("interaction_validity",),
                (
                    kw("input", "K_UP", "K_DOWN", "get_pressed", "pygame.key"),
                    kw("paddle", "paddle"),
                    rx("paddle update", r"(paddle|player).*(y|rect\.y)\s*[+\-]?="),
                ),
                ("input_effective",),
            ),
            TestPort(
                "ball_bounce",
                "Ball bounce",
                "Ball bounces from walls and paddles with changing direction.",
                ("rule_completeness", "state_evolution"),
                (
                    kw("ball", "ball"),
                    kw("velocity", "dx", "dy", "speed", "vel"),
                    kw("bounce", "colliderect", "collision", "bounce"),
                    kw("wall bounds", "top", "bottom", "HEIGHT", "wall"),
                ),
                ("state_changed",),
            ),
            TestPort(
                "scoring",
                "Scoring",
                "Out-of-bounds ball events update and display both scores.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("score", "score"),
                    kw("bounds", "left", "right", "WIDTH", "out"),
                    kw("draw score", "font.render", "blit"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "opponent_ai",
                "Opponent AI",
                "The opponent paddle tracks the ball to defend automatically.",
                ("rule_completeness", "state_evolution"),
                (
                    kw("opponent", "opponent", "ai", "computer", "right_paddle"),
                    kw("ball tracking", "ball.y", "ball_y", "ball_rect.centery", "centery"),
                    rx("opponent update", r"(opponent|ai|right_paddle|computer).*(y|rect\.y)\s*[+\-]?="),
                ),
                ("state_changed",),
            ),
            TestPort(
                "win_condition",
                "Win condition",
                "A target score ends the game and displays the result.",
                ("constraint_termination",),
                (
                    kw("score target", "WINNING_SCORE", "target_score", "max_score", ">= 5", ">=5"),
                    kw("end", "game_over", "winner", "win", "Game Over", "running = False"),
                    kw("result draw", "font.render", "blit", "winner", "wins"),
                ),
                ("terminated", "feedback_visible"),
            ),
        ),
    ),
    "medium_tetris": GameProfile(
        game_id="medium_tetris",
        display_name="Tetris Medium",
        test_ports=(
            TestPort(
                "piece_control",
                "Piece control",
                "Input moves, rotates, drops, or hard-drops pieces.",
                ("interaction_validity",),
                (
                    kw("keys", "K_LEFT", "K_RIGHT", "K_UP", "K_DOWN", "K_SPACE"),
                    kw("piece action", "rotate", "drop", "move"),
                ),
                ("input_effective",),
            ),
            TestPort(
                "gravity_drop",
                "Gravity drop",
                "Active piece descends on a timer.",
                ("state_evolution",),
                (
                    kw("timer", "500", "fall", "drop", "pygame.time", "clock"),
                    kw("piece y", "current_piece", "piece", "y"),
                    kw("loop", "while", "clock.tick"),
                ),
                ("state_changed",),
            ),
            TestPort(
                "lock_and_lines",
                "Lock and line clear",
                "Pieces lock into the board and full lines clear.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("board", "grid", "board"),
                    kw("lock", "lock", "freeze", "place", "merge"),
                    kw("line clear", "clear", "lines", "rows"),
                    kw("score", "score", "100", "300", "500", "800"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "spawn_collision_end",
                "Spawn collision end",
                "New piece overlap ends the game.",
                ("constraint_termination",),
                (
                    kw("spawn", "spawn", "new_piece", "current_piece"),
                    kw("collision", "collision", "valid_position", "overlap"),
                    kw("end", "game_over", "Game Over"),
                ),
                ("terminated",),
            ),
        ),
    ),
    "medium_space_invaders": GameProfile(
        game_id="medium_space_invaders",
        display_name="Space Invaders Medium",
        test_ports=(
            TestPort(
                "ship_control_fire",
                "Ship control and fire",
                "Input moves the ship and fires bullets.",
                ("interaction_validity",),
                (
                    kw("keys", "K_LEFT", "K_RIGHT", "K_SPACE", "get_pressed"),
                    kw("ship", "player", "ship"),
                    kw("bullet", "bullet", "shoot", "fire"),
                ),
                ("input_effective",),
            ),
            TestPort(
                "enemy_wave_motion",
                "Enemy wave motion",
                "Enemy formation moves over time.",
                ("state_evolution",),
                (
                    kw("enemy", "enemy", "invader", "aliens"),
                    kw("motion", "direction", "speed", "move_down", "dx"),
                    kw("loop", "while", "clock.tick"),
                ),
                ("state_changed",),
            ),
            TestPort(
                "hit_score",
                "Hit scoring",
                "Bullets destroy enemies and update score.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("bullet enemy collision", "colliderect", "collision", "hit"),
                    kw("enemy removal", "remove", "pop", "alive", "False"),
                    kw("score", "score"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "lives_and_end",
                "Lives and termination",
                "Enemy contact, enemy reach, or player hit triggers loss; all enemies cleared wins.",
                ("constraint_termination",),
                (
                    kw("lives", "lives", "health"),
                    kw("end state", "game_over", "Game Over", "win", "You Win"),
                    kw("enemy reach", "bottom", "HEIGHT", "player"),
                ),
                ("terminated",),
            ),
        ),
    ),
    "medium_pacman": GameProfile(
        game_id="medium_pacman",
        display_name="Pac-Man Medium",
        test_ports=(
            TestPort(
                "grid_direction_control",
                "Grid direction control",
                "Arrow input changes Pac-Man direction on valid paths.",
                ("interaction_validity",),
                (
                    kw("keys", "K_UP", "K_DOWN", "K_LEFT", "K_RIGHT"),
                    kw("direction", "direction", "next_dir", "desired"),
                    kw("walls", "wall", "#", "maze"),
                ),
                ("input_effective",),
            ),
            TestPort(
                "pellet_scoring",
                "Pellet scoring",
                "Eating pellets removes them and updates score/count.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("pellet", "pellet", "dot", "bean", "."),
                    kw("score", "score", "+10"),
                    kw("remaining", "remaining", "pellets_left", "dots_left"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "power_pellet_state",
                "Power pellet state",
                "Power pellets make ghosts edible for a timed duration.",
                ("rule_completeness", "state_evolution"),
                (
                    kw("power pellet", "power", "energizer", "frightened"),
                    kw("timer", "6", "timer", "time", "duration"),
                    kw("ghost edible", "edible", "frightened", "vulnerable"),
                ),
                ("state_changed",),
            ),
            TestPort(
                "ghost_behavior",
                "Ghost behavior",
                "Ghosts move through the maze and interact with Pac-Man.",
                ("state_evolution", "constraint_termination"),
                (
                    kw("ghost", "ghost"),
                    kw("movement", "move", "direction", "path", "maze"),
                    kw("collision", "colliderect", "collision", "hit"),
                ),
                ("state_changed", "terminated"),
            ),
            TestPort(
                "win_loss",
                "Win/loss",
                "All pellets cleared wins; lives reaching zero loses.",
                ("constraint_termination", "goal_feedback_alignment"),
                (
                    kw("lives", "lives", "life"),
                    kw("win", "You Win", "win", "all("),
                    kw("loss", "Game Over", "game_over"),
                ),
                ("terminated", "feedback_visible"),
            ),
        ),
    ),
    "medium_super_mario_bros": GameProfile(
        game_id="medium_super_mario_bros",
        display_name="Super Mario Bros Medium",
        test_ports=(
            TestPort(
                "run_jump_control",
                "Run and jump control",
                "Left/right/space input changes player movement and jump velocity.",
                ("interaction_validity",),
                (
                    kw("keys", "K_LEFT", "K_RIGHT", "K_SPACE"),
                    kw("physics state", "vel_y", "velocity", "jump", "gravity"),
                    kw("player", "player"),
                ),
                ("input_effective",),
            ),
            TestPort(
                "scrolling_world",
                "Scrolling world",
                "Camera follows player across a fixed wide level.",
                ("state_evolution",),
                (
                    kw("world size", "3200", "WORLD_WIDTH", "camera", "scroll"),
                    rx("camera update", r"(camera|scroll).*="),
                    kw("loop", "while", "clock.tick"),
                ),
                ("state_changed",),
            ),
            TestPort(
                "block_coin_enemy_rules",
                "Block, coin, and enemy rules",
                "Collisions with blocks, coins, and enemies produce game results and feedback.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("blocks", "brick", "question", "block", "platform"),
                    kw("coin", "coin", "+100"),
                    kw("enemy", "enemy", "stomp", "+200"),
                    kw("collision", "colliderect", "collision"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "pit_life_flag_end",
                "Pit, life, and flag end",
                "Pits or enemies cost lives; flag wins; zero lives loses.",
                ("constraint_termination",),
                (
                    kw("lives", "lives", "life"),
                    kw("pit", "pit", "fall", "HEIGHT"),
                    kw("flag", "flag", "goal", "finish"),
                    kw("end", "game_over", "You Win", "Game Over"),
                ),
                ("terminated",),
            ),
        ),
    ),
    "hard_roguelike_dungeon": GameProfile(
        game_id="hard_roguelike_dungeon",
        display_name="Roguelike Dungeon Hard",
        test_ports=(
            TestPort(
                "turn_input",
                "Turn input",
                "Arrow input advances player turns.",
                ("interaction_validity", "state_evolution"),
                (
                    kw("keys", "K_UP", "K_DOWN", "K_LEFT", "K_RIGHT"),
                    kw("turn", "turn", "enemy_turn", "move_enemies"),
                    kw("player", "player"),
                ),
                ("input_effective", "state_changed"),
            ),
            TestPort(
                "dungeon_generation",
                "Dungeon generation",
                "Rooms, corridors, walls, floor, and exit create a navigable dungeon.",
                ("rule_completeness", "constraint_termination"),
                (
                    kw("rooms", "room", "rooms"),
                    kw("corridors", "corridor", "tunnel"),
                    kw("exit", "exit", "stairs"),
                    kw("walls", "wall", "floor"),
                ),
                ("state_changed",),
            ),
            TestPort(
                "combat_xp_level",
                "Combat, XP, and level",
                "Adjacent enemy combat affects HP, XP, and level.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("combat", "attack", "ATK", "damage"),
                    kw("health", "HP", "health"),
                    kw("progression", "EXP", "level", "LV"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "items",
                "Items",
                "Potions and weapons modify player resources.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("potion", "potion", "heal"),
                    kw("weapon", "weapon", "ATK", "+2"),
                    kw("pickup", "pickup", "item", "collect"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "floor_or_death_end",
                "Floor advance or death",
                "Exit advances floor or wins; HP zero ends the game.",
                ("constraint_termination", "goal_feedback_alignment"),
                (
                    kw("floor", "floor", "Floor"),
                    kw("death", "HP <= 0", "health <= 0", "game_over"),
                    kw("restart text", "Press R", "Game Over", "You Win"),
                ),
                ("terminated", "feedback_visible"),
            ),
        ),
    ),
    "hard_tower_defense": GameProfile(
        game_id="hard_tower_defense",
        display_name="Tower Defense Hard",
        test_ports=(
            TestPort(
                "tower_build_input",
                "Tower build input",
                "Mouse and number keys select and place towers on valid tiles.",
                ("interaction_validity",),
                (
                    kw("mouse", "MOUSEBUTTONDOWN", "mouse", "get_pos"),
                    kw("tower selection", "K_1", "K_2", "K_3", "selected"),
                    kw("build", "build", "place", "tower"),
                ),
                ("input_effective",),
            ),
            TestPort(
                "enemy_path_waves",
                "Enemy path and waves",
                "Enemies spawn in waves and follow a fixed path.",
                ("state_evolution", "constraint_termination"),
                (
                    kw("path", "path", "waypoint", "route"),
                    kw("waves", "wave", "spawn"),
                    kw("enemy motion", "enemy", "speed", "move"),
                ),
                ("state_changed",),
            ),
            TestPort(
                "tower_attack_rules",
                "Tower attack rules",
                "Arrow, cannon, and slow towers target enemies with different effects.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("tower types", "Arrow", "Cannon", "Slow", "arrow", "cannon", "slow"),
                    kw("range damage", "range", "damage", "cooldown"),
                    kw("effects", "splash", "slow", "projectile"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "economy_upgrade",
                "Economy and upgrade",
                "Gold costs, rewards, and upgrades change tower state.",
                ("rule_completeness", "goal_feedback_alignment"),
                (
                    kw("gold", "gold", "coins", "money"),
                    kw("cost", "cost", "50", "80", "70"),
                    kw("upgrade", "upgrade", "level"),
                ),
                ("state_changed", "feedback_visible"),
            ),
            TestPort(
                "base_life_victory_loss",
                "Base life and victory/loss",
                "Enemies reaching base reduce life; five waves cleared wins; zero base life loses.",
                ("constraint_termination", "goal_feedback_alignment"),
                (
                    kw("base life", "base", "lives", "health", "20"),
                    kw("victory loss", "You Win", "Game Over", "game_over", "win"),
                    kw("wave target", "5", "MAX_WAVES", "wave"),
                ),
                ("terminated", "feedback_visible"),
            ),
        ),
    ),
}
