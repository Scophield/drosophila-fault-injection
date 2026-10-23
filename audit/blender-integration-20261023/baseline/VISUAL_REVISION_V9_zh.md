# assessment-v9 图形修订

上一版为澄清协议，将主稿简化为方框流程和重复柱状图，损失了模型身份、行为直观性
和配对证据的可见性。本次恢复旧稿有用的模型/动作叙事，全部定量内容对应现有 v9
实验。没有新仿真、重选测试种子、重新校准阈值、改统计或覆盖原始数据。

## 三幅主图

1. **模型—任务图**：视觉输入、回路与8个DN读出、运动反馈；体坐标方位和实际
   距离；独立神经、执行器与任务时钟。网络/身体图标及几何是明确标注的示意，
   不冒充实测解剖图或行为轨迹。P/R 是比例/继电控制。
2. **运动—全体配对结果—效应图**：真实同种子、同方位的健康/P50/R50轨迹；
   24行×12条件的完整288条结果；登记的两剂量损失对比、95%整簇区间和Holm p。
   示例1002/-30是按登记种子顺序找到的首个P50负方位碰撞，只作描述性示例。
   路径止于首次接触，接触帧没有执行器分段事件，线性插值后校核距离为50mm。
   完整结果矩阵和“健康安全余量未匹配”限制同时可见。
3. **神经输出—任务结果图**：全部400ms命令率点与冻结阈值；五种规则的碰撞
   检出/成功任务误报及原整簇区间。点的纵向抖动只用于分开观察值，固定显示seed，
   不是实验随机性。13正例/275负例、精确几何信息与零漏报非零风险均保留。

当前主稿为 `paper/fly_connectome_fault_assessment_v9_visual.pdf`，对应
`paper/main.tex` 和 `paper/sections/v9_*.tex`；正文默认IEEE字号，前四页技术内容，
第五页仅参考文献。图2在第三页、图3在第四页。缩短了重复图注和证据接口描述，
没有删掉定量结果或科学限制。旧具名v9/v8 PDF和原v9 ZIP保持原样。

## 复现与来源

绘图器 `tools/plot_task_v9_visual.py` 输出向量PDF、可编辑SVG、600dpi PNG。
固定蓝色比例控制、青绿色继电控制、赭红色接触标记，并用线型/符号补充颜色编码。
数据、生成器和输出hash在 `audit/visual-revision-20261023/figures-02/manifest.json`。
使用的仍为 `audit/acceptance-v9/core-v2/` 及对应288条原记录。

```text
python -X utf8 tools/run_v9.py tools/plot_task_v9_visual.py --analysis audit/acceptance-v9/core-v2 --out audit/my-visual-figures
powershell -NoProfile -File tools/build_paper.ps1 -BuildDirectory audit/my-visual-main
```

在重新编译前，将新图PDF复制到 `paper/figs/`。SI构建沿用原生成器；其TeX及13页
渲染像素与之前完整审阅的v9 SI相同，没有修改表格或不利结果。独立新目录：

```text
python -X utf8 tools/run_v9.py tools/build_supplement_v9.py --core audit/acceptance-v9/core-v2 --stress audit/acceptance-v9/stress-v2 --causal audit/acceptance-v9/causal --figures audit/visual-revision-20261023/figures-02 --out audit/my-visual-si
python -X utf8 tools/run_v9.py tools/qa_pdf.py --pdf paper/main.pdf --out audit/my-visual-qa --submission
```

实际最终构建 `audit/visual-revision-20261023/main-build-03/`、
`supplement-build-01/`；最终QA `main-qa-03/`、`supplement-qa-01/`。
头两次六页中间构建保留为过程记录，不是投稿版。最终5页主稿和13页SI均字体嵌入、
无Type3、未定义引用或overfull，全部主稿页实际查看；SI逐页像素等同证据已记录。

原科学复现命令仍见 REPRODUCE.md，它记录前一版完整科学release；新增视觉流程
见本文件。新归档 `releases/assessment-v9-visual-review.zip` 将保留原始数据/分析，
叠加本次源码、图形和新验证。外部矩阵/依赖缓存仍排除。打包、重绘和本地格式检查
不代表投稿、公开发布或接收。本次没有改善先前列出的创新/泛化/硬件证据边界。
