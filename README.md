# -ai-Low-

两个中文写作 skill，管住"课程论文"这件事的两头。

一头是老师发的**命题说明**：评分项、字数、格式、提交方式全写在里面，多数人只读题目，丢的正是那二三十分。另一头是写完之后的**那张 AIGC 检测报告**。

中间的活儿——定题、搭论证链、核材料、排版、改写——这两个 skill 包了。

纯 Python 标准库，不需要 `pip install` 任何东西。

## 里面有什么

| skill | 输入 | 输出 |
|---|---|---|
| `course-paper-zh` | 命题说明／作业要求（`.doc` `.docx` `.pdf`） | 格式完全合规的 `.docx`，外加一张逐项对照的交付清单 |
| `aigc-rate-lower-zh` | 已经写好的中文稿 | 降过 AIGC 痕迹的同一份稿 + 前后对比报告，字数与分页一并回归 |

两个可以分开用，也可以串起来：先 `course-paper-zh` 出稿，再 `aigc-rate-lower-zh` 过一遍。

## 装

拷进你的 skills 目录就行，`SKILL.md` 的 YAML frontmatter 两边通用：

```
~/.dsh/skills/          # DeepSeek Harness
~/.claude/skills/       # Claude Code
```

## 用到了别人的东西

本仓库**不含**打分器，也**没改**它——第二个 skill 的第 2 步直接调用：

- **[zkrun/academic-humanizer-zh](https://github.com/zkrun/academic-humanizer-zh)**（MIT）
  中文学术文本的 AI 痕迹打分器 `scripts/score.py`，以及 C1–C3 语义判读口径。
  规则细节见其 [`reference/rubric.md`](https://github.com/zkrun/academic-humanizer-zh/blob/main/reference/rubric.md)。

装上之后，把命令里的 `<academic-humanizer-zh>` 换成你的实际路径：

```bash
python <academic-humanizer-zh>/scripts/score.py paper.txt --json before.json
```

## 格式这件事，脚本里已经写死了

`course-paper-zh/scripts/make_docx.py` 的默认输出（中文课程论文最常见的一套口径）：

| 项 | 值 |
|---|---|
| 标题 | 宋体 三号（16pt）加粗 居中 |
| 一级／二级标题 | 宋体 四号（14pt）加粗 居中 |
| 正文 | 中文宋体 + 西文 Times New Roman，小四（12pt） |
| 行距 | 固定值 25 磅 |
| 首行缩进 | 2 字符 |
| 页面 | A4，上下 2.54 cm，左右 3.17 cm |
| 层次序号 | 一、／（一）／1.／（1）／① |

要改字号行距：`--line 30 --body 10.5`。

Word 里读回校验时，"固定值 25 磅"对应 `LineSpacingRule = 4`、`LineSpacing = 25`，脚本按这个写。标题段落自带 `keepNext`，不会孤零零掉在页脚。

## 输入约定

`make_docx.py` 吃一份约定式 markdown，一行一段：

```markdown
# 题目                      →  三号加粗居中
摘要：……
关键词：A；B；C

## 一、一级标题             →  四号加粗居中
### （一）二级标题          →  四号加粗居中
正文段落……引注写 <sup>[2]</sup> 即上标
> 灰色提示行（可删）

<blank>                     →  空一行
[1] 参考文献条目            →  小四不缩进
```

`examples/demo.md` 是一份能直接跑通的最小样例。

## 实测

同一份课程要求，换三个理论写了三版，每次都从零起稿、过一遍检测：

| 版本 | 所用理论 | 页数 | 正文（含标点） | 表层 AIGC 痕迹 |
|---|---|---|---|---|
| A | 总体国家安全观 | 4 | 2120 | 0.0% |
| B | 国防动员 | 4 | 1625 | 0.0% |
| C | 国防威慑 | 4 | 2010 | 0.0% |

用户自测（PaperYY，第一版）：查重 10.6%，AIGC 疑似率 0%。

三版观点互不重叠，是在写第一篇时就定好对照表的——同一个题目下，结论可以完全不同，只要理论换得够彻底。这事儿 skill 替不了你。

## 别指望的三件事

1. **表层分不是检测器读数。** `score.py` 是确定性词表规则（S1–S9），可复现，但和知网、维普、格子达、PaperYY 各算各的之间没有换算关系。它降了，不等于某家一定给 0；它 0% 了，也不等于真的干净。
2. **不写病句、不造错别字。** 检测器吃的是困惑度与突发性，不是语法对错。故意写错只会同时丢掉评分里的"语言流畅"。降的是**规整度**，不是**正确度**——这是底线。
3. **材料和事实要自己核。** 脚本保证格式和结构，不保证参考文献的页码是真的。凡引用必回原文，这一条 skill 帮不了你。

这是一套写作辅助工具：把"要求 → 结构 → 排版"里机械的那部分自动化掉。观点是你的，责任也是你的。

## 目录

```
course-paper-zh/
  SKILL.md
  scripts/make_docx.py       约定式 markdown → 格式合规 docx
  scripts/docx2txt.py        docx → 纯文本（含分节字数）
aigc-rate-lower-zh/
  SKILL.md
  scripts/docx2txt.py        docx → 纯文本，同上
  scripts/rhythm_check.py    句长/段长变异、句首重复、四字串重复
examples/
  demo.md                    最小可用样例
```

## License

MIT
