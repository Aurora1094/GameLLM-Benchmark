from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


RESPONSIBILITY_KEYWORDS = {
    "init",
    "setup",
    "handle",
    "input",
    "event",
    "update",
    "move",
    "collision",
    "collide",
    "score",
    "draw",
    "render",
    "reset",
}

BAD_NAMES = {"a", "b", "c", "x", "y", "z", "tmp", "temp", "var", "data", "foo", "bar"}
IGNORED_NUMBERS = {0, 1, -1}
SNAKE_CASE_RE = re.compile(r"^_?[a-z][a-z0-9_]*$")
UPPER_CASE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
CAP_WORDS_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def _read_source(code_path: Path) -> str:
    return code_path.read_text(encoding="utf-8-sig", errors="ignore").lstrip("\ufeff")


def _parse_source(source: str) -> ast.AST | None:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _line_bounds(node: ast.AST) -> tuple[int, int]:
    start = getattr(node, "lineno", 0)
    end = getattr(node, "end_lineno", start)
    return start, end


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _function_nodes(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _class_nodes(tree: ast.AST) -> list[ast.ClassDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]


def _effective_code_lines(source_lines: list[str]) -> list[str]:
    lines: list[str] = []
    for raw in source_lines:
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.lower() in {"pass", "return", "return none", "continue", "break"}:
            continue
        lines.append(re.sub(r"\s+", " ", line))
    return lines


def _attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _attribute_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


# =========================
# 指标 1：复杂度控制（15）
# =========================
def _fallback_cyclomatic_complexities(tree: ast.AST) -> list[int]:
    decision_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.IfExp,
        ast.ExceptHandler,
        ast.Assert,
        ast.comprehension,
    )

    def complexity(node: ast.AST) -> int:
        score = 1
        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, decision_nodes):
                score += 1
            elif isinstance(child, ast.BoolOp):
                score += max(0, len(child.values) - 1)
        return score

    functions = _function_nodes(tree)
    if functions:
        return [complexity(fn) for fn in functions]
    return [complexity(tree)]


def _radon_cyclomatic_complexities(source: str) -> tuple[list[int], str]:
    try:
        from radon.complexity import cc_visit  # type: ignore
    except Exception:
        return [], "ast_fallback"

    try:
        blocks = cc_visit(source)
    except Exception:
        return [], "ast_fallback"

    complexities = [int(block.complexity) for block in blocks if getattr(block, "complexity", None) is not None]
    return complexities, "radon"


def _max_nesting_depth_in_node(node: ast.AST) -> int:
    control_nodes = (ast.If, ast.For, ast.While, ast.AsyncFor)

    def walk(current: ast.AST, depth: int) -> int:
        next_depth = depth + 1 if isinstance(current, control_nodes) else depth
        best = next_depth
        for child in ast.iter_child_nodes(current):
            best = max(best, walk(child, next_depth))
        return best

    return walk(node, 0)


def _indicator_1_complexity(source: str, tree: ast.AST) -> dict[str, Any]:
    functions = _function_nodes(tree)
    lengths = [max(0, _line_bounds(fn)[1] - _line_bounds(fn)[0] + 1) for fn in functions]
    max_func_length = max(lengths, default=0)
    avg_func_length = mean(lengths) if lengths else 0.0
    max_depth = max((_max_nesting_depth_in_node(fn) for fn in functions), default=0)

    complexities, method = _radon_cyclomatic_complexities(source)
    if not complexities:
        complexities = _fallback_cyclomatic_complexities(tree)
        method = "ast_fallback"

    max_cc = max(complexities, default=0)
    avg_cc = mean(complexities) if complexities else 0.0

    if max_cc <= 8 and avg_cc <= 4:
        cc_score = 9
    elif max_cc <= 12 and avg_cc <= 6:
        cc_score = 7
    elif max_cc <= 18 and avg_cc <= 8:
        cc_score = 5
    elif max_cc <= 25 and avg_cc <= 10:
        cc_score = 3
    else:
        cc_score = 0

    if max_func_length <= 50 and avg_func_length <= 35:
        length_score = 3
    elif max_func_length <= 80:
        length_score = 2
    elif max_func_length <= 120:
        length_score = 1
    else:
        length_score = 0

    if max_depth <= 3:
        depth_score = 3
    elif max_depth == 4:
        depth_score = 2
    elif max_depth == 5:
        depth_score = 1
    else:
        depth_score = 0

    return {
        "score": cc_score + length_score + depth_score,
        "method": method,
        "cyclomatic_complexities": complexities,
        "max_cc": max_cc,
        "avg_cc": avg_cc,
        "max_func_length": max_func_length,
        "avg_func_length": avg_func_length,
        "max_depth": max_depth,
        "cc_score": cc_score,
        "length_score": length_score,
        "depth_score": depth_score,
    }


