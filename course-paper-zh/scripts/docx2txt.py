# -*- coding: utf-8 -*-
"""把 .docx 抽成纯文本（每段一行，段间空行），并给出分节字数。
不依赖 python-docx：直接解 zip 读 word/document.xml。

用法：
    python docx2txt.py paper.docx paper.txt
"""
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
PUNCT = "，。、；：“”‘’（）——？！…《》,.;:?!\"'()"


def docx_lines(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    out = []
    for p in root.iter(W + "p"):
        text = "".join(t.text or "" for t in p.iter(W + "t"))
        if text.strip():
            out.append(text.strip())
    return out


def stats(lines):
    i_ref = next((i for i, l in enumerate(lines) if l.startswith(("参考文献", "References"))), None)
    head = lines if i_ref is None else lines[:i_ref]
    refs = [] if i_ref is None else lines[i_ref + 1:]
    nopunct = lambda t: len("".join(c for c in t if c not in PUNCT))
    print("段落数        :", len(lines))
    print("全文含标点    :", sum(len(l) for l in lines))
    print("全文不含标点  :", sum(nopunct(l) for l in lines))
    if refs:
        print("参考文献区    :", sum(len(l) for l in refs))
        print("不含参考文献含标点  :", sum(len(l) for l in head))
        print("不含参考文献不含标点:", sum(nopunct(l) for l in head))


if __name__ == "__main__":
    src = sys.argv[1]
    lines = docx_lines(src)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write("\n\n".join(lines))
        print("->", sys.argv[2])
    stats(lines)
