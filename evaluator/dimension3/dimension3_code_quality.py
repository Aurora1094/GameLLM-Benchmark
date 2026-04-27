from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path
from typing import Any
import warnings


RESPONSIBILITY_KEYWORDS = {
    "update",
    "draw",
    "render",
    "handle",
    "input",
    "spawn",
    "collision",
    "score",
    "reset",
}

BAD_NAMES = {"a", "b", "x", "tmp", "var", "data"}
IGNORED_MAGIC_NUMBERS = {0, 1, -1}


def _read_source(code_path: Path) -> str:
    return code_path.read_text(encoding="utf-8-sig", errors="ignore").lstrip("\ufeff")


def _parse_source(source: str) -> ast.AST | None:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _numeric_value(node: ast.AST) -> int | float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _numeric_value(node.operand)
        if inner is None:
            return None
        return -inner
    return None


def _line_bounds(node: ast.AST) -> tuple[int, int]:
    start = getattr(node, "lineno", 0)
    end = getattr(node, "end_lineno", start)
    return start, end


# =========================
# 指标 1：模块划分（20）
# =========================
def _indicator_1_modularity(tree: ast.AST) -> dict[str, Any]:
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    num_functions = len(functions)
    num_classes = len(classes)

    # 子项 A：函数规模（10分）
    if num_functions == 0:
        function_scale_score = 0
    elif 1 <= num_functions <= 3:
        function_scale_score = 3
    elif 4 <= num_functions <= 8:
        function_scale_score = 7
    elif 9 <= num_functions <= 20:
        function_scale_score = 10
    elif 21 <= num_functions <= 40:
        function_scale_score = 8
    else:
        function_scale_score = 6

    # 子项 B：类结构（5分）
    if num_classes == 0:
        class_structure_score = 0
    elif 1 <= num_classes <= 2:
        class_structure_score = 3
    elif 3 <= num_classes <= 6:
        class_structure_score = 5
    else:
        class_structure_score = 4

    # 子项 C：职责分离（5分）
    function_names = [f.name.lower() for f in functions]
    responsibility_hits = 0
    for keyword in RESPONSIBILITY_KEYWORDS:
        if any(keyword in fn for fn in function_names):
            responsibility_hits += 1

    if responsibility_hits <= 1:
        responsibility_score = 0
    elif responsibility_hits <= 3:
        responsibility_score = 2
    elif responsibility_hits <= 5:
        responsibility_score = 4
    else:
        responsibility_score = 5

    score = function_scale_score + class_structure_score + responsibility_score
    score = min(20, score)

    return {
        "score": score,
        "num_functions": num_functions,
        "num_classes": num_classes,
        "responsibility_hits": responsibility_hits,
        "function_scale_score": function_scale_score,
        "class_structure_score": class_structure_score,
        "responsibility_score": responsibility_score,
    }


# =========================
# 指标 2：代码复用（20）
# =========================
def _indicator_2_reuse(tree: ast.AST, source_lines: list[str]) -> dict[str, Any]:
    # 行级重复：去掉空行和纯注释行后做频次统计。
    trivial_lines = {"pass", "return", "return none", "continue", "break"}
    effective_lines = []
    for raw in source_lines:
        # 去掉行内注释后再统计，避免同一语句因注释不同被误判成不重复。
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        # 忽略低信息量语句，降低误罚概率。
        if line.lower() in trivial_lines:
            continue
        effective_lines.append(line)

    total_effective = len(effective_lines)
    counter = Counter(effective_lines)
    duplicated_lines = sum(count - 1 for count in counter.values() if count > 1)
    duplicate_ratio = duplicated_lines / total_effective if total_effective > 0 else 0.0

    if duplicate_ratio > 0.3:
        base_score = 0
    elif duplicate_ratio > 0.2:
        base_score = 8
    elif duplicate_ratio > 0.1:
        base_score = 15
    else:
        base_score = 20

    # 复用加分：有自定义函数被调用次数 >=2。
    defined_funcs = {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    call_counter: Counter[str] = Counter()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in defined_funcs:
            call_counter[node.func.id] += 1

    reused_func_count = sum(1 for _, c in call_counter.items() if c >= 2)
    bonus = 2 if reused_func_count > 0 else 0

    score = min(20, base_score + bonus)
    return {
        "score": score,
        "duplicate_ratio": duplicate_ratio,
        "duplicated_lines": duplicated_lines,
        "effective_lines": total_effective,
        "reused_func_count": reused_func_count,
        "base_score": base_score,
        "bonus": bonus,
    }


# =========================
# 指标 3：命名规范（15）
# =========================
def _is_good_name(name: str) -> bool:
    n = name.strip().lower()
    if len(n) < 2:
        return False
    if n in BAD_NAMES:
        return False
    return True


def _indicator_3_naming(tree: ast.AST) -> dict[str, Any]:
    names: list[str] = []

    # 变量名：仅收集赋值上下文，避免把所有引用都重复计数。
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.append(node.id)
        if isinstance(node, ast.arg):
            names.append(node.arg)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)

    # 去重后再评分，避免同名变量多次赋值导致统计偏差。
    names = sorted(set(names))

    total_names = len(names)
    if total_names == 0:
        ratio = 0.0
        score = 0
        good_names = 0
    else:
        good_names = sum(1 for n in names if _is_good_name(n))
        ratio = good_names / total_names
        if ratio > 0.8:
            score = 15
        elif ratio > 0.6:
            score = 10
        elif ratio > 0.4:
            score = 6
        else:
            score = 0

    return {
        "score": score,
        "total_names": total_names,
        "good_names": good_names,
        "ratio": ratio,
    }


