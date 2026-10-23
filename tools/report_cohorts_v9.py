"""Generate numeric core/stress research record directly from checked evidence."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();sources={}
    def read(p):
        p=ROOT/p;sources[p.relative_to(ROOT).as_posix()]=sha(p)
        return json.loads(p.read_text(encoding='utf-8'))
    core=read(Path('audit/acceptance-v9/core-v2/summary.json'))
    stress=read(Path('audit/acceptance-v9/stress-v2/summary.json'))
    diag=read(Path('audit/acceptance-v9/control-diagnostic-core-v2/diagnostic.json'))
    compare=read(Path('audit/acceptance-v9/warning-comparisons-core/comparisons.json'))
    stress_compare=read(Path('audit/acceptance-v9/warning-comparisons-stress/comparisons.json'))
    for label in ['core','stress']:
        if not read(Path(f'audit/acceptance-v9/replay-{label}/replay.json'))['passed']:raise ValueError('replay failed')
        if not read(Path(f'audit/acceptance-v9/numbers-{label}/check.json'))['passed']:raise ValueError('numbers failed')
    if not core['complete'] or not stress['complete']:raise ValueError('incomplete cohort')
    p=ROOT/'audit/acceptance-v9/core-v2/pairs.csv';sources[p.relative_to(ROOT).as_posix()]=sha(p)
    with p.open(newline='') as f:pairs=list(csv.DictReader(f))
    maximum=max(abs(float(r['stop_ratio'])-float(r['common_ratio'])) for r in pairs)
    lines=['# 已完成的 v9 主实验与角度压力测试：数值记录','',
        '本文件直接由已通过独立回放及算术检查的 JSON/CSV 生成。它不宣称后续动作消融、最终 PDF 或发布步骤已完成。',
        '主实验与压力测试使用不同种子簇，禁止合并以提高显著性。此处“成功”仅指 1000 ms 内无首次接触，不是最终逃脱。','']
    def emit(s=''):lines.append(s)
    labels={'transmission':'命令率低','stop_count_upper':'各自停止上包络（回顾性）',
        'equal_duration_upper':'400ms 活动上包络','equal_duration_two_sided':'400ms 双侧活动',
        'schedule_only':'零未来转向／执行器基线','deadline':'保持当前神经转向的候选预测'}
    def pct(v):return '未定义' if v is None else f'{100*v:.2f}%'
    for title,d,label in [('主实验',core,'core'),('角度压力测试',stress,'stress')]:
        emit(f"## {title}：{d['records']} 条记录，{d['seed_clusters']} 个独立种子簇")
        emit();emit('| 控制律 | 网络 | 方位 | 成功/n | 损失 | 收益 | 健康风险集 |')
        emit('|---|---|---:|---:|---:|---:|---:|')
        for r in d['counts']:
            emit(f"| {r['mode']} | {r['fault']} | {r['phi_deg']:+g}° | {r['success']}/{r['n']} | {r['losses']} | {r['gains']} | {r['healthy_at_risk']} |")
        emit();emit('### 配对净损失与交互（百分点）');emit()
        emit('| 估计量 | 均值 | 95% 整簇百分位区间 |');emit('|---|---:|---:|')
        for key,r in d['cluster_effects'].items():emit(f"| {key} | {100*r['estimate']:.3f} | [{100*r['low']:.3f}, {100*r['high']:.3f}] |")
        emit();emit('交互方向为 relay 净损失减 proportional 净损失；负值表示 relay 的观察损失较少。');emit()
        for fault in ['F2_25','F2_50']:emit(f"- {fault}：对称零假设 sign-flip raw p={d['interaction_raw_p'][fault]:.10g}；两剂量 Holm p={d['interaction_holm_p'][fault]:.10g}。")
        emit();emit('这是模型内的对称簇零假设敏感性分析，不是随机分配控制律的随机化检验。压力测试仅八簇，区间很宽，不是主实验的精确确认。')
        emit();emit('### 对同一组任务记录进行预警评分');emit()
        emit('| 判据 | TP | FP | TN | FN | 灵敏度 | 特异度 | FPR | FNR |')
        emit('|---|---:|---:|---:|---:|---:|---:|---:|---:|')
        for name,text in labels.items():
            r=d['warning_scores'][name]['all']
            emit('| '+text+' | '+' | '.join(str(r[k]) for k in ['tp','fp','tn','fn'])+' | '+' | '.join(pct(r[k]) for k in ['sensitivity','specificity','false_positive_rate','false_negative_rate'])+' |')
        emit();emit('各自停止判据是回顾性资源评分，使用配对健康停止计数；400ms 规则使用健康验证集分方向／控制律中位数，两者分类差异不能全部归因时长。')
        emit('所有前瞻性预警窗口均早于接触。零漏报产生的退化 bootstrap 区间不证明零风险；联合簇漏报上界也不是条件 FNR 保证。')
        emit();emit('### 活动比值与终点');emit()
        emit('| 控制律/删除 | 各自停止 | 共同停止 | 400ms | 完整1s |')
        emit('|---|---:|---:|---:|---:|')
        for key,r in d['activity_ratios'].items():emit('| '+key+' | '+' | '.join(f"{r[k]['median']:.6f}" for k in ['stop_ratio','common_ratio','early_ratio','full_ratio'])+' |')
        emit();emit('| 控制律 | 网络 | 800ms 成功 | 900ms 成功 | 1000ms 成功 |')
        emit('|---|---|---:|---:|---:|')
        for mode in ['proportional','relay']:
            for fault in ['healthy','F2_25','F2_50']:
                rr=[next(r for r in d['horizon_sensitivity'] if (r['mode'],r['fault'],r['horizon_ms'])==(mode,fault,t)) for t in [800,900,1000]]
                emit(f"| {mode} | {fault} | "+' | '.join(f"{r['success']}/{r['n']}" for r in rr)+' |')
        execution=next((ROOT/f'runs/task-v9-{("test" if label=="core" else "stress")}').glob('execution-*.json'))
        ex=read(execution.relative_to(ROOT));emit()
        emit(f"实际三进程 campaign 用时 {ex['elapsed_seconds']:.3f} s，退出码 {ex['exit_codes']}；episode wall time 中位数 {d['compute']['episode_wall_seconds_median']:.3f} s。重叠 episode 时间求和不是 CPU 秒数。")
        emit(f"原始索引：`audit/acceptance-v9/{label}-v2/raw-index.csv`；逐记录、整簇、预警与时间窗表均在同目录。")
        emit()
    emit('## 事后诊断与解释边界');emit()
    emit(f"主实验 {diag['same_predecision_trace_pairs']}/{diag['paired_law_scenarios']} 个控制律配对具有相同触发时刻与触发前轨迹。控制律共享触发规则，但后续转向不同。");emit()
    for r in diag['healthy_margins']:emit(f"- {r['mode']} 健康最小安全间距：中位数 {r['median_min_clearance_mm']:.3f} mm，范围 [{r['minimum_min_clearance_mm']:.3f}, {r['maximum_min_clearance_mm']:.3f}] mm。")
    emit('因此，健康成功数一致不等于安全裕量、执行努力或完整控制质量相同。该对比支持系统上下文依赖，不识别独立于健康裕量的纯故障耐受优势。')
    emit(f'主实验各自停止与共同停止的最大单对比值差为 {maximum:.9f}，所有组中位数均不变，旧版大幅 exposure 效应不能作为当前主发现。')
    r=compare['comparisons']['all/deadline-minus-schedule_only']['specificity'];ci=r['cluster_interval']
    emit(f"候选预测相对执行器基线的核心特异度增量为 {100*r['difference']:.3f} pp，描述性整簇区间 [{100*ci[0]:.3f}, {100*ci[1]:.3f}]。该增量分析是登记后的描述性补充，不是新确认性假设或新算法。")
    n=stress_compare['diagnostics']['all/transmission']['sensitivity_valid_resamples']
    emit(f'压力测试的 20000 个 bootstrap 重采样中，{n} 个含正类，{20000-n} 个不含正类；灵敏度区间条件于前者。只有两次失败，不能验证“完美预警”。')
    emit('旧 original/gated 六簇 25% 交互 p=.25 仍按旧协议保留，不能被新控制律结果覆盖或称为复现。')
    emit();emit('## 来源与状态');emit()
    emit('阈值、控制律、种子和矩阵在独立测试前冻结；没有看测试结果调参、替换种子或增加样本直到显著。原冻结分析器的 CSV 字段冲突仅由导出修正版改字段名，原源码与失败记录保留。')
    emit('详细偏离说明在 `paper/PROTOCOL_v9_NOTES.md`。本报告只覆盖已完成的 core/stress；动作消融和最终稿状态应查看最终交付报告。')
    text='\n'.join(lines)+'\n';a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf-8') as f:f.write(text)
    manifest=dict(report_sha256=sha(a.out),generator_sha256=sha(Path(__file__)),input_sha256=sources)
    with a.out.with_suffix('.sources.json').open('x') as f:json.dump(manifest,f,indent=2)
    print(json.dumps(dict(report=str(a.out),source_files=len(sources),bytes=a.out.stat().st_size)))


if __name__=='__main__':main()
