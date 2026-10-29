"""Build the Codex demo (all 17 page types): python build_demo.py -> demo/mmdustc-codex-demo.pptx"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from codex import tokens as T  # noqa: E402
from codex.pages import Codex  # noqa: E402

OUT = os.path.join(HERE, 'demo')
FONT = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'NotoSerifSC-VF.ttf')


def _plt():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font_manager.fontManager.addfont(FONT)
    plt.rcParams['font.family'] = 'Noto Serif SC'
    plt.rcParams['axes.edgecolor'] = '#' + T.RULE
    return plt


def _save(fig, path):
    fig.patch.set_alpha(0)
    fig.savefig(path, transparent=True)
    fig.clf()


def sample_figures(tmp):
    """Stand-in research figures in the template palette (t-SNE, attention, confusion, similarity)."""
    plt = _plt()
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list('rubric', ['#FBF8F1', '#E8C3A8', '#' + T.RUBRIC])
    rng = np.random.default_rng(11)
    out = {}

    centers = np.array([[-5.2, 3.6], [4.6, 4.4], [0.4, -0.6], [-4.4, -4.8], [5.0, -4.0]])
    fig, axes = plt.subplots(1, 2, figsize=(5.9, 3.65), dpi=300)
    for ax, spread, name in zip(axes, (2.0, 0.9), ('ProtoNet', '本文')):
        for k, cen in enumerate(centers):
            pts = cen + rng.normal(0, spread, (38, 2)) * (1.15, 0.85)
            ax.scatter(pts[:, 0], pts[:, 1], s=8, color='#' + T.SERIES[k], alpha=0.72, linewidths=0)
            ax.scatter(*cen, marker='*', s=170, color='#' + T.SERIES[k], edgecolors='#' + T.INK, linewidths=0.7,
                       zorder=5)
        ax.set_title(name, fontsize=10, color='#' + T.TEXT, pad=5)
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_xlim(-10.5, 10.5), ax.set_ylim(-9.5, 9.5)
        ax.set_facecolor('none')
    fig.tight_layout(pad=0.5, w_pad=1.4)
    out['tsne'] = os.path.join(tmp, 'tsne.png')
    _save(fig, out['tsne'])

    # attention over a synthetic textured "image"
    yy, xx = np.mgrid[0:96, 0:128] / 96.0
    base = 0.55 + 0.25 * np.sin(xx * 9) * np.cos(yy * 7) + 0.1 * rng.standard_normal((96, 128))
    att = np.exp(-((xx - 0.85) ** 2 + (yy - 0.42) ** 2) / 0.02) + 0.6 * np.exp(-((xx - 0.45) ** 2 + (yy - 0.62) ** 2)
                                                                                / 0.012)
    fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=300)
    ax.imshow(base, cmap='gray', vmin=0, vmax=1.2)
    ax.imshow(att, cmap=cmap, alpha=0.62)
    ax.set_xticks([]), ax.set_yticks([])
    fig.tight_layout(pad=0.2)
    out['attention'] = os.path.join(tmp, 'attention.png')
    _save(fig, out['attention'])

    cm = np.array([[86, 5, 3, 4, 2], [6, 81, 7, 3, 3], [2, 8, 84, 4, 2], [3, 2, 6, 85, 4], [1, 4, 3, 5, 87]])
    fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=300)
    ax.imshow(cm, cmap=cmap)
    for i in range(5):
        for j in range(5):
            ax.text(j, i, cm[i, j], ha='center', va='center', fontsize=7,
                    color='#FBF8F1' if cm[i, j] > 50 else '#' + T.TEXT)
    ax.set_xticks(range(5), ['犬', '鸟', '车', '花', '船'], fontsize=7, color='#' + T.MUTED)
    ax.set_yticks(range(5), ['犬', '鸟', '车', '花', '船'], fontsize=7, color='#' + T.MUTED)
    ax.tick_params(length=0)
    fig.tight_layout(pad=0.3)
    out['confusion'] = os.path.join(tmp, 'confusion.png')
    _save(fig, out['confusion'])

    fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=300)
    names = ['犬', '鸟', '车', '花', '船']
    vals = [0.82, 0.31, 0.22, 0.18, 0.12]
    ax.barh(names[::-1], vals[::-1], color=['#' + T.GILT_PALE] * 4 + ['#' + T.RUBRIC], height=0.55)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=7, colors='#' + T.MUTED, length=0)
    ax.set_xlim(0, 1)
    ax.set_facecolor('none')
    fig.tight_layout(pad=0.3)
    out['similarity'] = os.path.join(tmp, 'similarity.png')
    _save(fig, out['similarity'])
    plt.close('all')
    return out


REFS = [
    'O. Vinyals, C. Blundell, T. Lillicrap, K. Kavukcuoglu, D. Wierstra. Matching networks for one shot learning. '
    'NeurIPS, 2016.',
    'J. Snell, K. Swersky, R. Zemel. Prototypical networks for few-shot learning. NeurIPS, 2017.',
    'C. Finn, P. Abbeel, S. Levine. Model-agnostic meta-learning for fast adaptation of deep networks. ICML, 2017.',
    'F. Sung, Y. Yang, L. Zhang, T. Xiang, P. H. S. Torr, T. M. Hospedales. Learning to compare: Relation network '
    'for few-shot learning. CVPR, 2018.',
    'A. Radford, J. W. Kim, C. Hallacy, et al. Learning transferable visual models from natural language '
    'supervision. ICML, 2021.',
    'R. Zhang, W. Zhang, R. Fang, et al. Tip-Adapter: Training-free adaption of CLIP for few-shot classification. '
    'ECCV, 2022.',
    'A. Dosovitskiy, L. Beyer, A. Kolesnikov, et al. An image is worth 16x16 words: Transformers for image '
    'recognition at scale. ICLR, 2021.',
    'J. Devlin, M.-W. Chang, K. Lee, K. Toutanova. BERT: Pre-training of deep bidirectional transformers for '
    'language understanding. NAACL, 2019.',
]


def main():
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, '_fig')
    os.makedirs(tmp, exist_ok=True)
    fig = sample_figures(tmp)
    P1, P2, P3 = 'Part I：研究背景', 'Part II：方法', 'Part III：实验'
    cx = Codex(title='面向小样本场景的多模态认知模型', author='李毅')

    cx.cover(kicker='组会报告', title_lines=['面向小样本场景的', '多模态认知模型'],
             title_en='A Multimodal Cognitive Model for Few-Shot Scenarios',
             affiliation='中国科学技术大学', presenter='李毅', date='2026 年 10 月 28 日', advisor='张老师')

    cx.toc([dict(title='研究背景', art='magnifier', pages=(3, 7)),
            dict(title='方法', art='armillary', pages=(8, 10)),
            dict(title='实验', art='scales', pages=(11, 14)),
            dict(title='结论', art='laurel', pages=(15, 15))])

    cx.section(0, '研究背景：为什么一个样本仍然不够')

    cx.cards(P1, '小样本多模态推理面临的四个难题', [
        dict(art='hourglass', title='样本稀缺', text='每类仅 1–5 个标注样本，难以估计类内变化。'),
        dict(art='scales', title='模态鸿沟', text='视觉与语言特征分布不一致，直接比较会失真。'),
        dict(art='astrolabe', title='类别偏移', text='测试类别从未在训练中出现，必须向未知泛化。'),
        dict(art='magnifier', title='判断可信', text='模型为何如此判断，需要能追溯到具体证据。'),
    ], takeaway='四个难题指向同一个要求：表征在样本极少时仍须可对齐、可追溯。')

    cx.text_page(P1, '问题陈述：在极少样本下对齐两种模态', [
        '小样本学习要求模型只凭每类一到五个标注样本识别新类别。度量学习方法用类均值作为原型，'
        '在样本极少时，原型本身就带有很大的估计误差，类内变化几乎无从估计。',
        '与此同时，大规模视觉–语言预训练提供了丰富的语义先验：类别名称与描述在训练前就已知道，'
        '而且不随样本数量变化。问题在于，两种模态的特征分布并不一致，直接比较图像与文本会产生系统偏差。',
        '本工作的出发点是：用稳定的文本原型约束不稳定的视觉原型，让两种模态在同一空间中可比较，'
        '并让每一次判断都能追溯到具体的原型与描述。',
    ], notes=['原型误差随样本数下降，1-shot 时最大。', '文本描述来自类别名称扩写，无需额外标注。'],
        refs='[2] Snell et al., NeurIPS 2017　[5] Radford et al., ICML 2021')

    cx.timeline(P1, '小样本学习的十年：从度量到对齐', [
        dict(date='2016', title='匹配网络', text='以注意力在支持集上做加权最近邻。'),
        dict(date='2017', title='原型网络', text='用类均值作原型，按距离分类。'),
        dict(date='2017', title='MAML', text='学习便于快速微调的初始参数。'),
        dict(date='2021', title='CLIP', text='大规模图文对比学习带来零样本能力。'),
        dict(date='2026', title='本文', text='以文本原型约束视觉原型，统一两种模态。', key=True),
    ], refs='[1] Vinyals et al., NeurIPS 2016　[2] Snell et al., NeurIPS 2017　[3] Finn et al., ICML 2017　'
            '[5] Radford et al., ICML 2021')

    cx.related_work(P1, '现有方法只覆盖了问题的一部分', ['方法', '来源', '多模态', '小样本', '可解释', '无需微调'], [
        ['ProtoNet', 'NeurIPS 2017', 'no', 'yes', 'part', 'yes'],
        ['MAML', 'ICML 2017', 'no', 'yes', 'no', 'no'],
        ['CLIP', 'ICML 2021', 'yes', 'part', 'no', 'yes'],
        ['Tip-Adapter', 'ECCV 2022', 'yes', 'yes', 'no', 'yes'],
        ['本文', '—', 'yes', 'yes', 'yes', 'yes'],
    ], ours=4, note='本文是唯一同时满足四项的方法。',
        refs='[2] Snell et al., NeurIPS 2017　[3] Finn et al., ICML 2017　[5] Radford et al., ICML 2021　'
             '[6] Zhang et al., ECCV 2022')

    cx.architecture(P2, '三个模块把图像与文本映射到同一组原型',
                    ('输入', ['支持集图像', '类别描述文本', '查询图像'], 'N-way K-shot 任务'), [
                        dict(title='编码', sub='共享编码器 f(·)', chips=['视觉分支 · ViT-B/16', '文本分支 · BERT-base', '投影到 512 维']),
                        dict(title='对齐', sub='原型构建与跨模态对齐', chips=['视觉原型（每类均值）', '文本原型（类别描述）', '双向对比对齐']),
                        dict(title='推理', sub='最近原型分类', chips=['余弦相似度 ÷ 温度 τ', 'Softmax 输出类别', '返回最近原型作证据']),
                    ], bracket=(1, 2, '训练阶段联合优化：分类损失 + λ · 对齐损失'),
                    refs='[7] Dosovitskiy et al., ICLR 2021　[8] Devlin et al., NAACL 2019')

    cx.formula(P2, '以温度缩放的原型损失对齐两种模态',
               r'\mathcal{L} = -\frac{1}{|\mathcal{Q}|}\sum_{(x,y)\in\mathcal{Q}} \log '
               r'\frac{\exp\bigl(\langle f(x), \bm{c}_y\rangle/\tau\bigr)}'
               r'{\sum_{k=1}^{N}\exp\bigl(\langle f(x), \bm{c}_k\rangle/\tau\bigr)}', '1',
               [(r'\bm{c}_k', '第 k 类原型，即支持集特征的均值'), (r'f(\cdot)', '共享的视觉–语言编码器，输出已归一化'),
                (r'\langle\cdot,\cdot\rangle', '余弦相似度'), (r'\tau', '温度系数，越小分布越尖锐')],
               note='τ 取 0.1 时训练最稳定；推导与收敛性分析见附录 A。', refs='[2] Snell et al., NeurIPS 2017')

    cx.pseudocode(P2, '一个 episode 内同时更新两种原型', '算法 1　原型对齐训练', [
        (0, '输入：支持集 S，查询集 Q，温度 τ，权重 λ'),
        (0, 'for each episode do'),
        (1, 'c_k ← mean{ f(x_i) : y_i = k }  ▷ 视觉原型'),
        (1, 't_k ← g(类别描述 k)  ▷ 文本原型'),
        (1, 'L_align ← 对比损失(c_k, t_k)'),
        (1, 'for each (x, y) in Q do'),
        (2, 'p ← softmax(cos(f(x), c_k) / τ)'),
        (2, 'L_cls ← L_cls − log p_y'),
        (1, 'end for'),
        (1, 'θ ← θ − η · ∇(L_cls + λ · L_align)'),
        (0, 'end for'),
        (0, '输出：投影层参数 θ'),
    ], [('3–4', '同一批支持样本同时产生视觉原型与文本原型。'),
        ('5', '对齐损失只在原型层面计算，开销与类别数成正比。'),
        ('10', 'λ 取 0.5；主干冻结，只更新投影层。')])

    cx.figure_text(P3, '原型对齐让同类样本在特征空间中更紧凑', fig['tsne'],
                   '左为 ProtoNet，右为本文；星形为类原型，颜色表示类别。', [
                       ('类内更紧凑', '类内平均距离下降 31%，原型落在簇的中心附近。'),
                       ('类间更分离', '最近类间距离扩大 1.8 倍，混淆集中于外观相近的类别。'),
                       ('文本锚点稳定', '文本原型不随样本数变化，为视觉特征提供固定参照。'),
                   ], label='图 2', refs='[2] Snell et al., NeurIPS 2017')

    cx.compare_table(P3, '本文方法在三种设置下均取得最优', ['方法', '来源', '1-shot', '5-shot', '10-shot'],
                     [['MatchingNet', 'NeurIPS 2016', '43.6', '55.3', '61.2'],
                      ['ProtoNet', 'NeurIPS 2017', '49.4', '68.2', '74.3'],
                      ['MAML', 'ICML 2017', '48.7', '63.1', '70.9'],
                      ['RelationNet', 'CVPR 2018', '50.4', '65.3', '71.8'],
                      ['本文', '—', '56.8', '74.6', '79.1']],
                     ours=4, best={(4, 2), (4, 3), (4, 4)}, second={(3, 2), (1, 3), (1, 4)},
                     note='miniImageNet 5-way 准确率（%）；朱色为最优，下划线为次优。',
                     stats=[('+7.4', '1-shot 相对 ProtoNet'), ('+4.8', '10-shot 相对 ProtoNet')],
                     remark='样本越少，优势越明显。', muted={1},
                     refs='[1] Vinyals et al., NeurIPS 2016　[2] Snell et al., NeurIPS 2017　'
                          '[3] Finn et al., ICML 2017　[4] Sung et al., CVPR 2018')

    cx.chart_analysis(P3, '样本越少，本文方法领先越多', ['1', '2', '5', '10', '20'], [
        dict(name='本文', values=[56.8, 64.0, 74.6, 79.1, 82.0], color=T.SERIES[0], width=2.5, marker=8),
        dict(name='ProtoNet', values=[49.4, 57.1, 68.2, 74.3, 78.0], color=T.SERIES[1], hollow=True),
        dict(name='MAML', values=[48.7, 55.0, 63.1, 70.9, 74.2], color=T.SERIES[2], dash=True, hollow=True),
    ], [
        ('低样本区差距最大', '1-shot 时领先 ProtoNet 7.4 个点，20-shot 时收窄到 4.0 个点。'),
        ('更早进入平台期', '5-shot 已接近基线在 10-shot 时的水平。'),
        ('增益来自文本原型', '去掉文本原型后，1-shot 准确率回落 5.1 个点。'),
    ], x_title='每类样本数 K', y_title='准确率（%）', y_range=(40, 90, 10),
        refs='[2] Snell et al., NeurIPS 2017　[3] Finn et al., ICML 2017')

    cx.gallery(P3, '注意力集中在区分类别的局部特征上', [
        (fig['attention'], '查询图像上的原型注意力'),
        (fig['confusion'], '5-way 测试的混淆矩阵'),
        (fig['similarity'], '查询与各类文本原型的相似度'),
    ])

    cx.closing('总结', '原型对齐让小样本多模态推理更可靠', [
        ('统一表征', '视觉与语言共享原型空间，跨模态比较不再失真。'),
        ('稳健泛化', '1-shot 准确率提升 7.4 个点，对新类别同样有效。'),
        ('可以追溯', '每次判断都能对应到最近的原型与其文本描述。'),
    ], thanks='谢谢聆听', contact='李毅 · liyi@mail.ustc.edu.cn')

    cx.references(REFS)

    cx.appendix('附录', '附录 A：超参数', '温度与对齐权重的敏感性', ['τ', 'λ = 0.1', 'λ = 0.5', 'λ = 1.0'], [
        ['0.05', '54.9', '55.8', '55.1'], ['0.1', '55.6', '56.8', '56.0'], ['0.2', '55.0', '56.1', '55.4'],
        ['0.5', '53.2', '54.1', '53.7']], [
        '表中为 miniImageNet 5-way 1-shot 准确率（%），每格 600 个测试任务取平均。',
        'τ 过小时梯度集中在最近原型上，训练早期不稳定；τ 过大时分布过平，类间区分变弱。',
        'λ 在 0.3–0.7 之间结果差异小于 0.5 个点，正文统一取 0.5。',
        '所有实验固定随机种子 3407，主干冻结，只训练投影层与对齐模块。',
    ])

    path = os.path.join(OUT, 'mmdustc-codex-demo.pptx')
    cx.save(path)
    for f in fig.values():
        os.remove(f)
    os.rmdir(tmp)
    print(path)


if __name__ == '__main__':
    main()
