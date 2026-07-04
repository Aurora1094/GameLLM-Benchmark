# Related Work / 设计依据（ICLR 写作用）

本文件把新 prompt 架构的每一个设计决定，锚定到已核实的文献上。
每节给出：① 文献结论 ② 撑住哪个设计 ③ 可直接改写进论文的英文草段。
BibTeX 见 references.bib（所有条目标题/作者/年份/编号均已核对）。

## 定位（novelty 该怎么措辞）
我们的贡献**不是**又一种 prompting 技巧（非 CoT 那类方法），而是一个面向
**多模型、多任务公平基准**的 prompt **架构**。它把"构念效度"(construct
validity) 显式操作化为三条可辩护的工程约束：
(i) 骨架不变量；(ii) 功能可验证规格；(iii) 拒绝泄漏质量评分标准以避免构念污染。

> Draft (positioning): *We do not propose a new prompting technique; rather, we
> contribute a prompt **architecture** for fair multi-model, multi-task
> code-generation benchmarking. It operationalizes construct validity through
> three constraints: an invariant scaffold, a verifiable functional
> specification, and the deliberate withholding of quality rubrics to prevent
> construct contamination.*

---

## 1. 元框架：基准分是一次测量，效度取决于操作化
**Jacobs & Wallach (2021), *Measurement and Fairness*, FAccT '21.**

① 该文把量化社会科学的"测量建模"引入计算系统：不可观测的**构念**
(construct) 只能通过可观测属性的**操作化**间接测得；操作化引入的假设可能
造成"想测的构念"与"实际测的东西"之间的错配，即**构念无关方差**
(construct-irrelevant variance)，这是效度的首要威胁。

② 我们的基准分操作化了一个不可观测构念——"模型生成游戏的能力"。整套 prompt
架构本质是一次**构念效度干预**：凡是与该构念无关、却会影响分数的因素
（prompt 格式、是否泄题、规格是否残缺），都要被设计消除。这是统领后面
三节的元论证。

> Draft: *Following measurement-modeling accounts of validity
> (Jacobs & Wallach, 2021), a benchmark score operationalizes an unobservable
> construct—here, a model's game-generation capability. Threats to validity
> arise from construct-irrelevant variance introduced during operationalization;
> our prompt design targets three such sources.*

---

## 2. 不变量：LLM 对保义的 prompt 改动极度敏感
**Sclar, Choi, Tsvetkov & Suhr (2024), *Quantifying Language Models'
Sensitivity to Spurious Features in Prompt Design*, ICLR 2024.**

① 该文证明多个主流开源 LLM 对**保义** (meaning-preserving) 的 prompt 格式
改动极度敏感，在 few-shot 设置下 LLaMA-2-13B 上不同格式的性能差距可达约
76 个准确率点；增大模型、增加示例、指令微调都不能消除这种敏感性。

② 这直接论证我们的**骨架不变量**：main.md 对同难度所有游戏、所有被测模型
**逐字节一致**，唯一变量是 spec 数据。若每个游戏各写各的 prompt，格式方差
会与模型能力方差混淆——无法判断"模型 A 优于 B"还是"prompt A 优于 B"。
占位符架构把骨架变成受控常量，把游戏规格变成唯一被操纵的变量。

> Draft: *Because LLMs are highly sensitive to meaning-preserving prompt
> perturbations (Sclar et al., 2024), any per-game or per-model variation in the
> prompt scaffold would confound model comparison with format effects. We
> therefore hold a single scaffold byte-identical across all games of a
> difficulty and all models, exposing only the game specification as the
> manipulated variable.*

---

## 3. 双刃：可验证指令是好评测，但"指令遵循"是独立构念
**Zhou, Lu, Mishra, Brahma, Basu, Luan, Zhou & Hou (2023), *Instruction-
Following Evaluation for Large Language Models (IFEval)*, arXiv:2311.07911.**

① IFEval 提出**可验证指令** (verifiable instructions)——可被代码客观判定
是否遵守的原子指令（如"至少 400 词"），以此实现**可复现、无偏**的评测；
文中亦明确指出基于 LLM 的自动评测"可能有偏或受评测模型能力限制"。
关键在于：IFEval 测的是**指令遵循这一构念本身**。