# =========================
# 指标 4：注释质量（15）
# =========================
def _effective_comment_lines(source_lines: list[str]) -> int:
    # 防“连续注释刷分”：每个连续注释块最多计 2 行。
    count = 0
    run = 0
    for raw in source_lines:
        stripped = raw.strip()
        if stripped.startswith("#"):
            run += 1
            continue

        if run > 0:
            count += min(run, 2)
            run = 0

    if run > 0:
        count += min(run, 2)
    return count


def _docstring_line_count(tree: ast.AST) -> int:
    # 将模块/函数/类 docstring 折算为注释行，避免漏计说明性文档。
    total = 0
    holders = [tree]
    holders.extend(
        n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    )

    for holder in holders:
        body = getattr(holder, "body", None)
        if not body:
            continue
        first_stmt = body[0]
        if not isinstance(first_stmt, ast.Expr):
            continue

        value = first_stmt.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            start = getattr(first_stmt, "lineno", 0)
            end = getattr(first_stmt, "end_lineno", start)
            total += max(1, end - start + 1)

    return total


def _indicator_4_comments(source_lines: list[str], tree: ast.AST) -> dict[str, Any]:
    total_lines = len(source_lines)
    hash_comment_lines = _effective_comment_lines(source_lines)
    docstring_lines = _docstring_line_count(tree)
    comment_lines = hash_comment_lines + docstring_lines
    ratio = comment_lines / total_lines if total_lines > 0 else 0.0

    if ratio > 0.1:
        score = 15
    elif ratio > 0.05:
        score = 10
    elif ratio > 0.02:
        score = 5
    else:
        score = 0

    return {
        "score": score,
        "comment_lines": comment_lines,
        "hash_comment_lines": hash_comment_lines,
        "docstring_lines": docstring_lines,
        "total_lines": total_lines,
        "ratio": ratio,
    }


