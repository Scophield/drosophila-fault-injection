> Historical repair checkpoint. Current status: [REVISION_REPORT.md](REVISION_REPORT.md).
> Current protocol: [paper/PROTOCOL_v2.md](paper/PROTOCOL_v2.md).

# 论文与复现一致性修订记录（2026-10-21）

仓库：`D:/autoresearch_labtorary/drosophila-fault-injection`。分支仍为 `submission`，
基准提交仍为 `051dcb6a3123841041a34d3b43395e2841975879`。开始时工作区干净，
未找到适用的 AGENTS.md。没有 reset、删除历史结果、commit、push 或投稿。
所有科学数值来自归档记录重分析或获授权的输入表节点核验；没有运行 Brian2 仿真。

## 一、已复算确认

### 数学与统计

| 删除比例 f | 存活比例 p=1−f | 输出保留率 R | R/p |
|---:|---:|---:|---:|
| 0.05 | 0.95 | 0.97029703 | 1.02136529 |
| 0.10 | 0.90 | 0.98349835 | 1.09277594 |
| 0.25 | 0.75 | 0.89218922 | 1.18958563 |
| 0.50 | 0.50 | 0.76457646 | 1.52915292 |

已删除 3.6/19 倍与相反趋势，移除普适幂律/drive-invariant 解释。
正文将 compressive recruitment 限定为候选机制，保留工作点和饱和效应解释。
单独驱动扫描的 F2_50 在 75 Hz 下只有 10/12 通过 51.4 Hz 阈值。

开环 healthy：rate 中位数 94.6875 Hz，spikes 中位数 39,694。
`INHrand_mass` trial **3、9（零基编号）**分别为 327,246、271,058 spikes，
即 8.24421×、6.82872× healthy；两次均超限，10/12 未超限。
中位数 50,323 / 39,694 = 1.26777× 不能描述尾部安全性。
288 条同一批记录的 transmission-only 重评分为 276/288，联合包络 262/288；
14 条差额恰为 HUB_inh 的 12 条加 INHrand_mass 的 2 条。
这不是实际运行 SpikeFI/SpikingJET 的 benchmark。

HUB_inh spikes **中位数 847,476.5、均值 847,857**；正文采用中位数 847.5k。
Full F4 的中位活动比应为 49,272.5 / 39,694 = 1.2413×，按 1.24× 表示。
未复核来源的 Mann–Whitney p 值已从正文移除，没有用新 p 值替换。
误差线明确是 trial 10th–90th percentiles；95% CI 是 trial-record median 的
20,000 次 bootstrap percentile interval（NumPy seed 0），两者不混用。

### 闭环逐 episode 配对

以相同方位、相同 seed 的 healthy 为分母，单独评分 total spikes；escape 是另一终点。

| 归档条件 | escape | burst | 配对活动 >2× | 配对活动比中位数 |
|---|---:|---:|---:|---:|
| Full F4，v4 | 12/12 | 12/12 | 6/12 | 1.702886× |
| F2_25，v4 | 10/12 | 10/12 | 0/12 | 0.886066× |
| F2_50，v4 | 0/12 | 0/12 | 0/12 | 0.381701× |
| HUB_inh，v4c | 6/12 | 12/12 | 12/12 | 71.693071× |

F4 负方位六次为 2.06–2.32×，正方位六次为 1.28–1.35×。
不能用汇总 1.7× 代替逐 episode 包络判断。
HUB_inh 的 ratio of paired medians 为 76.715×，不同于 median of paired ratios 的
71.693×；正文明确采用后一指标。匹配的 12 条 healthy 最终绝对 heading 中位数为
100°，HUB_inh 为 63.996°。旧稿 97°混用了不同聚合组。
24/24 非正前 healthy、0/3 正前、三个因果对照各 0/12 和 handrule 12/12 均保留并复核。

机器可读证据：`audit/verified-analysis/`。其中 manifest 保存所有原始输入 SHA256、
审查基准提交、分析脚本 SHA256、Python/NumPy 版本与 bootstrap 参数。

### 实际输入与 hub 集合

