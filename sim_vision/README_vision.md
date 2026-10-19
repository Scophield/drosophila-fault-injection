# 视觉任务示例:移动逼近威胁的逃逸转向(全脑连接组在环)

## 模块划分

| 模块 | 文件 | 性质 |
|---|---|---|
| 2D 场景与目标脚本 | `run_closedloop.py`(几何/逼近逻辑) | 外部环境 |
| 感觉编码(looming→逐细胞率) | `encoder.py` | **假设性映射**(见下) |
| 全脑网络 | `vision_core.py`(完整 138,639 神经元 / 15,091,983 连接 Brian2 LIF,**不裁剪**) | 已验证(与论文同源) |
| 输出读出 | 8 个下行命令神经元(4 型 × 左右)+ 左右差;1,299 DN 次级读出 | 已验证 |
| 读出→转向映射 | `calibrate_readout.py` → `calib.json`(**仅用训练条件校准后冻结**) | 校准(训练/测试分离) |
| 执行器 | 2D 质点运动学(恒速前进 + 转向积分) | 外部控制器 |

分工声明:**全脑网络决定**转向意图(8 DN 左右差)与响应幅度;**外部控制器只决定**质点运动学积分与目标脚本;场景变量(目标方位)从不直接进入控制器(对照 `handrule` 模式仅供因果上界参考)。

## 已验证 vs 假设(诚实清单)

**已验证(本仓库/论文既有结果)**:全脑 LIF 网络构建、零基线、逃逸全池驱动的 94.7 Hz 读出、θ=51.4 Hz 判据、故障注入管线(F1/F2/F4/F5 语义)。

**本演示新增验证(A 阶段,待数据)**:视觉 loom 刺激下 DN 群体的方位/剂量响应可重复性、左右差符号一致性、无刺激零响应。

**显式假设(影响结论强度,如实标注)**:
1. RF 中心近似:左/右半脑细胞分别随机分配到对侧?同侧视野的方位区间(固定种子 `RF_SEED=20260201` 生成于 `rf_map.csv`);逐细胞真实感受野无公开数据。
2. 背腹梯度:LPLC2 输出增益按 soma 高度线性加权(依据 Dombrovski et al. 2025 的定性梯度),增益常数 `GRAD_GAIN=0.8` 为假设参数。
3. looming 强度包络 u(t)=clip(dα/dt/150°/s)·exp(−α/60°),为 Gabbiani 型 ψ 函数的简化;LC4/LPLC2 的动态增益未做实验标定。
4. 转向语义:左右差→转向方向的符号由训练条件校准(非文献先验);DNa02 左右对的转向功能有 Yang et al. 2024 (Cell) 依据,但其余 3 型的转向贡献未验证。
5. 逃逸行为映射:生物果蝇为跳跃起飞(GF 通路);2D 演示以质点转向近似"逃逸机动",不代表起飞行为。

## 运行命令(最小复现序列)

```bash
git clone https://github.com/philshiu/Drosophila_brain_model.git   # 上游数据(SHA256 见主 README)
ln -s <parent>/Drosophila_brain_model .
pip install -r requirements.txt
cd sim_vision
python3 run_openloop.py            # A:开环 15 条件 × 6 种子(~25 min 单核)
python3 analyze_openloop.py        # 汇总表 + 方向编码检查
python3 calibrate_readout.py       # B:训练条件校准(冻结 calib.json)
python3 run_closedloop.py --modes brain --seeds 0,1,2 --phis -60,0,30   # C:闭环冒烟
python3 run_closedloop.py --tag main --modes brain,silence,flip,handrule \
    --faults none,F2_25,F2_50,F4_1pct --seeds 0,1,2 --phis -60,-30,0,30,60   # C+D+E 全量(~1 h)
python3 make_video.py --tag main   # 视频:无故障 vs F2 vs F4 并排
```

## 阶段判据

- **A**:无刺激全网 0 尖峰;方位条件左右差符号跨种子一致;loom 速率/尺寸呈剂量趋势。
- **B**:校准仅用 φ∈{−60,−30}、v_0p5、static;`calib.json` 冻结后用于全部测试轨迹。
- **C**:闭环逃逸成功率与最小距离(真实记录,失败照实展示)。
- **D**:silence(DN 输出断开→直线逃逸)与 flip(左右反转→逃向目标)性能应显著劣于 brain;handrule 为外部规则上界参考。
- **E**:F2/F4 故障应用于全脑网络(统一刺激/时限/种子);F4 预期过活动(同时检查总尖峰;输出静默≠神经元删除)。