# =========================
# 指标 2：代码复用（20）
# =========================
def _indicator_2_reuse(tree: ast.AST, source_lines: list[str]) -> dict[str, Any]:
    effective_lines = _effective_code_lines(source_lines)
    ngram_size = 4
    if len(effective_lines) >= ngram_size:
        blocks = [tuple(effective_lines[i : i + ngram_size]) for i in range(len(effective_lines) - ngram_size + 1)]
    else:
        blocks = []

    block_counter = Counter(blocks)
    duplicated_blocks = sum(count - 1 for count in block_counter.values() if count > 1)
    duplicate_block_ratio = duplicated_blocks / len(blocks) if blocks else 0.0

    if duplicate_block_ratio <= 0.03:
        duplication_score = 20
    elif duplicate_block_ratio <= 0.08:
        duplication_score = 15
    elif duplicate_block_ratio <= 0.15:
        duplication_score = 10
    elif duplicate_block_ratio <= 0.25:
        duplication_score = 5
    else:
        duplication_score = 0

    defined_funcs = {n.name for n in _function_nodes(tree)}
    call_counter: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in defined_funcs:
            call_counter[node.func.id] += 1
    reused_func_count = sum(1 for count in call_counter.values() if count >= 2)

    return {
        "score": duplication_score,
        "method": "normalized_4_line_block_similarity",
        "duplicate_block_ratio": duplicate_block_ratio,
        "duplicated_blocks": duplicated_blocks,
        "total_blocks": len(blocks),
        "effective_lines": len(effective_lines),
        "reused_func_count": reused_func_count,
    }


# =========================
# 指标 3：常量使用（15）
# =========================
def _literal_numeric_value(node: ast.Constant, parents: dict[ast.AST, ast.AST]) -> int | float | None:
    if not isinstance(node.value, (int, float)) or isinstance(node.value, bool):
        return None
    value: int | float = node.value
    parent = parents.get(node)
    if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.USub):
        value = -value
    return value


def _assignment_targets_upper(assign_node: ast.AST) -> bool:
    targets: list[ast.AST] = []
    if isinstance(assign_node, ast.Assign):
        targets = list(assign_node.targets)
    elif isinstance(assign_node, ast.AnnAssign):
        targets = [assign_node.target]

    for target in targets:
        if isinstance(target, ast.Name) and UPPER_CASE_RE.match(target.id):
            return True
        if isinstance(target, (ast.Tuple, ast.List)):
            if any(isinstance(item, ast.Name) and UPPER_CASE_RE.match(item.id) for item in target.elts):
                return True
    return False


def _inside_upper_constant_assignment(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.Assign, ast.AnnAssign)):
            return _assignment_targets_upper(current)
    return False


def _inside_range_boundary(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.Call) and _attribute_name(current.func) == "range":
            return True
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return False
    return False


def _constant_numeric_values(tree: ast.AST, parents: dict[ast.AST, ast.AST]) -> set[int | float]:
    values: set[int | float] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            value = _literal_numeric_value(node, parents)
            if value is not None and _inside_upper_constant_assignment(node, parents):
                values.add(value)
    return values


