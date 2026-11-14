# -*- coding: utf-8 -*-
"""按中文课程论文常见格式，把约定式 markdown 变成 .docx。纯标准库，无第三方依赖。

输入约定（一行一段）：
    # 题目                      -> 三号加粗居中
    ## 一、一级标题             -> 四号加粗居中
    ### （一）二级标题          -> 四号加粗居中
    其他非空行                  -> 正文，小四，首行缩进 2 字符
    > 提示文字                  -> 灰色小四，写完删掉
    <blank>                     -> 空一行
    [1] 参考文献条目            -> 小四，不缩进

用法：
    python make_docx.py paper.md paper.docx
    python make_docx.py paper.md paper.docx --line 30 --body 10.5
"""
import argparse
import re
import zipfile
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
ET.register_namespace("w", W)

SONG = "宋体"          # 中文
TNR = "Times New Roman"  # 西文
HINT_CLR = "7F7F7F"


def qn(tag):
    return "{" + W + "}" + tag


def sub(parent, tag, **attrs):
    e = ET.SubElement(parent, qn(tag))
    for k, v in attrs.items():
        e.set(qn(k), str(v))
    return e


class Builder:
    def __init__(self, line_pt=25.0, body_pt=12.0, title_pt=16.0, head_pt=14.0,
                 indent=True):
        self.line = int(round(line_pt * 20))   # 转 twips，固定行距
        self.body = int(round(body_pt * 2))    # 转半磅
        self.title = int(round(title_pt * 2))
        self.head = int(round(head_pt * 2))
        self.indent = indent

    def para(self, kind, text=""):
        p = ET.Element(qn("p"))
        pPr = sub(p, "pPr")

        # OOXML 要求 pPr 子元素按 schema 顺序：spacing -> ind -> jc
        if kind == "title":
            sub(pPr, "spacing", before=0, after=240, line=self.line, lineRule="exact")
            sub(pPr, "jc", val="center")
            size, bold, color = self.title, True, None
        elif kind in ("h1", "h2"):
            # keepNext：标题不和下文分页，避免一级/二级标题孤零零落在页脚
            sub(pPr, "keepNext")
            sub(pPr, "spacing", before=120, after=120, line=self.line, lineRule="exact")
            sub(pPr, "jc", val="center")
            size, bold, color = self.head, True, None
        elif kind == "hint":
            sub(pPr, "spacing", before=0, after=0, line=self.line, lineRule="exact")
            self._indent(pPr)
            size, bold, color = self.body, False, HINT_CLR
        elif kind == "ref":
            sub(pPr, "spacing", before=0, after=0, line=self.line, lineRule="exact")
            size, bold, color = self.body, False, None
        elif kind == "blank":
            sub(pPr, "spacing", before=0, after=0, line=self.line, lineRule="exact")
            return p
        else:
            sub(pPr, "spacing", before=0, after=0, line=self.line, lineRule="exact")
            self._indent(pPr)
            size, bold, color = self.body, False, None

        # 行内 <sup>[1]</sup> 拆成独立 run（上标），其余为正文 run
        for i, seg in enumerate(re.split(r"<sup>(.*?)</sup>", text)):
            if not seg:
                continue
            sup = (i % 2 == 1)
            r = sub(p, "r")
            rPr = sub(r, "rPr")
            rf = sub(rPr, "rFonts")
            rf.set(qn("ascii"), TNR)
            rf.set(qn("hAnsi"), TNR)
            rf.set(qn("eastAsia"), SONG)
            rf.set(qn("cs"), TNR)
            if bold:
                sub(rPr, "b")
            if color:
                sub(rPr, "color", val=color)
            # rPr 子元素须按 schema 顺序：rFonts -> b -> color -> sz -> szCs -> vertAlign
            sub(rPr, "sz", val=str(size))
            sub(rPr, "szCs", val=str(size))
            if sup:
                sub(rPr, "vertAlign", val="superscript")
            t = sub(r, "t")
            t.set(XML_SPACE, "preserve")
            t.text = seg
        return p

    def _indent(self, pPr):
        if self.indent:
            # firstLineChars=200 表示 2 字符，firstLine 是兼容用的 twips 兜底
            sub(pPr, "ind", firstLineChars=200, firstLine=480)

    def document(self, blocks):
        body = ET.Element(qn("body"))
        for kind, text in blocks:
            body.append(self.para(kind, text))
        sect = sub(body, "sectPr")
        sub(sect, "pgSz", w=11906, h=16838)          # A4
        sub(sect, "pgMar", top=1440, right=1800, bottom=1440, left=1800,
            header=851, footer=992, gutter=0)
        doc = ET.Element(qn("document"))
        doc.append(body)
        return doc


def parse(md_text):
    md_text = md_text.lstrip("\ufeff")   # 防止 BOM 吃掉第一行标题
    blocks = []
    for raw in md_text.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s == "<blank>":
            blocks.append(("blank", ""))
        elif s.startswith("### "):
            blocks.append(("h2", s[4:].strip()))
        elif s.startswith("## "):
            blocks.append(("h1", s[3:].strip()))
        elif s.startswith("# "):
            blocks.append(("title", s[2:].strip()))
        elif s.startswith("> "):
            blocks.append(("hint", s[2:].strip()))
        elif re.match(r"^\[\d+\]", s):
            blocks.append(("ref", s))
        else:
            blocks.append(("body", s))
    return blocks


CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '</Types>')

RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/>'
    '<Relationship Id="rId2" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
    'Target="word/styles.xml"/>'
    '</Relationships>')


def styles(body_pt):
    sz = int(round(body_pt * 2))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="%s"><w:docDefaults><w:rPrDefault><w:rPr>'
        '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体" w:cs="Times New Roman"/>'
        '<w:sz w:val="%d"/><w:szCs w:val="%d"/></w:rPr></w:rPrDefault>'
        '<w:pPrDefault><w:pPr><w:spacing w:before="0" w:after="0" w:line="500" w:lineRule="exact"/>'
        '</w:pPr></w:pPrDefault></w:docDefaults></w:styles>') % (W, sz, sz)


def build(src_md, dst_docx, **kw):
    with open(src_md, encoding="utf-8-sig") as f:
        blocks = parse(f.read())
    if not blocks:
        raise SystemExit("输入文件没有可用段落")
    b = Builder(**kw)
    xml = ET.tostring(b.document(blocks), encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(dst_docx, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", xml)
        z.writestr("word/styles.xml", styles(kw.get("body_pt", 12.0)))
    with zipfile.ZipFile(dst_docx) as z:
        ET.fromstring(z.read("word/document.xml"))   # 结构自检
    return len(blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--line", type=float, default=25.0, help="固定行距（磅），默认 25")
    ap.add_argument("--body", type=float, default=12.0, help="正文字号（磅），小四=12")
    ap.add_argument("--title", type=float, default=16.0, help="标题字号（磅），三号=16")
    ap.add_argument("--head", type=float, default=14.0, help="小标题字号（磅），四号=14")
    ap.add_argument("--no-indent", action="store_true", help="取消首行缩进")
    a = ap.parse_args()
    n = build(a.src, a.dst, line_pt=a.line, body_pt=a.body, title_pt=a.title,
              head_pt=a.head, indent=not a.no_indent)
    print(f"OK -> {a.dst}  paragraphs={n}")


if __name__ == "__main__":
    main()
