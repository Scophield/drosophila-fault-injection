# Blender 果蝇示例工程

本目录由本地果蝇研究项目生成，独立保存，不修改论文、仿真或原始数据。

## 打开和查看

- 双击 `打开果蝇工程.cmd` 打开可编辑的 `drosophila_studio.blend`。
- Blender 窗口顶部的 Scene 下拉菜单可切换三个场景：
  - `01_Fruit_fly`：程序化果蝇外形，含复眼、触角、六足、一对翅和翅脉。
  - `02_Connectome_anchors`：本地神经元注释坐标及选取的连接通路。
  - `03_Visual_command_pathway`：同一真实通路的示意布局，更容易辨认输入和输出。
- 鼠标中键拖动旋转视角，滚轮缩放；小键盘 0 返回相机。
- F12 渲染当前场景。图片分别为 `fruit_fly.png`、`connectome.png`、`visual_pathway.png`。
- 选取的神经元和连接保留为可编辑对象；对象自定义属性保存对应 FlyWire ID、模型索引和连接权重。
- 工作区根目录的 `启动Blender.cmd` 可直接启动 Blender。

## 数据和图像含义

使用现有的：

- `../Drosophila_brain_model/Completeness_783.csv`
- `../Drosophila_brain_model/Connectivity_783.parquet`
- `../drosophila-fault-injection/sim/data/annotations.tsv`

本地模型共 138,639 个神经元、15,091,983 条连接表记录，原始 Connectivity 字段总和为 54,492,922。
坐标图展示 8,500 个背景神经元的可复现随机样本，以及完整显示的选定通路节点。

通路输入为 104 个 LC4 和 210 个 LPLC2，输出为 DNp01、DNa02、DNp04、DNb01 各左右两个。
按原项目相同的绝对模型权重规则，从 849 个两跳中继候选中选取前 90 个。
其中 2 个同时属于输入或输出端点，因此去重后共 410 个节点，其中独立中继角色为 88 个。
在这些节点的 8,327 个候选通路连接对中，保留每个端点最强关联边，再按绝对模型权重补足到 1,050 条。
这是一部分选定通路，不是全部脑网络的连接图。未引入新的神经仿真或研究结论。

`02_Connectome_anchors` 中球心来自 `pos_x/y/z`，是神经元代表锚点，并非胞体中心。
采用官方注释说明中的 4 × 4 × 40 nm 体素尺寸，再进行统一缩放和刚性坐标轴重排。
`03_Visual_command_pathway` 中的位置是人为布局；连接、ID 和权重仍然来自原始文件。
线条连接的是代表点，弯曲路径不表示实测轴突或树突。线宽表示绝对模型权重；颜色表示节点分组，不表示活动或兴奋/抑制符号。
果蝇外形是示意建模，不是样本扫描，也没有将此个体的外形与该脑数据作解剖配准。

详细采样规则、数量、源文件 SHA-256 和坐标变换见 `data_manifest.json`。
显示的全部神经元和边分别列于 `displayed_neurons.csv` 和 `displayed_edges.csv`。

## 重新生成

`extract_local_connectome.py` 使用本机已有的 CPython 3.12 与项目内 `tmp/v9-deps`。
`build_blender.py` 使用 Blender 自带 Python，无须安装 Blender 插件或额外 Python 包。
在本目录执行：

```powershell
& '..\tools\blender-5.4.0-alpha+main.954765769893-windows.amd64-release\blender.exe' --background --factory-startup --python-exit-code 1 --python '.\build_blender.py' -- --quality final
```

快速预览将 `final` 换成 `preview`。重新生成会覆盖本目录的生成工程和图片，编辑后的工程请先另存。

## Blender 安装

使用用户已下载的 Blender 5.4.0 Alpha（2026-10-22，954765769893）ZIP 便携版，
程序存放于工作区 `tools/blender-5.4.0-alpha+main.954765769893-windows.amd64-release/`。
Windows 已验证 `blender.exe` 的 Blender Foundation 数字签名，且 `--version` 已成功运行。
这是 Alpha 开发版本；本工程保留了完整生成脚本，便于后续在其他版本中调整和重建。

## 数据来源说明

- 原始计算模型：[philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model)，MIT License，Philip Shiu 和 Nico Spiller。
- [FlyWire 官方注释与坐标字段说明](https://github.com/flyconnectome/flywire_annotations/blob/main/supplemental_files/README.md)。本地注释文件以记录的 SHA-256 为准，不声称与在线最新版相同。
- 图中没有使用第三方外形网格或 AI 生成位图。