按用户追加授权，仅获取并读取外部输入，没有运行模型。
上游稀疏 checkout：`../Drosophila_brain_model`，提交
`91bdd1e7dcf193f3e7ca5a8933497fcef63b7960`，不是完整实验环境。
Connectivity 为 100,804,642 bytes，SHA256 与 REPRODUCE 原记录一致。
Completeness 的 Git blob SHA256 也一致；Windows 工作区 CSV 的 CRLF 导致不同文件 hash，
逐字节规范化换行后完全相同。没有修改科学数据值。

| 比例 | 旧 index 排除：抑制/兴奋，损伤边数 | 旧映射排除：抑制/兴奋，损伤边数 | 新确定性选择：抑制/兴奋，损伤边数 |
|---|---|---|---|
| 1% | 765/621，1,365,747 | 767/619，1,366,282 | 766/620，1,365,472 |
| 2% | 1489/1284，1,996,549 | 1491/1282，1,996,705 | 1491/1282，1,996,705 |
| 5% | 3727/3205，3,378,240 | 3727/3205，3,377,965 | 3727/3205，3,377,839 |

旧 index 集合在 1% 时误含三个 protected command neurons：

- `720575940604954289`（DNp04）
- `720575940625878160`（DNb01）
- `720575940629757036`（DNp04）

2%/5% 旧 index 集合各误含四个 protected 细胞。
与新集合相比，旧 index 在三档分别替换 3/4/4 个节点；旧 mapped 在三档分别替换
1/0/1 个节点。后者是边界并列处理变化，不能全归因于 index/FlyID bug。
旧两种重建准确复现了 real/ER 的三档旧损伤边数，形成直接一致性证据；
但归档没有实际选中清单，因此这是从已知代码/输入重建，并非恢复了历史运行 manifest。
任意异构图不要求损伤相同；本例 target-only permutation 在同源行表与同一集合下
不应改变出边数。

新 1% inhibitory hub 的 contacts 为 4,732,878，期望 contact-mass 对照需要 8,895 个
随机抑制细胞，不能继续把旧 8,889-cell 活动结果当作新定义的结果。

`audit/verified-hubs/` 保存每档旧/新完整 FlyID 清单、符号组成、contacts、edges、
protected overlap、集合差异以及清单 hash；新 inhibitory/excitatory 子清单单独保存。
清单 hash 使用数值升序 FlyID、十进制 ASCII、每项末尾换行。
新完整 hub SHA256：

```text
1%  0d945e97ae80237c5dbbd583d0ccfd0cd448659302a3b51889c2de11586cd03d
2%  ebb9f111b7712e69e10f21c57aff83f2d77c3b6361f8278918d9709c80e68698
5%  fe7f018e846dbabd4ea1d1133bd11a6d4bcb232d1d2d0138cec26a19da4cb4df
```

## 二、已修代码但待重跑

`sim/hub_selection.py` 统一整数 contact 排序、FlyID 排除与按 FlyID 的确定性 tie break。
main real/null、lean controls、F4 recheck 和 closed loop 均调用它。
每次新运行保存实际集合/hash、fault seed、代码/输入/包版本；恢复运行校验 manifest，
禁止把不同配置/代码的结果混入同一目录。FLY_RUN_DIR 必须显式指定，归档目录禁止写入。
F4 recheck 有独立 healthy、独立输出目录，不再隐式替换 main F4 或跳过 main 已有 trial。

受影响归档范围：

