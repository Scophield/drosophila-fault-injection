# Prepublication revision report (historical check state)

# V10 有限科学贡献修订与核验

## 对象与版本边界

完整读取的最新 ScienceGuru 报告是本目录 `ScienceGuru_latest_review.txt`，不是上一版工具叙事的旧审稿报告。它指向原 science candidate，PDF SHA256 为 `536ede47297f2c561fa44ad86fe1adaae8dbd5c9852db4f182a322c4057d731c`。报告文件 SHA256 为 `6638dfa8197494c0f9819105fd4f317223464038acb4cd66d913db638b02da44`。

本轮分支：`research/iscas2027-v10-horizon-evidence`。工作树原有 V10 改动全部保留；没有 commit、push、main 更新或 Release。新候选独立保存为：

`output/v10-horizon-candidate/iscas2027-v10-horizon-candidate.pdf`

SHA256：`7ac89fa92507d6529db773d0320821c4556e32d1c0fe1b8a4ceb4ad40eb319e1`。

修改前已将 177 个候选稿、视觉资产及相关源码文件备份到项目外：

`<local-workspace>/drosophila-research-backups/20261025-v10-before-horizon-01`

逐文件哈希见 `before.json`。其中 175 个保持原样；仅原接口 `evidence_v10/contract.py` 和接口说明 `docs/EVIDENCE_INTERFACE_V10.md` 在原路径修复。论文在新文件中修订，原 science PDF、LaTeX、Blender 资产均未覆盖。

## 新增的具体知识及证据身份

| 判定时域，RF-0/50% 删除 | P 无接触 | R 无接触 | 描述性成功率差 R−P |
|---|---:|---:|---:|
| 900 ms | 46/48（95.83%） | 48/48（100%） | +4.17 pp |
| 1000 ms | 37/48（77.08%） | 48/48（100%） | +22.92 pp |

这两行来自**同一批** 24 个独立 seed 簇，每律含两个方位的 48 条轨迹。它们不是两个独立样本、不是新增确认性检验，也不改变预注册的 1 s 终点。2 次 P 接触在 900 ms 以前，另 9 次在最后 100 ms，最晚一次为 999.961740 ms。R 在 1 s 内没有接触，不能由此推断 1 s 以后持续安全。

程序 `tools/plot_horizon_v10.py` 先核验原 288 条 RF-0 记录的 SHA256，再选择 96 条 P/R、50% 删除记录，核对每对的 mask/uniform 摘要及健康参考成功。输出位于 `output/v10-horizon-candidate/horizon-04/`：

- `first-contacts.csv`：全部 96 条轨迹、首次接触时刻、seed、方位、输入/掩码摘要及来源哈希。
- `horizon-counts.csv`：上述两行判定汇总。
- `curve-points.csv`：经验累计首次接触曲线的全部阶梯点。
- `check.json`：脚本、原图、原始输入和原汇总的哈希，以及 Python/NumPy/Matplotlib 版本。

没有估计新的置信区间或 p 值，没有调整阈值、筛 seed、重跑神经模型或增加样本。原始统计文件未改写。

主要贡献段由“完成了配对评价、接口和预警测试”的工作清单，改为三项可核查所得：同轨迹的首次接触时域差异及不确定 RF 迁移、冻结标量预警的实际错配、可执行证据约束与有限跨 plant 复用。英文原文逐段对照见 `CONTRIBUTIONS_BEFORE_AFTER.md`。

## 最新审稿意见逐项解决表

