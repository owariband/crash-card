# Crash Card：学习方法依据与设计取舍

核查日期：2026-09-23；v2 设计依据补充于 2026-09-24。本次是为学习 Skill 服务的定向证据调研，覆盖自我解释、教别人、提取练习、反馈、间隔学习和 ADHD 学习支持；不是系统综述，也未声称穷尽全部研究。

## 结论先行

“费曼式解释”适合作为组织学习的骨架：**自己解释 → 发现缺口 → 补学 → 重新解释**。证据主要支持其组成机制，不能把流行四步骤、ADHD 适配和具体题数作为一套已充分验证的干预来宣传。本次未找到整套组合的直接验证；这不等于证明不存在相关研究。

本 Skill 的优化是：保留学习者主动解释，加入可核对的迁移题和答案反馈；用明确的当前任务降低启动负担，用完整解释和整体复述保持知识结构，用延迟复习区分当场表现和保持情况。

按学习状态选择方法：零基础用完整例题；说不清用自我解释；记不住用闭卷检索与间隔复习；答错用反馈修补；相近内容混淆时用对照，再在已学内容内进行少量混合练习。这是组合策略，不要求每个单元依次执行全部方法。

## 证据如何落到规则

| 设计决策 | 直接依据 | 推论与边界 |
|---|---|---|
| 由用户解释机制，助手找缺口 | Chi 等（1994）的自我解释实验；Koh 等（2018）的教学与检索比较 [1–2] | 支持主动生成解释；未直接检验这个聊天 Skill |
| 自检先回答，再看答案 | 一般学习者的检索实验 [3–4]；ADHD 大学生研究 [9] | ADHD 成效随材料与任务变化，不能保证所有题材都优于重读 |
| 反馈指出具体错处，正确但低把握也核对 | Butler 等（2008）[5] | 具体的反馈组织方式是交互设计；不宣称即时反馈在所有任务中最优 |
| 零基础或卡住先给完整例子 | Sweller 与 Cooper（1985）[7] | 早期代数实验支持支架；远迁移仍需单独检验 |
| 少干扰、短回合、书面下一步、可暂停 | NICE NG87 的环境调整建议 [8] | 一次一题、字数范围、续学卡是设计转译，不是指南验证的界面规格 |
| 分块后加整体解释 | Stern 与 Halamish（2023）[10] | 研究比较整体与分段回忆，未直接测试本 Skill 的组合；不能说越碎越好 |
| 答不出先补基础，再换题重测 | Minear 等（2023）[11] | 该研究提示检索收益不足以补偿初始编码不足；具体修补顺序是设计推论 |
| 间隔复习按表现调整 | Cepeda 等（2008）[6] | 最佳间隔与保持目标有关；次日／几天后／一周后只是可调整起点 |
| 会分别解题后，混合练习选择策略 | Taylor 与 Rohrer（2010）[12] | 支持训练题目与方法的匹配；非 ADHD 专属研究，也不意味着所有材料都应该混排 |

## 原始研究和官方指南

### [1] 自我解释

Chi, M. T. H., de Leeuw, N., Chiu, M.-H., & LaVancher, C.（1994）. *Eliciting Self-Explanations Improves Understanding*. Cognitive Science, 18, 439–477.

