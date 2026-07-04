# prompts/

把游戏描述从"投喂材料"升级为**结构化 prompt 架构**：一个不变的骨架
(main.md) + 每游戏结构化 spec，通过占位符切换。

## 文件
- `main.md` — 唯一 prompt 骨架，含占位符。**不变量**：同难度所有游戏、
  所有模型逐字节一致，只有 spec 数据变。
- `specs/SCHEMA.md` — 每游戏 spec 的 frontmatter 规范。
- `specs/easy/pong.md` — 一个跑通的示例 spec。
- `builder_spec.md` — **给 Codex 的实现任务书**：prompt_builder 契约、
  校验、留档、与 D2 的单一真源接线。
- `DESIGN_REVIEW.md` — 设计审视结论（功能维显式 / 质量维克制 /
  单一真源 / 不变量）。
- `RELATED_WORK.md` — ICLR 写作用：五篇文献如何撑住每个设计决定
  + 可改写的英文草段 + 建议消融。
- `references.bib` — 已核对的 BibTeX。

## 给 Codex 的一句话任务
按 `builder_spec.md` 实现 prompt_builder：读 `main.md` + `specs/<difficulty>/<game>.md`，
校验并注入占位符，缺值即 fail-fast，落盘最终 prompt，且让 D2 评估器从
同一个 spec 文件读 checkpoints。骨架文案一律不动。

## 三条不可违反的约束（否则破坏基准效度）
1. 骨架不变量（Sclar et al. 2024）。
2. 功能维显式写全但不抄评估器内部；质量维按论文顺序覆盖但不泄漏实现
   （Zhou et al. 2023；Jacobs & Wallach 2021）。
3. checkpoint 单一真源：prompt 与 D2 读同一份数据（对应 Chen et al. 2021
   中 docstring 的双重角色）。
