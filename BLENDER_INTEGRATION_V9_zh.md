# assessment-v9 Blender 稿件更新

本次将提供的 Blender 素材正式整合进主稿。当前主稿为
`paper/fly_connectome_fault_assessment_v9_blender.pdf`，对应 `paper/main.tex`、
`paper/sections/v9_*.tex` 和 `paper/figs/`。补充材料为
`paper/fly_connectome_supplement_v9_blender.pdf`。实验协议仍为
task-v9.1-causal-exact-events；本次没有运行神经仿真、拟合阈值或改变统计结果。

## 图形与排版

- 图1改为第二页顶部跨栏图：脑代表锚点与小幅果蝇外形、视觉—指令选定子图、
  合成任务/反馈/精确执行器时序。通路是主要面板，避免直接缩成单栏后线条挤成团。
- 在复制的场景中隐藏原渲染标题、文字和地板，透明背景重新渲染，合成为白底。
  保留相机视角并按全部可见几何重新取景；连接显示半径统一乘0.65。没有删除节点、
  隐藏不利边或改变节点身份/连接权重。标签以可编辑矢量文字排版。
- 图2、图3及SI的assessment定量图逐字节保留。图2浮动定义移到Methods中，
  保持第三页顶部；图3仍在第四页。压缩Introduction、证据接口和Conclusion中的
  重复文字以容纳跨栏概览，没有缩小IEEE正文字号或删除结果/局限。
- 最终主稿5页，前4页技术内容，第5页仅参考文献；约3.33MB。所有主稿页均查看。
  无未定义引用、overfull、缺失字形、未嵌入字体或Type3。
- SI仍13页，TeX内容和每一页渲染像素均与上一视觉版一致；重新编译只更新来源绑定
  与PDF元数据，不增加实验、表格或结论。

## 素材核验与解释边界

独立读表核验确认410个FlyID及模型index映射、1050个有向连接的聚合有符号权重和
contact数均匹配实际模型。314个视觉输入与v9 input-map完全相同；8个指令细胞与冻结
校准完全相同。Completeness、Connectivity和annotations的hash与v9登记一致。
生成过程中还对两个网络场景的节点/边身份hash前后逐一比较。

分组为104 LC4、210 LPLC2、88个独立relay角色、8个DN；抽取器原先挑选的90个relay
候选中有2个与端点角色重叠，所以不是额外90个独立节点。所示1050条连接含2条组内边，
不能解读为纯三层前馈网络。完整模型仍有138639个神经元、15091983行连接表。

脑位置为代表锚点而非胞体中心；曲线表示选定连接而非测得的轴突/树突路径。
通路面板采用示意布局；颜色表示分组而非活动或兴奋/抑制符号。果蝇为程序化外形示意，
与脑坐标没有标本级空间配准。主稿图注明确限定子图、布局和曲线含义。
这次改善的是模型身份与协议可读性，不增加生物学、硬件或算法创新证据。

## 改动文件与保留记录

- `paper/main.tex`：跨栏图1、明确图注；`paper/figs/task_v9_overview.pdf`：新概览。
- `paper/sections/v9_methods.tex`：图1引用、移动图2浮动定义；方法参数与方程不变。
- `paper/sections/v9_intro.tex`、`v9_artifact.tex`、`v9_discussion.tex`：压缩重复文字。
- `paper/main.pdf`及新具名主稿；`paper/supplement.pdf`及新具名SI：源码对应的新构建。
- `tools/export_blender_v9.py`：从复制的工程导出透明背景、无嵌入文字的场景。
- `tools/check_blender_v9.py`：显式路径参数、只读核验模型和登记输入。
- `tools/plot_task_v9_blender.py`：Python/matplotlib组图，PDF/SVG/600dpi PNG及hash。
- `tools/package_visual_v9.py`：允许把可编辑 `.blend` 工程打入新审阅归档。
- README、paper/README、REVIEW_MATERIALS、ARTIFACT_README、STATE与本说明更新入口。

完整基线和素材备份在 `audit/blender-integration-20261023/baseline/`、`source/`；
只包含本次相对基线的文本diff在 `incremental.patch`。原Blender目录、旧具名PDF、
旧ZIP、冻结仿真源码和历史结果均保留。没有commit、push或投稿。

## 来源、构建与复查

最终图形：`audit/blender-integration-20261023/figures-03/manifest.json`。
素材核验：`graph-audit.json`；渲染：`renders-01/render-manifest.json`；
定量图/旧资产保留：`presentation-integrity.json`。以下命令均从仓库根目录执行，
使用新的、尚不存在的输出目录，替换 `<...>` 为本机相应路径：

```text
python -X utf8 tools/run_v9.py tools/check_blender_v9.py --source audit/blender-integration-20261023/source --model ../Drosophila_brain_model --out audit/my-blender-graph.json
<blender.exe> --background --python-exit-code 1 --python tools/export_blender_v9.py -- --source audit/blender-integration-20261023/source/drosophila_studio.blend --out audit/my-blender-renders
python -X utf8 tools/run_v9.py tools/plot_task_v9_blender.py --renders audit/my-blender-renders --graph-audit audit/my-blender-graph.json --out audit/my-blender-figures
```

把新overview PDF复制到 `paper/figs/task_v9_overview.pdf` 后构建：

```text
powershell -NoProfile -File tools/build_paper.ps1 -BuildDirectory audit/my-blender-main
python -X utf8 tools/run_v9.py tools/build_supplement_v9.py --core audit/acceptance-v9/core-v2 --stress audit/acceptance-v9/stress-v2 --causal audit/acceptance-v9/causal --figures audit/my-blender-figures --out audit/my-blender-si
python -X utf8 tools/run_v9.py tools/qa_pdf.py --pdf paper/main.pdf --out audit/my-blender-qa --submission
python -X utf8 tools/run_v9.py tools/check_tests_v9.py --out audit/my-blender-tests
```

图形运行时为提供的Blender 5.4.0 Alpha（954765769893）与现有Python/matplotlib；
此Alpha版本是实际使用环境，不宣称稳定版或跨平台逐位一致。64-sample Cycles渲染、
相机、分辨率、实际设备、wall time与输出hash均记录；3场景GPU渲染合计约195秒。
主稿构建仍用pdflatex/BibTeX/pdflatex/pdflatex及IEEEtran，无新增依赖安装。
只重组图和编译可使用归档内的选定数据与渲染，无需整脑矩阵；独立核验/重新抽取
仍需未打包的外部模型表和已有annotations。原抽取器保留为历史源，不应在复制目录
直接执行其原目录假设；新核验器使用明确的 `--model`、`--annotations` 参数。

最终构建/QA：`main-build-04/`、`main-qa-04/`、`supplement-build-01/`、
`supplement-qa-01/`；轻量测试 `tests-final/check.json`；完整验证
`final-validation/validation.json`。新归档 `releases/assessment-v9-blender-review.zip`
与其manifest/receipt绑定当前PDF及全部科学来源，另有 `artifact-byte-check.json`
逐成员独立检查。中间6页构建保留为过程记录，不是最终投稿版。

科学风险保持原状态：单模型/单假设感受野映射、健康安全余量和努力未匹配、少量失败簇、
预警较多误报、没有硬件映射，以及部分历史hub清单/时序元数据缺失仍未解决。
详见原研究报告和最终模拟审稿；本次图形更新不能据此宣称接收竞争力或科学问题已全部解决。