- 核实层级：出版商原始条目／摘要与元数据。
- 结果：24 名八年级学生中，被提示自我解释的组比重复阅读组获得更大的理解增益。
- 限制：样本小，循环系统文本，非 ADHD 研究；不能直接给出所有学科的效果大小。
- [出版商 DOI](https://doi.org/10.1207/s15516709cog1803_3)。该文另有旧 Elsevier DOI 入口，属于同一研究。

### [2] 教别人时的检索

Koh, A. W. L., Lee, S. C., & Lim, S. W. H.（2018）. *The learning benefits of teaching: A retrieval practice hypothesis*. Applied Cognitive Psychology, 32, 401–410.

- 核实层级：出版商提交到 Crossref 的摘要与元数据。
- 结果：一周后的理解测验中，不依赖笔记教学和检索练习组优于照笔记教学及控制组。
- 限制：支持检索是教学收益的一种机制，不证明所有教学收益都只来自检索；本次没有据全文核查样本细节。
- [DOI](https://doi.org/10.1002/acp.3410)；[出版商提交记录](https://api.crossref.org/works/10.1002/acp.3410)。

### [3] 当场熟悉与延迟保持

Roediger, H. L., & Karpicke, J. D.（2006）. *Test-Enhanced Learning: Taking Memory Tests Improves Long-Term Retention*. Psychological Science, 17, 249–255.

- 核实层级：期刊官方摘要。
- 结果：文本学习实验中，重复阅读在五分钟后的测验较好，先前回忆练习在两天或一周后的保持较好；反复阅读也提高了信心。
- 限制：不能凭当场流畅、自信判定保持效果；这不是 ADHD 专属试验。
- [期刊官方摘要](https://www.psychologicalscience.org/journals/psychological-science/j.1467-9280.2006.01693.x/)；DOI：10.1111/j.1467-9280.2006.01693.x。

### [4] 概念理解也需要主动回忆

Karpicke, J. D., & Blunt, J. R.（2011）. *Retrieval Practice Produces More Learning than Elaborative Studying with Concept Mapping*. Science, 331, 772–775.

- 核实层级：PubMed 收录原始摘要、作者机构论文入口。
- 结果：科学文本实验中，检索练习的优势也出现在理解和推理题上。
- 限制：不能据此断言概念图无用，或所有复杂任务都应只做检索；图示可作为讲解支架。
- [原始论文摘要](https://pubmed.ncbi.nlm.nih.gov/21252317/)；DOI：10.1126/science.1199327。

### [5] 正确答案也值得反馈

Butler, A. C., Karpicke, J. D., & Roediger, H. L.（2008）. *Correcting a metacognitive error: feedback increases retention of low-confidence correct responses*. Journal of Experimental Psychology: Learning, Memory, and Cognition, 34, 918–928.

- 核实层级：PubMed 收录原始摘要。
- 结果：两个一般知识实验中，反馈既帮助修正错误，也提高低信心正确答案的保持。
- 限制：题材和反馈形式特定；本 Skill 的逐要点核对、语义等价评分不是该研究直接验证的产品方案。
- [原始论文摘要](https://pubmed.ncbi.nlm.nih.gov/18605878/)；DOI：10.1037/0278-7393.34.4.918。

### [6] 复习间隔取决于要记多久

Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T., & Pashler, H.（2008）. *Spacing Effects in Learning: A Temporal Ridgeline of Optimal Retention*. Psychological Science, 19, 1095–1102.

- 核实层级：出版商原始摘要。
- 结果：超过 1,350 人的事实学习研究显示，有利的复习间隔随最终测试的延迟而改变。
- 限制：不支持人人使用固定的“1、3、7 天”处方，也不能精确预测个人何时遗忘。
- [出版商 DOI](https://doi.org/10.1111/j.1467-9280.2008.02209.x)。

### [7] 新手需要示例支架

Sweller, J., & Cooper, G. A.（1985）. *The Use of Worked Examples as a Substitute for Problem Solving in Learning Algebra*. Cognition and Instruction, 2, 59–89.

- 核实层级：出版商摘要。
- 结果：五项实验中，学习完整例题可节约学习时间，并改善后续同结构代数题的速度或错误表现。
- 限制：结构特异性明显；不能用类比和例题代替独立应用，更不能保证跨领域迁移。网页后来的上线日期不是研究年份。
- [出版商论文页](https://www.tandfonline.com/doi/abs/10.1207/s1532690xci0201_3)。

### [8] ADHD 的个体化环境调整

NICE（2018；本次核查当前在线版）. *Attention deficit hyperactivity disorder: diagnosis and management*, NG87，术语中的 Environmental modifications。

- 核实层级：官方指南条目。
- 内容：根据个人需要减少干扰，可采用较短专注阶段、活动休息和书面指令等调整。
- 限制：临床指南不等于对本聊天流程的教学效果验证；没有适合所有 ADHD 学习者的统一时长。
- [NICE 原文定位](https://www.nice.org.uk/guidance/ng87/chapter/recommendations#terms-used-in-this-guideline)。

### [9] ADHD 大学生的检索收益

Knouse, L. E., Rawson, K. A., Vaughn, K. E., & Dunlosky, J.（2016）. *Does Testing Improve Learning for College Students With Attention-Deficit/Hyperactivity Disorder?* Clinical Psychological Science, 4, 136–143.

- 核实层级：期刊官方摘要。
- 结果：ADHD 25 人、对照 75 人的分类词表学习实验，两天后两组均有中等大小的测试收益。
- 限制：样本与材料有限；不能从词表推断所有长篇文本、因果解释或真实课程成绩同样获益。
- [期刊官方摘要](https://www.psychologicalscience.org/journals/clinical/2167702614565175/)；DOI：10.1177/2167702614565175。

### [10] 分块不应丢失整体

Stern, P., & Halamish, V.（2023）. *Free-recall retrieval practice tasks for students with ADHD: whole-text versus section recall*. Frontiers in Psychology, 14, 1301726.

- 核实层级：开放全文。
- 结果：72 人，其中 ADHD 36 人。逐段回忆在练习时回忆更多；两天后的整篇回忆条件优于逐段回忆条件，两种回忆条件均未显著优于重读。
- 限制：特定短文、两天延迟、未预注册；不能把这项结果理解为取消分块讲解。加入整体复述是本 Skill 的设计推论。
- [原始全文](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2023.1301726/full)；DOI：10.3389/fpsyg.2023.1301726。

### [11] 检索收益不能替代初始学习

Minear, M. E., Coane, J. H., Cooney, L. H., Boland, S. C., & Serrano, J. W.（2023）. *Is practice good enough? Retrieval benefits students with ADHD but does not compensate for poor encoding in unmedicated students*. Frontiers in Psychology, 14, 1186566.

- 核实层级：开放全文与 PubMed 元数据。
- 结果：ADHD 与对照各 36 人，学习斯瓦希里语—英语词对；带反馈的检索有益，但未补偿部分参与者较差的初始编码。
- 限制：诊断自报，词对任务，亚组结果不能普遍化；不据此作任何用药建议。“补术语／前提再重测”是教学设计推论。
- [原始全文](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2023.1186566/full)；DOI：10.3389/fpsyg.2023.1186566。

### [12] 混合练习帮助选择合适的方法

Taylor, K., & Rohrer, D.（2010）. *The Effect of Interleaving Practice*. Applied Cognitive Psychology, 24, 837–848.

- 核实层级：作者机构收录的原始摘要与元数据。
- 结果：儿童练习四类数学题，研究控制了练习间隔。混合练习的当场表现较差，但次日测试更好；错误分析提示收益与把题目匹配到恰当解法有关。
- 限制：特定数学任务、一天延迟，非 ADHD 专属试验，不能把混合无关学科等同于这种练习。“基本题已能完成才增加混合题”是降低启动负担的设计选择，不是该研究确立的最佳门槛。
- [作者机构原始摘要](https://digitalcommons.usf.edu/psy_facpub/1760/)；DOI：10.1002/acp.1598。

补充核查：Rohrer, D., Dedrick, R. F., & Stershic, S.（2015）. *Interleaved Practice Improves Mathematics Learning*. Journal of Educational Psychology, 107, 900–908。原文报告 126 名七年级学生的课堂研究，交错条件在一天与三十天后测试均更好；流程先教学、给少量同类题，再交错其余练习，并持续纠错。它支持在已教内容中混合练习，不支持把讲授也打散或彻底取消集中练习。该研究同样不是 ADHD 专属试验。[作者提交的原文](https://files.eric.ed.gov/fulltext/ED557355.pdf)。

## 明确属于设计选择的参数

一次一个主要待答任务、卡片版式、字号、学习状态分类，以及复习起始时间，均为可调整的设计选择。v2 不设每段字数、每卡要点数或每主题题数。完整的前提、推理和例子决定所需篇幅；层级和导航帮助阅读，短段落本身不是学习目标。

“没有遗留问题”在本方案中的可执行含义是：本次范围内的显式问题、必要前置知识与已暴露误解均有交代，已讲与已掌握分开记录。待核验事实或未通过的能力必须展示，不能用隐藏缺口或无限加题制造完成感。


## v2 补充：教学预期与可访问排版

Kobayashi（2024）的以教促学研究综合将教学预期作为影响因素。本 Skill 因此在学习前说明稍后要解释的目标；这一设计不证明对每种材料或 ADHD 学习者都有同样效果。[出版商论文页](https://link.springer.com/article/10.1007/s10648-024-09871-4)。

W3C 的认知可访问性指导建议清楚的语言、易定位的信息和一致视觉设计；v2 据此使用稳定导航、连贯段落、明确标题与适量留白。其“简洁文本”指导不构成删去必要知识的依据。1200×1600、约 400 px 预览、字号及六类版式是产品参数，不是临床或学习效果结论。[简洁文本指导](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p05-succinct-text/)、[一致视觉设计](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o1p03-consistent-design/)。

PNG 保留用户要求的分享与复习形式；文字稿从同一数据导出，补充搜索与朗读。图片文字不能随着用户字体设置自动重排，故同时检查缩小预览并提供文本，不以文本替代请求的三类 PNG。[W3C 图片文字说明](https://www.w3.org/WAI/WCAG22/Understanding/images-of-text.html)。