② 两处支撑，一正一反：
- **正**：我们的 D1 就是一组可验证指令（语法、导入、建窗、事件循环、
  稳定运行、可退出），全部机械判定——与 IFEval 的哲学一致，天然可复现。
- **反（更关键）**：正因为"指令遵循"是独立构念，当我们**想测代码质量
  (D3/D4)** 时就绝不能误测成指令遵循。若把 D3/D4 的评分标准
  （用常量、控制复杂度……）枚举进 prompt，遵从的模型都会照做，D3 便塌缩为
  一次指令遵循测量——构念污染。故质量维 guidance 刻意泛化：我们要测的是
  模型的**自发**质量，不是它的遵从度。

> Draft: *Verifiable instructions enable objective, reproducible evaluation
> (Zhou et al., 2023); our executability dimension is exactly such a battery,
> checked mechanically. Crucially, IFEval also establishes instruction-following
> as a construct in its own right. Enumerating our code-quality criteria in the
> prompt would therefore collapse the quality dimensions into an
> instruction-following measurement—a construct-validity failure. We keep
> quality guidance deliberately generic so as to measure spontaneous quality
> rather than compliance.*

---

## 4. 领域锚点：从 spec 到功能正确性
**Chen et al. (2021), *Evaluating Large Language Models Trained on Code*
(Codex / HumanEval), arXiv:2107.03374.**

① HumanEval 确立了代码生成评测范式：从自然语言 spec（docstring）合成程序，
以**功能正确性**为度量。其 docstring 既是喂给模型的 spec，也是驱动评测的
依据。

② 两点对应：
- D2 checkpoint 把"单函数正确"推广到"整局游戏功能完整"——同一功能正确性
  精神，扩展到有状态、有交互、有终止条件的完整程序。
- checkpoint 的**单一真源**（既喂 prompt 又驱动 D2）正对应 HumanEval 里
  docstring 的双重角色：喂模型和评分用的是同一份规格，天然对齐。

> Draft: *Functional-correctness evaluation from a natural-language
> specification is the canonical paradigm for code generation
> (Chen et al., 2021). Our functionality checkpoints extend this from
> single-function correctness to whole-game functional completeness, and—mirroring
> HumanEval's docstring, which is both the prompt and the grading target—we
> derive the model-facing spec and the grader from a single source.*

---

## 5. 结构本体：prompt 分区不是随手写的
**Schulhoff et al. (2024), *The Prompt Report: A Systematic Survey of
Prompting Techniques*, arXiv:2406.06608.**

① 该综述系统梳理了 prompt 的组件本体与技术分类（directive、context、
output-formatting、role 等）。

② 论证 main.md 的**内部分区**（角色设定 / 运行要求 / 游戏规格 /
代码与体验 / 输出格式）对齐成文的组件本体，而非临时拼凑——提升方法的
可复述性与可复现性。

> Draft: *The internal structure of our scaffold (role, directive, functional
> specification, quality guidance, output constraint) follows established prompt
> component taxonomies (Schulhoff et al., 2024), aiding reproducibility.*

---

## 6. 诚实的局限与建议做的消融（reviewer 会加分）
- **质量维泛化的代价**：一句话的 D3/D4 引导可能**一致地**压低所有模型的
  UX 投入，压缩 D4 方差。建议消融：A/B 对比"泄漏 vs 不泄漏 D3/D4 标准"，
  量化构念污染的真实幅度——这本身就是一个可发表的小结果。
- **骨架跨难度不变的假设**：假定同一骨架对不同难度不产生差异性偏好。
  建议做一次本任务上的 mini-Sclar 复现：扰动骨架格式，测本基准的 prompt
  敏感度，给不变量选择提供实证支撑。
- **单点估计噪声**：LLM 生成随机，每 (model, game) 若只生成一次，排名不稳。
  建议 N 次取均值±std 或 pass@k（呼应 Chen et al. 2021 的重复采样）。