| 范围 | 状态与处理 |
|---|---|
| real / real_fix 的三档 F4 | 损伤规模与旧 index 逻辑匹配；新集合均变化，需要重跑 |
| er / real_legacy 的 F4 | 与旧 mapped 逻辑匹配；1%/5% tie 边界变化。2% 重建集合未变，但没有历史节点 manifest |
| F4_1pct_d75/d150/d300 | 新保护与排序改变集合，需重跑；healthy/F2 的原记录没有因此被篡改 |
| HUB_inh / HUB_exc | 1% 组成变化，需重跑，不能把 765-cell 归档标成新 766-cell 结果 |
| EIm_1pct / EIm_2pct | 匹配的 E/I 数量变化，需重跑 |
| INHrand_cells / INHrand_mass | 目标数量由 765/8889 变为 766/8895，需重跑 |
| closed-loop F4 / HUB_* | 旧 mapped 的 1% 边界变化，需重跑；旧 12/12 或 6/12 仅为归档观察 |
| pathway_mass.json | 修复 CSR 合并重复 null pair 之前抽样原始连接行；尚未重新计算 |
| visual open-loop 的 fresh records | 显式播种并修复 endpoint-inclusive 多跑一帧（600→620 ms）；未运行新轨迹，不能宣称逐位重放 |

`real` 与 `real_fix` 的 F4 trial records 含 `engine: vision_core N_CHUNKS=8`；
`real_legacy` 和 ER 不含此字段。实际损伤集合也不同，不能将 ~100k→~49k 的活动变化
全部归因于 chunking/backend。需要在相同节点集合与受控随机流下做 backend 对照。

## 三、因输入或资源缺失无法验证

- 外部连接组文件现已获取，但历史实际选中清单、完整运行环境锁与生成日志没有随归档保存。
  节点重建支持定位问题，不能证明历史仿真实际用了完全相同的集合。
- 用户仅授权模型输入核验，未授权整脑重跑。新 hub/control 的活动、escape、包络与 CIs
  未测量；没有生成任何假称新仿真的结果。
- `calibrate_readout.py` 的从头拟合依赖先前控制器产生的训练轨迹；原拟合时间顺序和
  bootstrap calibration 未完整说明。REPRODUCE 将 frozen calib 作为显式输入，未宣称
  独立重建校准已完成。
- 原始 simulator pins 未整套安装/执行；补出 upstream model.py 对 joblib 的依赖，但
  历史 joblib 版本未知。当前审查用 Python 3.12 与独立分析工具目录，不能等同于
  原 CPython 3.11 仿真环境。未安装 Brian2、未测 Cython/编译器仿真路径。
- 旧 visual open-loop 记录缺少实际 duration。旧生成器名义 600 ms、含终点循环实际
  620 ms；分析器现在要求显式 legacy duration 假设，不能无依据选一个来改论文。
  此问题不涉及主 150 Hz sweep 或已有闭环逐 episode 评分。
- 既有 pathway 图沿用归档数据并明确标注；修正后的大矩阵路径分析未执行。图 1 保留
  原归档素材，未声称整套历史制图流程已重建。

## 四、修改文件及目的