| 意见 | 实际处理 | 状态与尚存边界 |
|---|---|---|
| B1：科学贡献过于笼统 | Introduction 末段列出 2/48→11/48、11/13 漏报及有界接口能力；摘要与结论对应同一问题 | 表述与数据联系已强化；没有因此获得连接组特异机制或普适保护原则 |
| B2：健康裕量及终点限制 | Fig.3 新增 d 面板；IV-A 给出两个时域和最晚接触；将健康净空 33.1/41.4 mm、400 ms 航向 88.3°/100°与晚期接触共同讨论 | 同记录复算已确认；这些只是可能贡献因素，未隔离因果作用 |
| B2：RF-A/B 解释过强风险 | 保留各 −4.2 pp、95% CI [−12.5,0]、每图仅一个非零对比簇、四项 Holm p=1；明确没有 between-map 效应变化检验 | 不宣称 RF 单独导致减弱；不显著不构成等效 |
| B3：预警结论太宽 | IV-B 改为 “Frozen Scalar Warnings Miss Subsequent Contacts”；首句限定实际冻结操作点，保留精确状态预测器的信息优势 | 只支持所测标量判据的局限，不否定其他神经预测器 |
| SHOULD-FIX：非法输入会崩溃 | 原样复现 null uniform、数值 mask、list seed 的三个 TypeError；在通用集合/正则操作前加入类型、key 可哈希性验证，提供带原 row 编号的 schema issue | 三例及两适配器/混合批次回归通过；不是任意对象的完备解析器 |
| SHOULD-FIX：尽早给出独立簇数 | 摘要前部注明 48 项任务来自 24 个独立簇；Fig.3(d) 图内、图注均注明重复计分 | 没有把方向、律或时域当作独立重复 |
| SHOULD-FIX：指标身份 | 保留原 Methods：primary L/G/activity、derived D、prespecified secondary 对比/预警、post-hoc clearance/heading；新时域分析明确 descriptive | 未将 secondary 提升为 primary，未改变预注册 |
| Related Work 的直接区别 | 分别说明 Shiu 的模型先例、An 的稀疏化任务依赖、Jo 的损伤/虚拟行为及损伤辨识、DriveFI 的闭环违例搜索 | 本文增量限定为配对首次碰撞、显式时域、400 ms 前缀预测和具体可执行审计；没有增加首创性主张 |
| 神经任务晚于工具细节 | 神经实验与统计设计提前为 II，证据契约后移为 III | Methods 科学定义文字完整保留；IV 仍是结果 |
| 压缩水箱/历史辩护 | 契约段由 319 降至 222 个计数 token；保留方程、安全范围、样本结构、150 ms 延迟、11+3 挑战和 logger 反例 | 96 项均安全的有限复用性质保留；没有伪称性能对照 |
| 原历史六簇 p=0.25 与个案篇幅 | 不再占当前主文；原 science candidate、历史报告、原始数据和事后 seed1010 图均原样保留 | 不是删除不利数据，也没有把历史探索性分析改称新确认性结果；当前 25% p=0.50 与新增 RF 阴性结果仍在正文 |
| 字体、主图及版面 | 保持四图；新累计接触仅加入 Fig.3(d)，不另加第五张图 | 4 页技术内容＋第 5 页参考文献，无缩字体/改页边距 |
| 结尾后续方向 | 保留用户已确认的 future device-level nonidealities 句子 | 不暗示已经开展器件级故障实验 |

## 图表与视觉保护

Fig.1、Fig.2、Fig.4 使用原 PDF，全部 Blender 文件、渲染图和相关资产哈希不变。Fig.3(a–c) 的原向量页以原宽和原高嵌入新组合图；`figure3-preservation.json` 记录在同一分辨率下尺寸相同、像素完全一致、最大像素差为 0。

原 PDF 与新 PDF 内的全部栅格图像摘要、像素尺寸及显示宽高完全相同；没有重新渲染、降低分辨率或替换 Blender 内容。新旧逐页对照在 `page-comparisons/page-1.png` 至 `page-5.png`。已逐页查看最终原生 Poppler 渲染：图 3 新面板、两端计数和图注可读，无明显重叠或裁切。

正文计数采用统一规则：去掉章节标题和 cite 命令后按空白分词，数学 token 保留（不是自然语言词数估计）。摘要 142→150，Introduction 246→282，Results 410→429，Scope/Conclusion 233→201，Contract 319→222；五部分合计 1350→1284，减少 66 个 token。Methods 文本未变。

## 代码可靠性与测试

修复之前，三个指定非法输入均产生 TypeError，见 `schema-before.json`。修复后它们在 tank 及真实 saved-fly schema 上成为 `native-schema` 或直接入口的 `record-schema`；批次中合法行继续检查，缺失矩阵单元仍被报告。`success='yes'` 等非布尔值不再被当成合法标签。也测试了坏行与其他记录的时序错误同时存在，以及极大数值帧字段。

命令（Python 为本机已存在的 CPython 3.12 环境，经仓库 launcher 使用已有依赖；无安装）：

```text
python -X utf8 tools/run_v9.py -m unittest discover -s tests -p "test_evidence*v10.py" -v
python -X utf8 tools/run_v9.py tools/check_evidence_v10.py --out audit/science-contribution-20261025-01/evidence-regression-01
python -X utf8 tools/run_v9.py tools/plot_horizon_v10.py --out output/v10-horizon-candidate/horizon-04
```

20 个测试方法全部通过。完整原回归对 288 条 fly 记录和 96 条 tank 示例均返回零问题；每适配器原定 14 类挑战仍分别为 11 类 common checker、3 类 native replay 检出。新类型测试不计入原 14 类，不构成检错覆盖率。tank 回归的重复运行不是新的独立科学队列。

