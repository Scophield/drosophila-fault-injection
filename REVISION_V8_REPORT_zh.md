# 2026-10-21 审阅意见的大修响应（assessment-v8）

审阅版本：2026-10-21；修订完成日期：2026-10-22（日本时间）。
稿件保留原题、单作者及 IEEE 五页格式。定位为故障评估选择的经验案例研究。

## 最主要的新证据

完成 Original / Pre-cue gate × Healthy / F2-25% / F2-50% 的完整交叉比较。
使用相同 seeds 12–17、相同 ±30°、冻结校准、相同输入 seed 和删除 mask。
72 条记录包含 24 条字节一致的既有健康记录与 48 条新故障记录；独立统计单位是六个 seed 簇。

| 控制律 | Healthy | 25% 删除 | 50% 删除 | 25% 配对损失 / 收益 | 50% 配对损失 / 收益 |
|---|---:|---:|---:|---:|---:|
| Original | 4/12 | 4/12 | 0/12 | 1 / 1 | 4 / 0 |
| Pre-cue gate | 6/12 | 3/12 | 0/12 | 3 / 0 | 6 / 0 |

所有成功均出现在 −30°；该交叉比较的全部 +30° 记录均碰撞。
损失定义为健康成功、故障失败；收益为健康失败、故障成功。健康成功的风险集分别为 4 和 6。
Original 在 25% 删除下的净损失为零，包含一次损失和一次收益，不能解释为没有故障影响。

交互项为 gate 的健康减故障成功率，再减去 Original 的相同差值；两个方向始终随 seed 一起重采样。

| 删除剂量 | 净损失交互（百分点） | 条件 bootstrap 95% 范围 | 非零 seed 簇 | 事后符号翻转敏感性 |
|---|---:|---:|---:|---:|
| 25% | +25.0 | 8.3–41.7 | 3/6 | p=0.25 |
| 50% | +16.7 | 0.0–33.3 | 2/6 | p=0.50 |

20,000 次条件 bootstrap 的区间与全部 46,656 种有放回簇重采样的精确枚举一致。
看到区间后增加了明确标为事后的 64 种符号翻转检查；它假设独立 seed 簇的交互零假设对称居中，
不等同于随机分配控制律的试验。25% 区间不含零，但仅三个非零簇，不作总体显著性或普遍性声明。
50% 删除时两种故障控制律都为 0/12，净损失差主要反映其健康基线差异。
健康条件下 gate 的优势不能直接称为容错改进。

## 活动与阈值

每条故障轨迹均与同一控制律、方向和 seed 的健康轨迹比较，提供 200/300/400/500 ms 与逐对共同持续时间比值。
没有补造碰撞之后的活动。48 条故障记录中发生 41 次碰撞；在四个固定窗口、c=1.5/2/3/4 的全部组合中，
活动超阈均没有标出这些碰撞。500 ms、c=1.5 时反而标出了两条最终成功的故障记录。
400 与 500 ms 的判定对应关系列在补充表 S22；全部 64 种组合保留在 thresholds.csv。

这支持“在本任务、窗口及操作性阈值下，所用活动规则不足以区分这些结果”，不支持“spike count 普遍无效”。
历史 joint rule 的 cohort 计数也独立重算：四种 c 下的额外拒绝数均为 14、2、2、0。
这些阈值没有经过硬件资源、功率或安全预算验证。

## 逐项回应

| 审阅问题 | 修订及证据位置 |
|---|---|
| 核心创新不突出 | Abstract、Introduction 明确为经验发现；区分测量选择造成的解释变化与已有的匹配、报告原则；不声称新容错算法。 |
| 健康控制律对照不能证明故障效应 | 主表 I 改为完整六条件矩阵；新增配对损失、收益、净损失交互。补充表 S17–S20 给出每个 seed 与两个方向。 |
| 历史证据强度混合 | 方法开头建立 prospective task evidence → archive reanalysis → selector diagnostics 层级；F4 首次出现即披露 manifest 和保护规则问题。 |
| 历史 dt、seed、终止及保护规则 | 现行协议与补充材料统一列出；历史时间步长继续记为未知，缺失 manifest 不用当前源码补造。 |
| F2 注入单位 | 统一为 connection-table rows；一个删除行包含它表示的全部 contacts，两个剂量的 mask 为嵌套抽样。 |
| 288 records 的独立性 | 明确为条件与控制组的混合，不是 288 个总体独立故障样本；排除分析为事后的整条件敏感性比较。 |
| 方向符号 | 方法给出 +30° 左侧、−30° 右侧和两个 readout 数值对应转向的实例；不解释为真实果蝇行为。 |
| activity threshold 的意义 | 明确为 operational criterion；新增阈值与碰撞/成功对应表、全部窗口 CSV；不建立硬件或安全阈值。 |
| 摘要措辞与方向泛化 | 额外拒绝明确相对于 transmission-only；方向结论限定为本交叉比较的 +30° episodes。 |
| 文献定位和英文 | 修正 Related Work 的残句；围绕 paired exposure、完整观察时域及神经/任务端点区分定位，不对已有工作作未经核实的缺失声明。 |
| Figure 2 配对关系 | 同一 seed、同一方向的两剂量活动比用细线相连；新增补充图 S9 对两种控制律分别展示全部配对。 |
| duration matching 与早期截断混淆 | 保留两种不同 estimand；0.382→0.729 是共同暴露纠正；840–900 ms 的六次 crossing 是已知校准场景的晚期超阈。 |
| bootstrap 计数解释 | 27 和 46,656 均为有放回重采样组合，不是新增独立实验；增加重采样次数不能增加独立信息。 |
| 结论与排版 | 结论要求声明 analysis horizon、termination reason、方向及 loss/gain；移除参考文献前强制换页，正文与参考文献共五页。 |

## 复现与核验入口

- 主稿：paper/fly_connectome_fault_assessment_v8.pdf；英文源文件保留于 paper/。
- 补充材料：paper/fly_connectome_supplement_v8.pdf，包含 22 张表与 9 幅图。
- 当前协议：paper/PROTOCOL_v8.md；复现命令：REPRODUCE.md。
- 原始完整矩阵：runs/controller-fault-v8/vision/episodes_controls/；生成源码、配置和校准 hash 随批次保存。
- 分析：audit/controller-fault-v8/cross.json、pairs.csv、thresholds.csv。
- 独立核验：audit/cross-audit-v8/audit.json、archive_thresholds.csv；包括原始二元结果、活动计数、精确 bootstrap 与事后敏感性。
- 39 项回归检查已通过。最终 PDF、源文件和全部结果的匹配核验见 audit/revision-v8-release-check/validation.json；本地 ZIP 的 manifest 绑定交付文件。

三个续跑 worker 的退出码均为零。成功续跑的 elapsed 为 1727.1 s，不包含被中断的先前 invocation。
全部 48 条新故障记录的实测 episode wall time 之和为 6162.4 s；worker 彼此重叠，这不是 CPU 时间或总 campaign elapsed。
历史原始数据和已保存 episode 未被覆盖；没有提交、推送或公开发布。

## 仍然保留的边界

本轮完成 P0 交叉实验和相关阈值展示；没有新增方向外测试、独立扩展 seed、校正 hub 重跑、硬件映射或机制分析。
仅六个 seed 簇、+30° 健康基线地板及固定的模型/任务限制外推。1 s collision-free 不等于最终逃逸。
新增直接对照改善了证据对应关系，但没有把稿件变成新的 fault-tolerant architecture 研究。