| 文件 | 修改 |
|---|---|
| paper/main.tex | 摘要收缩机制与 hub 结论，明确归档/待重跑 |
| paper/sections/intro.tex | 去掉驱动不变贡献，限定机制与 hub 解释 |
| paper/sections/methods.tex | 阈值适用范围、bootstrap 单位/次数/seed |
| paper/sections/results.tex | 三处硬错误、median/mean、contact mass、protocol 比较、逐 episode 评分、图注 |
| paper/sections/principles.tex | 修正 2/12、三档扫描局限、真实节点核验、待重跑；移除 page enlargement |
| paper/figs/fig3_curves.pdf, fig4_topology.pdf, fig5_demo.pdf | 从归档重绘，补 dispersion/individual trials 与 TrueType |
| paper/main.pdf | 从当前源码独立编译 |
| README.md, REPRODUCE.md, paper/README.md | 当前结果、输入路径、CLI、执行顺序、隔离输出、完整闭环命令、资源与校准边界 |
| REPORT_zh.md, paper/REPORT_zh.md, sim_vision/README_vision.md | 保留历史正文，加明显的非当前规范提示 |
| sim/hub_selection.py | 共同节点选择与实际清单/hash |
| sim/project_paths.py, sim/run_provenance.py | sibling/环境变量路径、输出保护与版本/输入/seed provenance |
| sim/engine.py, sim_vision/vision_core.py, sim_vision/encoder.py | 使用共同路径解析 |
| sim/sweep.py, sim_vision/controls_openloop.py | 共同 hub、manifest、seed、新输出/恢复规则 |
| sim_vision/f4_recheck.py | 独立输出与 healthy，不覆盖 sweep |
| sim_vision/inhib_controls.py | 独立输出，实际随机清单/hash 与 contact mass 参数 |
| sim_vision/run_closedloop.py | 共同 hub、frozen calibration 参数、独立 batch 与禁止覆盖 episode |
| sim_vision/run_openloop.py | 共同路径，显式 seed、真实 frame 数与 duration/readout metadata |
| sim/pathway_analysis.py | 共同路径、新输出、在 CSR 合并前抽样 |
| sim/analyze.py | 明确输入/派生数据/输出，生成 strict JSON，显示 trial 尾部与 percentiles |
| sim_vision/fig_demo.py | fonttype=42、明确输入输出、缺 panel 报错 |
| sim_vision/score_protocols.py | 可复用重评分、逐 trial 失败原因、源 hash、不覆盖历史评分 |
| sim_vision/analyze_controls.py | 修正 reference 路径，独立输出 |
| sim_vision/analyze_closedloop.py | 从唯一 episode 汇总，防重复，正前与四方位分开 |
| sim_vision/analyze_openloop.py | 明确输入输出；command rate 统一为 8-cell mean，不混成 summed rate |
| sim/inspect_data.py, find_escape_types.py, fig_pathway.py, fig_neuron.py, timing_test.py | 共同输入路径；相关制图新增独立输出参数 |
| requirements.txt | 补 joblib import 依赖并注明历史版本未知 |
| tools/audit_archive.py, audit_hubs.py, check_reproduction.py | 原始记录重分析、节点输入核验、无 simulator import 的 CLI/input preflight |
| tools/build_paper.ps1, qa_pdf.py | 新目录构建、引用检查、逐页渲染、字体与文字边界 QA |
| tests/test_review.py | 13 项轻量回归测试 |
| audit/ | 所有派生统计、源 hash、实际清单、构建日志和 QA；不是新仿真记录 |

完整路径清单另见 `audit/modified-files.json`。原始 `sim/results/` 与
`sim_vision/results_vision/` 没有修改；检查结果记录在最终 validation manifest 中。

## 五、执行验证与 PDF

已执行的主要命令（仓库根目录）：

```text
python -m unittest discover -s tests -v
python tools/audit_archive.py --out audit/verified-analysis
python sim_vision/score_protocols.py --out audit/verified-protocol.json
python tools/audit_hubs.py --out audit/verified-hubs
python tools/check_reproduction.py --require-model
python sim_vision/analyze_controls.py --out audit/verified-control-bootstrap
python sim/analyze.py --derived audit/verified-analysis --out audit/publication-figures
python sim_vision/fig_demo.py --tag v4 --out audit/publication-demo
powershell -File tools/build_paper.ps1 -BuildDirectory <repo>/audit/build-delivery
python tools/qa_pdf.py --pdf paper/main.pdf --out audit/pdf-delivery
```

构建脚本使用 pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX，禁用自动宏包安装。
本机 MiKTeX 已有所需宏包，latexmk 的 Perl runtime 未确认，故采用显式四步构建。
审查用 NumPy/bootstrap 与绘图/输入核验环境版本分别写入对应 manifest；完整实验环境未安装。

会议规范来源：[ISCAS 2027 Author Information](https://epapers2.org/iscas2027/ESR/authorinfo1.php)，
于 2026-10-21 核查：4 页技术内容加可选仅参考文献的第 5 页，全部字体嵌入，避免 Type 3，
PDF 不超过 5 MB。最终页数、字体、引用、裁切与版面检查见 `audit/pdf-delivery/qa.json`、
逐页 PNG 与 `audit/build-delivery/main.log`。保留 git diff，不自动提交；会议系统/PDF eXpress
的最终验证不属于本次本地编译检查。

最终验证：13 项测试通过；PDF 5 页，24 个嵌入字体，0 Type 3，0 未嵌入字体，0 未定义引用/溢出。全部 182 个审查原始来源 hash 保持不变。构建和派生文件 hash 见 audit/validation-final.json。