零神经执行 logger 反例仍通过，`neural_dynamics_executed=false`。这是有意保留的能力边界，不能把 schema 修复等同于神经执行认证、任意数据真实性验证或安全证明。

## 编译、引用和工件核验

```text
powershell -File tools/build_v10.ps1 -SourceFile main_v10_horizon.tex -BuildDirectory output/v10-horizon-candidate/build-02
python -X utf8 tools/run_v9.py tools/qa_pdf.py --pdf output/v10-horizon-candidate/build-02/main.pdf --out audit/science-contribution-20261025-01/qa-02 --submission
python -X utf8 tools/run_v9.py tools/render_v10.py --pdf output/v10-horizon-candidate/build-02/main.pdf --out audit/science-contribution-20261025-01/native-main-01 --main
python -X utf8 tools/run_v9.py audit/science-contribution-20261025-01/validate_and_package.py
```

主编译及 native rendering 成功记录保存在构建目录和 JSON；`qa-run-final.txt` 保存独立文本/字体检查结果。最终 PDF 为 3,393,378 字节、5 页 Letter；技术内容止于第 4 页，第 5 页仅参考文献。15 个正文引用 key 与 15 个实际 bibitem 一致，无未定义引用、Overfull box、过大 float、缺失字形或页面外文本。29 个字体条目全部嵌入，无 Type 3；无书签、表单、超链接等检查报错。上述为本地核验，不冒称投稿门户认证。本轮没有新增文献，Related Work 只据已有文献审计和最新报告澄清评价目标；没有把尚未完整获取的 An 正文描述为已经完成全面技术比较。

`final-check.json` 确认 576 条冻结原始记录、8 个预注册/校准 JSON 及 175 个受保护旧文件不变。新源码包含完整 LaTeX、四张使用中的图、原始 Fig.3、288 条 RF-0 记录、描述性分析 CSV/脚本、接口修订及测试；包内 `SHA256.json` 和 ZIP 内容逐项核对通过。它不是完整神经运行环境，不包含外部连接矩阵、许可未确认的第三方数据原表或私人 Blender 工程，也不是正式投稿补充附件。

公开生成时工件仍是 `986ff54193fee6a1b95815499a4a3477b15ea49a`，此前公开最终论文修订是 `48c16c0852bcc3f6b061ab8edc97b0f16ebc1016`。**它们均不代表本轮新候选和新 schema 防护**。正文已区分不可变的生成快照和本轮源码修订；在另行公开新固定版本之前，仍有版本链接更新这一交付事项。本轮没有用旧 commit 冒充新版本。

## 独立判断与剩余拒稿风险

新叙事比原 science candidate 更具体：同一批轨迹直接显示 100 ms 的终点差异如何改变任务判定，随后用 RF 迁移和冻结预警错误限定可推广范围。它将科学结果与证据契约连接起来，减少了工作清单感和水箱插叙。但是，这只是既有证据的更准确组织和一个描述性复算，不能据此声称创新性评分或接收概率已经提高。

1. **经验增量仍窄。** 单图、假定 RF、合成 plant，尚无连接组特异的损伤机制或理论解释。这仍是最主要的竞争力风险。
2. **反馈对比未匹配健康 reserve/动作预算。** 结果是完整系统配置的条件性差异，不能解释为 relay 的普适或损伤特异优势。
3. **时域限制实质存在。** RF-0 大部分额外接触很晚，另有接近 1 s 的 transfer 接触；1 s 内未接触不证明长期安全，也不是普适 50% 容忍阈值。
4. **RF 变化无法独立归因。** 地图、重校准及测试簇同时改变；A/B 50% 对比各只有一个非零簇。不显著不是等效，也没有证明“效应变化显著”。
5. **预警失败信息稀疏。** RF-A/B 只有 2/1 个正类簇，条件率区间不稳；所测冻结标量失效不代表神经预测普遍无效。约 66° 的 decoder RMSE 仍保留。
6. **接口验证有边界。** 选择的挑战、core schema 与日志一致性有证据支持；任意异常输入、未记录状态和真实神经执行认证没有。
7. **工件新版本尚未公开。** 本地 PDF/源码/哈希一致，但当前 schema 防护与描述性图没有新的公开固定 commit；需要后续明确的版本发布动作。

没有新增神经仿真、没有改动冻结实验、没有补造数据或检验。新稿可作为有界系统实证研究的更清楚候选版；剩余机制和外推缺口没有被文字修订消除。
