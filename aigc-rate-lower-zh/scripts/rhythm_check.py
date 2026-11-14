# -*- coding: utf-8 -*-
"""看中文文本的"规整度"——商用 AIGC 检测器真正吃的东西，词表打分抓不到。

输出四项：
  1. 段长分布与变异系数（CV 越低越均匀）
  2. 句长分布与变异系数（人类常见 0.5–0.7；<0.45 偏齐）
  3. 句首二字重复度（同一起头反复出现＝模板感）
  4. 重复四字串（≥3 次，排除主题词后才是问题）

用法：
    python rhythm_check.py paper.txt
    python rhythm_check.py paper.txt --min-rep 4
"""
import argparse
import re
from collections import Counter


def load(path):
    with open(path, encoding="utf-8") as f:
        blocks = [b.strip() for b in re.split(r"\n\s*\n", f.read()) if b.strip()]
    # 去掉标题、参考文献、过短行
    paras = []
    for b in blocks:
        if len(b) < 15:
            continue
        if b.startswith(("参考文献", "[", "References")):
            continue
        paras.append(b)
    return paras


def cv(xs):
    m = sum(xs) / len(xs)
    var = sum((x - m) ** 2 for x in xs) / len(xs)
    return (var ** 0.5) / m if m else 0.0


def main(path, min_rep):
    paras = load(path)
    if not paras:
        print("没有可分析的正文段落")
        return
    plens = [len(p) for p in paras]
    sents = [s for p in paras for s in re.split(r"[。！？；]", p) if len(s) >= 4]
    slens = [len(s) for s in sents]

    print(f"段落数   {len(paras)}")
    print(f"段长     均值 {sum(plens)/len(plens):.1f} 字  CV {cv(plens):.3f}  最短 {min(plens)}  最长 {max(plens)}")
    print(f"句长     均值 {sum(slens)/len(slens):.1f} 字  CV {cv(slens):.3f}  最短 {min(slens)}  最长 {max(slens)}")
    print()

    heads = Counter(s[:2] for s in sents)
    top = heads.most_common(8)
    print("句首二字 Top8：", "  ".join(f"{k}({v})" for k, v in top))
    if top and top[0][1] >= 4:
        print(f"  ↑ 「{top[0][0]}」开了 {top[0][1]} 个句子，换掉一部分")
    print()

    four = Counter()
    for p in paras:
        for i in range(len(p) - 3):
            g = p[i:i + 4]
            if re.match(r"^[\u4e00-\u9fa5]{4}$", g):
                four[g] += 1
    rep = [(k, v) for k, v in four.most_common(60) if v >= min_rep]
    print(f"重复四字串(>={min_rep})：", "  ".join(f"{k}({v})" for k, v in rep[:14]) or "无")
    if rep:
        print("  ↑ 主题词（如学科名、理论名）可留，其余反复出现的词组是节奏指纹")
    print()
    print("段长序列：", plens)

    print()
    if cv(plens) < 0.45:
        print("提示：段长太均匀，插一个短段（20–40 字）打断一下")
    if cv(slens) < 0.45:
        print("提示：句长太齐，把某处长句改成逗号连缀，或拆出一个 6–10 字的短句")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--min-rep", type=int, default=3)
    a = ap.parse_args()
    main(a.path, a.min_rep)