# =========================
# 指标 5：常量使用（15）
# =========================
def _count_constants_and_magic(tree: ast.AST) -> tuple[int, int]:
    constants_count = 0
    constant_values: set[int | float] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id.isupper() for t in node.targets):
                constant_value = _numeric_value(node.value)
                if constant_value is not None:
                    constants_count += 1
                    constant_values.add(constant_value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id.isupper():
                constant_value = _numeric_value(node.value)
                if constant_value is not None:
                    constants_count += 1
                    constant_values.add(constant_value)

    magic_numbers = 0
    for node in ast.walk(tree):
        value = _numeric_value(node)
        if value is None:
            continue
        if value in IGNORED_MAGIC_NUMBERS:
            continue

        # 如果该数字值已被抽象为常量，则不再记为 magic number。
        if value in constant_values:
            continue

        magic_numbers += 1

    return constants_count, magic_numbers


def _indicator_5_constants(tree: ast.AST) -> dict[str, Any]:
    constants_count, magic_numbers = _count_constants_and_magic(tree)
    ratio = constants_count / (magic_numbers + 1)

    if ratio > 0.7:
        score = 15
    elif ratio > 0.4:
        score = 10
    elif ratio > 0.2:
        score = 5
    else:
        score = 0

    return {
        "score": score,
        "constants_count": constants_count,
        "magic_numbers": magic_numbers,
        "ratio": ratio,
    }


# =========================
# 指标 6：复杂度控制（15）
# =========================
def _max_nesting_depth_in_node(node: ast.AST) -> int:
    control_nodes = (ast.If, ast.For, ast.While, ast.AsyncFor)

    def walk(node: ast.AST, depth: int) -> int:
        next_depth = depth + 1 if isinstance(node, control_nodes) else depth
        best = next_depth
        for child in ast.iter_child_nodes(node):
            best = max(best, walk(child, next_depth))
        return best

    return walk(node, 0)


def _max_function_nesting_depth(functions: list[ast.AST]) -> int:
    # 复杂度深度只在函数内部计算，避免顶层控制流污染评分。
    if not functions:
        return 0
    return max(_max_nesting_depth_in_node(fn) for fn in functions)


def _indicator_6_complexity(tree: ast.AST) -> dict[str, Any]:
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

    max_func_length = 0
    for fn in functions:
        start, end = _line_bounds(fn)
        fn_len = max(0, end - start + 1)
        max_func_length = max(max_func_length, fn_len)

    max_depth = _max_function_nesting_depth(functions)

    score = 15
    if max_func_length > 50:
        score -= 5
    if max_depth > 4:
        score -= 5
    if max_func_length > 80:
        score -= 5
    score = max(0, score)

    return {
        "score": score,
        "max_func_length": max_func_length,
        "max_depth": max_depth,
    }


def evaluate_dimension3_code_quality(code_path: Path | str) -> dict[str, Any]:
    target = Path(code_path)
    if not target.exists():
        return {
            "score": 0,
            "score_normalized": 0.0,
            "reason": f"代码文件不存在：{target}",
            "indicator_scores": {
                "modularity": 0,
                "reuse": 0,
                "naming": 0,
                "comments": 0,
                "constants": 0,
                "complexity": 0,
            },
            "category_scores": {
                "structure": 0,
                "readability": 0,
                "maintainability": 0,
            },
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
            "indicator_scores": {
                "modularity": 0,
                "reuse": 0,
                "naming": 0,
                "comments": 0,
                "constants": 0,
                "complexity": 0,
            },
            "category_scores": {
                "structure": 0,
                "readability": 0,
                "maintainability": 0,
            },
            "details": {},
        }

    # 1) 模块划分
    d1 = _indicator_1_modularity(tree)

    # 2) 代码复用
    d2 = _indicator_2_reuse(tree, lines)

    # 3) 命名规范
    d3 = _indicator_3_naming(tree)

    # 4) 注释质量
    d4 = _indicator_4_comments(lines, tree)

    # 5) 常量使用
    d5 = _indicator_5_constants(tree)

    # 6) 复杂度控制
    d6 = _indicator_6_complexity(tree)

    indicator_scores = {
        "modularity": d1["score"],
        "reuse": d2["score"],
        "naming": d3["score"],
        "comments": d4["score"],
        "constants": d5["score"],
        "complexity": d6["score"],
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
        "reason": "评估完成。",
        "indicator_scores": indicator_scores,
        "category_scores": category_scores,
        "details": {
            "indicator_1_modularity": d1,
            "indicator_2_reuse": d2,
            "indicator_3_naming": d3,
            "indicator_4_comments": d4,
            "indicator_5_constants": d5,
            "indicator_6_complexity": d6,
        },
    }


def score_code_quality(
    has_docstring: bool = False,
    has_type_hints: bool = False,
    lint_errors: int = 0,
    code_path: Path | str | None = None,
) -> float:
    """兼容旧接口，同时支持基于代码文件的维度3评分。

    - 旧接口（main_evaluator 当前调用方式）：
      score_code_quality(has_docstring=True, has_type_hints=True, lint_errors=0)
    - 新接口：
      score_code_quality(code_path="path/to/code.py")
    """
    if code_path is not None:
        result = evaluate_dimension3_code_quality(code_path)
        return result["score_normalized"]

    # 旧逻辑保留，避免破坏现有调用。
    warnings.warn(
        "score_code_quality() 未传入 code_path，已回退到旧版占位评分逻辑。"
        "建议改为 score_code_quality(code_path=...) 以使用维度3正式评分规则。",
        RuntimeWarning,
        stacklevel=2,
    )
    base = 0.4
    if has_docstring:
        base += 0.2
    if has_type_hints:
        base += 0.2
    base -= min(0.4, lint_errors * 0.05)
    return max(0.0, min(1.0, base))
