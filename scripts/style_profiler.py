#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
style_profiler.py —— 风格特征提取与对比（把"语感"变成可测量特征）

用法:
    python3 style_profiler.py 爆款锚.md 我的章节.md [更多文件...]
    python3 style_profiler.py 我的章节.md

思路: "别扭感"的本质 = 你的文本与读者熟悉的爆款网文的统计特征不一致。
      用爆款文本当"锚"，提取同一组特征对比，偏离大的项就是返工目标。
"""
import sys, os, re

CJK = re.compile(r"[\u4e00-\u9fff]")

ADVERBS = ["缓缓", "微微", "轻轻", "淡淡", "静静", "深深", "狠狠", "紧紧", "顿时", "瞬间", "刹那", "猛地", "骤然", "倏地", "非常", "十分", "极其", "特别", "格外"]
CONNECTIVES = ["因为", "所以", "于是", "然而", "但是", "不过", "不仅", "而且", "同时", "与此同时", "毕竟", "况且", "因此", "从而"]
IDIOMS = ["洋洋洒洒"]
SPOKEN = ["啊", "吧", "呢", "嘛", "呗", "哈", "啦", "呀", "哦", "他娘的", "狗东西", "搁", "咱", "这破", "娘的"]
METAPHOR_MARKS = ["像", "如", "似", "仿佛", "宛如", "如同", "恰似", "好似", "好比", "犹如"]

def cjk(s):
    return len(CJK.findall(s))

def strip_markdown(text):
    text = re.sub(r"(?m)^#.*$", "", text)
    text = re.sub(r"（本章完）|\(本章完\)", "", text)
    return text

def strip_dialogue(text):
    text = re.sub(r'"[^"]*"', '""', text)
    text = re.sub(r'"[^"]*"', '""', text)
    return text

def dialogues(text):
    ds = re.findall(r'"([^"]*)"', text)
    ds += re.findall(r'"([^"]*)"', text)
    return ds

def profile(path):
    text = open(path, encoding="utf-8").read()
    body = strip_markdown(text)
    narr = strip_dialogue(body)
    total = cjk(body)
    f = {}
    f["字数"] = total
    # 句
    sents = [s for s in re.split(r"[。！？…\n]", narr) if s.strip()]
    lens = [len(s) for s in sents]
    f["平均句长"] = round(sum(lens) / len(lens), 1) if lens else 0
    f["碎短句%"] = round(sum(1 for l in lens if l <= 12) / len(lens) * 100) if lens else 0
    f["长句%"] = round(sum(1 for l in lens if l >= 30) / len(lens) * 100) if lens else 0
    f["超短句(≤6)%"] = round(sum(1 for l in lens if l <= 6) / len(lens) * 100) if lens else 0
    # 密度
    def d(ws, t=text):
        return round(sum(t.count(w) for w in ws) / total * 1000, 1) if total else 0
    f["副词/千字"] = d(ADVERBS)
    f["连接词/千字"] = d(CONNECTIVES)
    f["成语/千字"] = d(IDIOMS)
    f["的/千字"] = d(["的"])
    f["语气词/千字"] = d(SPOKEN)
    # 比喻
    f["比喻数"] = sum(1 for s in re.split(r"[，。！？；：…\n]", narr)
                      if any(m in s for m in METAPHOR_MARKS))
    # 对话
    dc = sum(cjk(x) for x in dialogues(text))
    f["对话占比%"] = round(dc / total * 100) if total else 0
    # 段落
    paras = [p for p in re.split(r"\n\s*\n", body) if cjk(p) > 0]
    if paras:
        f["平均段长"] = round(sum(cjk(p) for p in paras) / len(paras))
        f["一句一段%"] = round(sum(1 for p in paras if len(re.findall(r"[。！？…]", p)) == 1) / len(paras) * 100)
    else:
        f["平均段长"], f["一句一段%"] = 0, 0
    return f

def main():
    files = sys.argv[1:]
    if not files:
        print("用法: python3 style_profiler.py <锚.md> <候选.md> [更多...]")
        sys.exit(1)
    keys = ["字数", "平均句长", "碎短句%", "长句%", "超短句(≤6)%", "副词/千字",
            "连接词/千字", "成语/千字", "的/千字", "语气词/千字", "比喻数",
            "对话占比%", "平均段长", "一句一段%"]
    profs = [(f, profile(f)) for f in files]
    # 表头
    w = max(len(os.path.basename(f)) for f, _ in profs) + 2
    header = "特征".ljust(14) + "".join(os.path.basename(f).ljust(w) for f, _ in profs)
    print(header)
    print("-" * len(header))
    for k in keys:
        print(k.ljust(14) + "".join(str(p[k]).ljust(w) for _, p in profs))
    # 若给了锚+候选，给出偏离提示
    if len(profs) >= 2:
        anchor = profs[0][1]
        print("-" * len(header))
        print("候选相对锚的偏离(需人工判断方向是否合理):")
        for f, p in profs[1:]:
            print("  [%s]" % os.path.basename(f))
            for k in ["副词/千字", "连接词/千字", "成语/千字", "的/千字", "平均句长", "对话占比%", "平均段长"]:
                if isinstance(anchor[k], (int, float)) and anchor[k]:
                    ratio = p[k] / anchor[k]
                    mark = "▲偏高" if ratio > 1.25 else ("▼偏低" if ratio < 0.75 else "≈")
                    print("    %s: 锚 %.1f vs 本 %.1f  %s" % (k, anchor[k], p[k], mark))

if __name__ == "__main__":
    main()