def _indicator_3_constants(tree: ast.AST, source_lines: list[str]) -> dict[str, Any]:
    parents = _parent_map(tree)
    constant_values = _constant_numeric_values(tree, parents)
    numeric_literals = 0
    magic_numbers = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        value = _literal_numeric_value(node, parents)
        if value is None or value in IGNORED_NUMBERS:
            continue
        if _inside_range_boundary(node, parents):
            continue

        numeric_literals += 1
        if _inside_upper_constant_assignment(node, parents):
            continue
        if value in constant_values:
            continue
        magic_numbers += 1

    effective_lines = max(1, len(_effective_code_lines(source_lines)))
    magic_density = magic_numbers / effective_lines

    if magic_density <= 0.03:
        score = 15
    elif magic_density <= 0.07:
        score = 10
    elif magic_density <= 0.12:
        score = 5
    else:
        score = 0

    if numeric_literals > 2 and not constant_values:
        score = min(score, 5)

    return {
        "score": score,
        "method": "ast_magic_number_density",
        "constants_count": len(constant_values),
        "constant_values": sorted(constant_values),
        "numeric_literals": numeric_literals,
        "magic_numbers": magic_numbers,
        "effective_lines": effective_lines,
        "magic_density": magic_density,
    }


# =========================
# 指标 4：命名规范（15）
# =========================
def _is_descriptive_name(name: str) -> bool:
    stripped = name.strip("_").lower()
    if len(stripped) < 2:
        return False
    if stripped in BAD_NAMES:
        return False
    return True


def _indicator_4_naming(tree: ast.AST) -> dict[str, Any]:
    checked: list[tuple[str, str, bool]] = []

    for fn in _function_nodes(tree):
        checked.append(("function", fn.name, bool(SNAKE_CASE_RE.match(fn.name))))
        for arg in fn.args.args:
            if arg.arg in {"self", "cls"}:
                continue
            checked.append(("parameter", arg.arg, bool(SNAKE_CASE_RE.match(arg.arg))))

    for cls in _class_nodes(tree):
        checked.append(("class", cls.name, bool(CAP_WORDS_RE.match(cls.name))))

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if UPPER_CASE_RE.match(node.id):
                checked.append(("constant", node.id, True))
            else:
                checked.append(("variable", node.id, bool(SNAKE_CASE_RE.match(node.id))))

    unique_checked = sorted(set(checked), key=lambda item: (item[0], item[1]))
    total = len(unique_checked)
    convention_ok = sum(1 for _, _, ok in unique_checked if ok)
    descriptive_ok = sum(1 for _, name, _ in unique_checked if _is_descriptive_name(name))
    convention_ratio = convention_ok / total if total else 0.0
    descriptive_ratio = descriptive_ok / total if total else 0.0

    score = round(convention_ratio * 10 + descriptive_ratio * 5)

    return {
        "score": score,
        "method": "pep8_naming_and_generic_name_scan",
        "total_names": total,
        "convention_ok": convention_ok,
        "descriptive_ok": descriptive_ok,
        "convention_ratio": convention_ratio,
        "descriptive_ratio": descriptive_ratio,
        "violations": [
            {"kind": kind, "name": name}
            for kind, name, ok in unique_checked
            if not ok or not _is_descriptive_name(name)
        ][:50],
    }


# =========================
# 指标 5：模块划分（20）
# =========================
def _is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if not isinstance(test, ast.Compare):
        return False
    if not (isinstance(test.left, ast.Name) and test.left.id == "__name__"):
        return False
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    if len(test.comparators) != 1:
        return False
    comparator = test.comparators[0]
    return isinstance(comparator, ast.Constant) and comparator.value == "__main__"


