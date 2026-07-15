from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "prompts" / "specs"
WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TOP_LEVEL_SECTION = re.compile(r"^#\s*(\d+)(?:\.|\s)")


@dataclass(frozen=True)
class SpecDefinition:
    source_fragment: str
    destination: str
    game_name: str
    difficulty: str
    window_size: tuple[int, int]
    player_color: str
    round_time_sec: int
    checkpoints: tuple[tuple[str, str], ...]


SPECS = (
    SpecDefinition(
        source_fragment="Snake ",
        destination="easy/snake.md",
        game_name="Snake（贪吃蛇）",
        difficulty="easy",
        window_size=(600, 800),
        player_color="#F28C28",
        round_time_sec=120,
        checkpoints=(
            ("direction_control", "玩家使用 WASD 控制蛇按网格改变方向，直接反向输入必须被忽略"),
            ("food_growth", "蛇吃到食物后身体长度增加一格，并在未被蛇占据的格子重新生成一个食物"),
            ("score_feedback", "每吃到一个食物分数增加 1，顶部持续显示实时分数"),
            ("wall_or_self_end", "蛇穿越上下边界时从另一侧回绕，碰到左右边界或自身时结束，并可按 R 完整重开"),
        ),
    ),
    SpecDefinition(
        source_fragment="Flapping Bird",
        destination="easy/flappy_bird.md",
        game_name="Flappy Bird",
        difficulty="easy",
        window_size=(800, 600),
        player_color="#FFD700",
        round_time_sec=120,
        checkpoints=(
            ("flap_input", "每次独立按下 Space 都把小鸟竖直速度设为向上拍动速度，长按不能连续触发"),
            ("gravity_motion", "小鸟持续受重力影响，管道按规定速度和间隔从右向左连续移动并生成"),
            ("pipe_scoring", "分数按小鸟存活秒数向下取整并实时显示，通过管道本身不能额外加分"),
            ("collision_end", "小鸟碰到上下边界或任意管道时结束，显示结束反馈并可按 R 完整重开"),
        ),
    ),
    SpecDefinition(
        source_fragment="Space Invaders",
        destination="medium/space_invaders.md",
        game_name="Space Invaders（太空侵略者）",
        difficulty="medium",
        window_size=(800, 600),
        player_color="#2F80ED",
        round_time_sec=180,
        checkpoints=(
            ("ship_control_fire", "玩家用 A/D 左右移动飞船并用 Space 发射子弹，移动范围和发射频率均受规则约束"),
            ("enemy_wave_motion", "敌人按三波独立阵列生成，只整体向下推进，并能随机向下发射敌人子弹"),
            ("hit_score", "玩家子弹击中敌人后只消灭一个目标并增加 10 分，界面实时显示分数与波次"),
            ("lives_and_end", "受击正确扣除生命并触发短暂无敌；三波清空时胜利，生命耗尽或敌人突破防线时失败，并可按 R 重开"),
        ),
    ),
    SpecDefinition(
        source_fragment="2048",
        destination="medium/2048.md",
        game_name="2048",
        difficulty="medium",
        window_size=(600, 800),
        player_color="#EDC22E",
        round_time_sec=300,
        checkpoints=(
            ("move_and_merge", "方向键每次只触发一次压缩与合并流程，相同方块按移动方向合并且每格每回合最多合并一次"),
            ("deterministic_spawn", "只有有效移动后才在随机空格生成新方块，数值严格按 2、2、2、2、4 的循环产生"),
            ("score_and_max_feedback", "合并所得新方块数值累加到分数，界面实时显示 Score 和 Max Tile"),
            ("continue_after_2048", "首次生成 2048 后显示达成提示但不终止游戏，玩家仍可继续移动和合并"),
            ("no_moves_end", "仅在棋盘无空格且没有相邻可合并方块时结束，并可按 R 清空状态后重新开始"),
        ),
    ),
    SpecDefinition(
        source_fragment="Carrot Defense",
        destination="hard/carrot_defense.md",
        game_name="Carrot Defense-like",
        difficulty="hard",
        window_size=(800, 600),
        player_color="#F28C28",
        round_time_sec=240,
        checkpoints=(
            ("tower_placement_economy", "玩家能选择普通塔、冷冻塔或铲子，在合法格子按金币规则连续建造或无退款拆除"),
            ("wave_enemy_progression", "四波敌人依次生成并沿固定路径前进，当前波清空后才进入下一次三秒准备阶段"),
            ("tower_attack_freeze", "防御塔自动选择范围内目标攻击，普通塔造成伤害，冷冻塔造成不叠加但可刷新的减速"),
            ("combat_feedback_rewards", "击杀、生命、金币、剩余敌人、攻击线、血条和完美波次奖励均提供一致的可见反馈"),
            ("carrot_win_loss", "敌人到达终点时正确伤害萝卜；萝卜生命耗尽时失败，第四波结束且仍有生命时胜利，并可按 R 重开"),
        ),
    ),
    SpecDefinition(
        source_fragment="Lode Runner-like",
        destination="hard/lode_runner_like.md",
        game_name="Lode Runner-like Platform Collector（淘金者类平台收集游戏）",
        difficulty="hard",
        window_size=(800, 600),
        player_color="#2D9CDB",
        round_time_sec=240,
        checkpoints=(
            ("movement_ladders", "玩家使用方向键在固定平台地图上移动和攀爬梯子，并遵守墙体、平台与重力约束"),
            ("digging_recovery", "Z/X 只能挖除玩家左下或右下的普通砖块，临时洞会困住角色并在四秒后恢复"),
            ("gold_door_progression", "六个金块被逐一收集并更新顶部图标，全部收集后出口门从关闭状态变为可进入"),
            ("enemy_damage_lives", "三个敌人持续追踪玩家；接触会扣除生命、重置位置并提供两秒可见无敌反馈"),
            ("escape_or_game_over", "玩家进入已开启出口时胜利，生命降为零时失败，结束后冻结状态并可按 R 完整重开"),
        ),
    ),
    SpecDefinition(
        source_fragment="Farming-lite",
        destination="hard/farming_lite.md",
        game_name="Farming-lite",
        difficulty="hard",
        window_size=(800, 600),
        player_color="#F28C28",
        round_time_sec=240,
        checkpoints=(
            ("tool_selection_and_actions", "玩家能选择两种种子、浇水壶和收获工具，并用鼠标在 6×4 地块上执行或取消操作"),
            ("daily_growth_cycle", "每个三十秒日程结束时只让当天浇水的作物成长一阶段，并重置全部浇水状态"),
            ("economy_harvest", "播种按价格扣除金币，只有成熟作物可收获并按作物收益增加金币和分类统计"),
            ("farm_state_feedback", "界面持续显示金币、天数、时间和累计收获，并清楚反馈地块阶段、选中工具、错误与收获结果"),
            ("season_completion", "第八天结束时只执行一次成熟作物自动收获，显示 Season Complete 结算并可按 R 完整重开"),
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import the supplied GameBench DOCX game specifications into prompt specs."
    )
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args()


def docx_paragraphs(document: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(document)) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{{{WORD_NAMESPACE}}}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            local_name = node.tag.rsplit("}", 1)[-1]
            if local_name == "t" and node.text:
                parts.append(node.text)
            elif local_name == "tab":
                parts.append("\t")
            elif local_name in {"br", "cr"}:
                parts.append("\n")
        paragraphs.append("".join(parts).strip())
    return paragraphs


def specification_body(paragraphs: list[str], source_name: str) -> str:
    content: list[str] = []
    started = False
    for paragraph in paragraphs:
        match = TOP_LEVEL_SECTION.match(paragraph)
        if match:
            section = int(match.group(1))
            if section == 1:
                started = True
            elif section >= 8 and started:
                break
        if started and paragraph and paragraph != "---":
            content.append(paragraph)
    if not content:
        raise ValueError(f"No sections 1-7 found in {source_name}")
    return "\n\n".join(content).strip()


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_spec(definition: SpecDefinition, source_name: str, body: str) -> str:
    width, height = definition.window_size
    lines = [
        "---",
        f"game_name: {yaml_string(definition.game_name)}",
        f"difficulty: {definition.difficulty}",
        f"source_doc: {yaml_string(source_name)}",
        "params:",
        f"  window_size: [{width}, {height}]",
        f"  player_color: {yaml_string(definition.player_color)}",
        f"  round_time_sec: {definition.round_time_sec}",
        "checkpoints:",
    ]
    for checkpoint_id, description in definition.checkpoints:
        lines.extend(
            (
                f"  - id: {checkpoint_id}",
                f"    desc: {yaml_string(description)}",
                "    weight: 1",
            )
        )
    lines.extend(("---", body, ""))
    return "\n".join(lines)


def find_source_member(members: list[str], fragment: str) -> str:
    matches = [
        member
        for member in members
        if PurePosixPath(member).suffix.lower() == ".docx"
        and fragment.casefold() in PurePosixPath(member).name.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one DOCX matching {fragment!r}, found {matches}")
    return matches[0]


def import_specs(zip_path: Path, output_root: Path) -> list[Path]:
    if not zip_path.is_file():
        raise FileNotFoundError(zip_path)
    written: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        members = archive.namelist()
        for definition in SPECS:
            member = find_source_member(members, definition.source_fragment)
            body = specification_body(docx_paragraphs(archive.read(member)), member)
            destination = output_root / definition.destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                render_spec(definition, PurePosixPath(member).name, body),
                encoding="utf-8",
            )
            written.append(destination)
    return written


def main() -> int:
    args = parse_args()
    for path in import_specs(args.zip_path.resolve(), args.output_root.resolve()):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
