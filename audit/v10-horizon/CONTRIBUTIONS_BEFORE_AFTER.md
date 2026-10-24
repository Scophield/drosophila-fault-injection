# Contribution 修改前后

对照对象为 SHA256 `536ede47297f2c56…` 的 science-candidate；本轮没有覆盖它。

## 修改前（原文）

> We quantify paired task loss under two frozen feedback laws and separately recalibrated, same-prior receptive-field (RF) realizations. We contribute an evidence interface that checks campaign invariants and delegates native input/plant semantics to independent replay, with tested reuse on a delayed tank. We also evaluate frozen neural warnings against later collision, retaining misses, false alarms and uncertain transfer. Together, these contributions connect conditional task outcomes to testable pairing, timing and exposure assumptions.

## 修改后（原文）

> We contribute three concrete findings and capabilities: (i) a paired first-contact characterization in which RF-0 proportional 50\%-deletion losses rise from 2/48 to 11/48 between 900 and 1000\,ms, with no relay contacts, alongside smaller uncertain contrasts in separately recalibrated RF cohorts; (ii) a frozen-prefix evaluation exposing 11/13 missed RF-0 contacts and cross-configuration false alarms, limiting substitution of the tested scalar warnings for task outcomes; and (iii) executable pairing, timing and exposure checks with native replay, tested error cases and limited cross-plant reuse. These quantify a mismatch between healthy success, deletion-task preservation and frozen warnings, without identifying a damage-specific protection mechanism.

## 变化及其科学意义

| 原表述的重点 | 新表述提供的可核查知识 | 保留的边界 |
|---|---|---|
| 量化两种反馈律和 RF 的配对任务损失 | RF-0 同一批 50% 删除轨迹中，P 的接触数由 900 ms 的 2/48 增至 1 s 的 11/48；R 均为 0/48；新 RF 的对比更小且不确定 | 24 个 seed 簇；重复判定不增加样本；没有新的时域假设检验或 RF 因果识别 |
| 评估冻结神经预警 | RF-0 命令率判据漏报 11/13 次后续接触，且跨配置存在误报 | 只评价实际冻结的标量判据；不是所有神经预测器的不可行性结论 |
| 提供证据接口和水箱适配 | 可执行配对、时序、暴露检查和独立重放，以及有界的跨 plant 复用 | 14 类是选定挑战；不能认证神经执行；本轮类型防护不是一般性检错覆盖率 |

新增时域图使“任务保留取决于声明的观察终点”成为同一批记录可直接核验的事实。
健康净空差异和晚期接触被共同讨论为解释因素，但没有把它们写成已分离验证的机制。
该修订增加问题的具体性与证据连接；它没有产生新的机制发现、独立实验或理论创新。