def _top_level_executable_count(tree: ast.AST) -> int:
    count = 0
    passive = (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    for node in getattr(tree, "body", []):
        if isinstance(node, passive):
            continue
        if _is_main_guard(node):
            continue
        count += 1
    return count


def _indicator_5_modularity(tree: ast.AST) -> dict[str, Any]:
    functions = _function_nodes(tree)
    classes = _class_nodes(tree)
    num_functions = len(functions)
    num_classes = len(classes)
    lengths = [max(0, _line_bounds(fn)[1] - _line_bounds(fn)[0] + 1) for fn in functions]
    max_func_length = max(lengths, default=0)
    avg_func_length = mean(lengths) if lengths else 0.0
    has_main_guard = any(_is_main_guard(node) for node in getattr(tree, "body", []))
    top_level_executable = _top_level_executable_count(tree)

    if num_functions == 0:
        function_count_score = 0
    elif num_functions <= 2:
        function_count_score = 2
    elif num_functions <= 5:
        function_count_score = 4
    else:
        function_count_score = 5

    if max_func_length <= 40:
        length_score = 5
    elif max_func_length <= 70:
        length_score = 3
    elif max_func_length <= 100:
        length_score = 1
    else:
        length_score = 0

    main_guard_score = 4 if has_main_guard else 0

    function_names = [fn.name.lower() for fn in functions]
    responsibility_hits = sum(
        1 for keyword in RESPONSIBILITY_KEYWORDS if any(keyword in name for name in function_names)
    )
    if responsibility_hits >= 6:
        responsibility_score = 6
    elif responsibility_hits >= 4:
        responsibility_score = 4
    elif responsibility_hits >= 2:
        responsibility_score = 2
    else:
        responsibility_score = 0

    score = function_count_score + length_score + main_guard_score + responsibility_score
    if top_level_executable > 3:
        score = max(0, score - 2)

    return {
        "score": min(20, score),
        "method": "ast_structure_metrics",
        "num_functions": num_functions,
        "num_classes": num_classes,
        "max_func_length": max_func_length,
        "avg_func_length": avg_func_length,
        "has_main_guard": has_main_guard,
        "top_level_executable_count": top_level_executable,
        "responsibility_hits": responsibility_hits,
        "function_count_score": function_count_score,
        "length_score": length_score,
        "main_guard_score": main_guard_score,
        "responsibility_score": responsibility_score,
    }


# =========================
# 指标 6：注释质量（15）
# =========================
def _effective_comment_lines(source_lines: list[str]) -> int:
    count = 0
    run = 0
    for raw in source_lines:
        stripped = raw.strip()
        if stripped.startswith("#"):
            run += 1
            continue
        if run:
            count += min(run, 2)
            run = 0
    if run:
        count += min(run, 2)
    return count


def _docstring_stats(tree: ast.AST) -> tuple[int, int, int]:
    holders: list[ast.AST] = [tree]
    holders.extend(_function_nodes(tree))
    holders.extend(_class_nodes(tree))

    with_docstring = 0
    docstring_lines = 0
    for holder in holders:
        body = getattr(holder, "body", None)
        if not body:
            continue
        first_stmt = body[0]
        if not isinstance(first_stmt, ast.Expr):
            continue
        value = first_stmt.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            with_docstring += 1
            start = getattr(first_stmt, "lineno", 0)
            end = getattr(first_stmt, "end_lineno", start)
            docstring_lines += max(1, end - start + 1)
    return len(holders), with_docstring, docstring_lines


def _indicator_6_comments(source_lines: list[str], tree: ast.AST) -> dict[str, Any]:
    total_lines = max(1, len(source_lines))
    hash_comment_lines = _effective_comment_lines(source_lines)
    doc_targets, docstring_count, docstring_lines = _docstring_stats(tree)
    comment_lines = hash_comment_lines + docstring_lines
    comment_density = comment_lines / total_lines
    docstring_coverage = docstring_count / doc_targets if doc_targets else 0.0

    if 0.04 <= comment_density <= 0.18:
        density_score = 8
    elif 0.02 <= comment_density < 0.04 or 0.18 < comment_density <= 0.25:
        density_score = 5
    elif comment_density > 0:
        density_score = 2
    else:
        density_score = 0

    if docstring_coverage >= 0.5:
        docstring_score = 5
    elif docstring_coverage >= 0.2:
        docstring_score = 3
    elif docstring_count > 0:
        docstring_score = 1
    else:
        docstring_score = 0
    non_noise_score = 2 if 0 < comment_density <= 0.25 else 0

    return {
        "score": density_score + docstring_score + non_noise_score,
        "method": "comment_density_and_docstring_coverage",
        "comment_lines": comment_lines,
        "hash_comment_lines": hash_comment_lines,
        "docstring_lines": docstring_lines,
        "total_lines": total_lines,
        "comment_density": comment_density,
        "docstring_targets": doc_targets,
        "docstring_count": docstring_count,
        "docstring_coverage": docstring_coverage,
        "density_score": density_score,
        "docstring_score": docstring_score,
        "non_noise_score": non_noise_score,
    }


def _zero_indicator_scores() -> dict[str, int]:
    return {
        "complexity": 0,
        "reuse": 0,
        "constants": 0,
        "naming": 0,
        "modularity": 0,
        "comments": 0,
    }


def evaluate_dimension3_code_quality(code_path: Path | str) -> dict[str, Any]:
    target = Path(code_path)
    if not target.exists():
        return {
            "score": 0,
            "score_normalized": 0.0,
            "reason": f"代码文件不存在：{target}",
            "indicator_scores": _zero_indicator_scores(),
            "category_scores": {"structure": 0, "readability": 0, "maintainability": 0},
            "details": {},
        }

    source = _read_source(target)
    lines = source.splitlines()
    tree = _parse_source(source)
    if tree is None:
        return {
            "score": 0,
            "score_normalized": 0.0,
            "reason": "Python 语法错误，无法进行代码质量评估。",
            "indicator_scores": _zero_indicator_scores(),
            "category_scores": {"structure": 0, "readability": 0, "maintainability": 0},
            "details": {},
        }

    d1 = _indicator_1_complexity(source, tree)
    d2 = _indicator_2_reuse(tree, lines)
    d3 = _indicator_3_constants(tree, lines)
    d4 = _indicator_4_naming(tree)
    d5 = _indicator_5_modularity(tree)
    d6 = _indicator_6_comments(lines, tree)

    indicator_scores = {
        "complexity": d1["score"],
        "reuse": d2["score"],
        "constants": d3["score"],
        "naming": d4["score"],
        "modularity": d5["score"],
        "comments": d6["score"],
    }

    category_scores = {
        "structure": indicator_scores["modularity"] + indicator_scores["reuse"],
        "readability": indicator_scores["naming"] + indicator_scores["comments"],
        "maintainability": indicator_scores["constants"] + indicator_scores["complexity"],
    }

    total_score = sum(indicator_scores.values())

    return {
        "score": total_score,
        "score_normalized": total_score / 100.0,
        "reason": "评估完成：D3 使用静态工具化/AST 指标，无 LLM 参与。",
        "indicator_scores": indicator_scores,
        "category_scores": category_scores,
        "details": {
            "indicator_1_complexity": d1,
            "indicator_2_reuse": d2,
            "indicator_3_constants": d3,
            "indicator_4_naming": d4,
            "indicator_5_modularity": d5,
            "indicator_6_comments": d6,
        },
    }


def score_code_quality(
    has_docstring: bool = False,
    has_type_hints: bool = False,
    lint_errors: int = 0,
    code_path: Path | str | None = None,
) -> float:
    """基于代码文件的维度3评分接口。"""
    if code_path is not None:
        result = evaluate_dimension3_code_quality(code_path)
        return result["score_normalized"]
    raise ValueError("score_code_quality() requires code_path.")
