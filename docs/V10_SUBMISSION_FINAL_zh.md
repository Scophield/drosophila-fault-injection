# 最后一轮有限投稿修订

基线为公开固定提交 `126e265ef1a0bb49d2a3103ff47b0c9077acdcc0`，不是旧 main。
已完整阅读所提供的 2026-10-25 审稿报告。本轮仅处理三项要求和两个获准小修，未重构论文。

| 项目 | 实际改动 | 核验与边界 |
|---|---|---|
| 工程贡献 | Introduction 用“声明时序与实际执行的区分”解释用途；Contract 以真实时序案例替代类型修补史 | 复查 72 条历史记录：17 个 260 ms 延迟、4 个已完成 440 ms burst、6 个错误终点标记；实际涉及 17 条不同记录，类别重叠，不相加、不与当前科学样本混用 |
| 审计价值 | 明确要求 onset=trigger+250 ms、duration=450 ms、终点 active 标记符合区间 | 忽略错误会错报快运动时长或终点执行状态；没有计算它们造成多少碰撞变化，也不声称其他工具无法发现 |
| 三图时域计数 | 只扩展 Fig.3(d) 原计数区，保持原 a–c 和 RF-0 曲线及尺寸 | 同批轨迹描述性重评分，无新样本、CI、p 值或确认性检验；RF-0 注册已列重复终点 |
| 工件引用 | 正文分别引用生成快照 986ff54 和 horizon/schema 修订 126e265 | 两条固定公开 URL 分工明确；最终本轮稿件由其新 enclosing commit 标识，不回填生成元数据 |
| RF 预警阈值 | Methods 明确每张 RF 独立用健康验证校准后冻结 | 原 command cutoffs 为 RF-0/A/B 的 5.8333/6.0625/5.6458 Hz；冻结 JSON 未改 |
| Fig.2 图例 | 左图 Healthy / 50% deletion；右图 Applied / Requested | 仅图例；曲线和挑战条形图像素一致，150 ms 标记不变 |

50% 删除的成功数（每格顺序 P、R）：

| RF | 900 ms | 1000 ms |
|---|---|---|
| RF-0 | 46/48、48/48 | 37/48、48/48 |
| RF-A | 23/24、23/24 | 22/24、23/24 |
| RF-B | 24/24、24/24 | 23/24、24/24 |

独立单位仍为 24/12/12 个 seed 簇，方位、控制律和重复终点不是独立重复。
健康净空差异、RF 重校准与不同队列、稀疏失败、非等效和非 RF 因果解释均保留。
原摘要、标题、结论主张和实验统计未改；没有把预警失效推广到所有神经预测器。
接口实现未改，原 20 项回归和 synthetic logger 盲点保留；本轮验证关注实际数据和绘图输出。

编译与检查：

```text
powershell -File tools/build_v10.ps1 -SourceFile main_v10_horizon.tex -BuildDirectory output/submission-polish/build-02
python tools/plot_horizon_v10.py --out output/submission-polish/horizon-01
python tools/plot_v10f.py --out output/submission-polish/reuse-01 --reuse-only
python tools/qa_pdf.py --pdf output/submission-polish/build-02/main.pdf --out audit/v10-submission-polish/pdf-qa-02 --submission
python tools/render_v10.py --pdf output/submission-polish/build-02/main.pdf --out audit/v10-submission-polish/native-qa-02 --main
```

使用本机已存在的 Python/LaTeX 及依赖，无安装、无新神经仿真。历史记录复查在保留其原始记录的研究目录中只读执行，与既有公开审计的 72 个来源哈希逐项一致。公开派生审计保留来源哈希；未把 V8 当作 V9/V10 重新评分。

最终检查：5 页 Letter，技术内容止于第 4 页，第 5 页仅 16 条参考文献；29 个字体条目全部嵌入，无 Type3、未定义引用、Overfull box、过大 float、缺字或页面外文本。
全部五页均渲染并视觉查看，契约段完整结束于第 3 页。字号、页边距和四图尺寸没有缩减；Fig.1/4 原 PDF、Fig.3(a–c)、RF-0 接触曲线及全部 Blender 资产均保持原样。576 条原记录、预注册、校准、原统计及生成快照均通过原哈希核验。

本轮没有执行报告中超出三项限定的新增实验、预警模型、动作/裕量匹配、网络对照或大规模方法扩写，也不宣称已解决全部审稿建议。竞争力风险仍是有界系统案例的增量较窄、健康 reserve 未匹配、RF/拟合/队列无法独立归因及失败支持稀少；文字与可核验入口改进不能消除这些科学缺口。

最终 PDF SHA256：`94cf80f8a27a230e0f6e1077337bee54b5c10429b049022d442130da528bbb1f`。
