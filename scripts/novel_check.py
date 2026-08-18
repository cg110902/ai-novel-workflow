#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_check.py —— 配置化章节质检器（读感第一，标准动态）

设计哲学（v1.3）:
  - 脚本是"体检报告"，不是"及格线"。
  - 红线(真·必改): 正文禁用词 / 金手指硬泄露 / 解释句 / 上帝视角 / 说教句。
  - 数值项(字数/句长/段落/密度/对话占比/比喻数/视线密度/神态复用):
    默认"读感模式"只作参考区间提示(△)，不阻断交付；
    配置 strict: true 时才升级为硬门禁(✗)。
  - 最终裁决 = 读感终审(人)，不是脚本。

用法:
    python3 novel_check.py <章节.md> -c book.yaml
    python3 novel_check.py <章节.md> -c book.yaml --json out.json
"""
import sys, os, re, json, argparse

CJK = re.compile(r"[\u4e00-\u9fff]")
HAN = r"一-鿿"

GAZE_DEFAULT = ["看", "望", "盯", "瞥", "瞅", "瞧", "打量", "凝视", "扫视",
                "环顾", "目光", "眼神", "视线", "抬头", "低头", "转头", "回头",
                "四目相对", "对视"]
GESTURE_DEFAULT = ["皱眉", "点头", "摇头", "摆手", "耸肩", "叹气", "冷笑", "挑眉",
                   "眯眼", "咧嘴", "咽口水", "捏拳", "攥拳", "咬牙", "腿软", "冷汗",
                   "咽唾沫", "转身", "挥手", "跺脚", "捋须", "抿嘴", "抿唇", "翻白眼"]

# ---------------- 配置加载 ----------------
def load_config(path):
    raw = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        return json.loads(raw)
    try:
        import yaml
        return yaml.safe_load(raw)
    except ImportError:
        return _mini_yaml(raw)

def _mini_yaml(text):
    data = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if not key:
            continue
        if val.startswith("[") and val.endswith("]"):
            data[key] = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
        else:
            v = val.strip("\"'")
            try:
                v = float(v) if ("." in v) else int(v)
            except ValueError:
                pass
            data[key] = v
    return data

def cfg_get(cfg, key, default=None):
    return cfg.get(key, default)

# ---------------- 文本工具 ----------------
def load_text(path):
    return open(path, encoding="utf-8").read()

def strip_markdown(text):
    text = re.sub(r"(?m)^#.*$", "", text)
    text = re.sub(r"（本章完）|\(本章完\)", "", text)
    return text

def strip_dialogue(text):
    text = re.sub(r'"[^"]*"', '""', text)
    text = re.sub(r'"[^"]*"', '""', text)
    text = re.sub(r'【[^】]*】', '【】', text)
    return text

def dialogues(text):
    ds = re.findall(r'"([^"]*)"', text)
    ds += re.findall(r'"([^"]*)"', text)
    ds += re.findall(r'【([^】]*)】', text)
    return ds

def split_sents(text):
    return [s for s in re.split(r"[，。！？；：…\n]", text) if s.strip()]

def split_full(text):
    return [s for s in re.split(r"[。！？…\n]", text) if s.strip()]

def cjk(s):
    return len(CJK.findall(s))

def ctx(text, pos, width=14):
    return text[max(0, pos - width):pos + width].replace("\n", " ")

# ---------------- 报告器 ----------------
class R:
    def __init__(self):
        self.s1 = []; self.warn = []; self.fails = []; self.notes = []; self.ranges = []
    def add_s1(self, m): self.s1.append(m)
    def add_warn(self, m): self.warn.append(m)
    def add_fail(self, name, got, limit): self.fails.append((name, got, limit))
    def add_range(self, name, got, ref): self.ranges.append((name, got, ref))
    def add_note(self, m): self.notes.append(m)

def hit_list(text, words):
    out = []
    for w in words:
        for m in re.finditer(re.escape(w), text):
            out.append((w, m.start()))
    return out

def per1000(n, total):
    return round(n / total * 1000, 1) if total else 0.0

def strict(cfg):
    return cfg_get(cfg, "strict", False)

def gate(cfg, r, name, got, ref):
    """数值项：读感模式→参考区间(△)；strict 模式→硬门禁(✗)。"""
    if strict(cfg):
        r.add_fail(name, got, ref)
    else:
        r.add_range(name, got, ref)

# ---------------- 检查项 ----------------
def check_words(cfg, text, r):
    body = strip_markdown(text)
    n = cjk(body)
    lo, hi = cfg_get(cfg, "word_min", 0), cfg_get(cfg, "word_max", 0)
    ref = "%d~%d字" % (lo, hi)
    ok = (n >= lo and n <= hi) if (lo and hi) else True
    mark = "✓" if ok else ("✗" if strict(cfg) else "△")
    print("【0】字数口径  实际 %d 字 (参考 %s)  %s" % (n, ref, mark))
    if not ok:
        gate(cfg, r, "字数", "%d字" % n, ref)
    return n

def check_banned(cfg, text, r):
    words = cfg_get(cfg, "banned", [])
    if not words:
        return
    print("【1】正文禁用词  规则: %s (对话/系统消息豁免)  [红线]" % "、".join(words))
    body = strip_markdown(strip_dialogue(text))
    for w in cfg_get(cfg, "banned_whitelist", []):
        body = body.replace(w, "")
    hits = hit_list(body, words)
    if hits:
        for w, pos in hits:
            print("    ✗ 正文【%s】: …%s…" % (w, ctx(body, pos)))
            r.add_s1("正文禁用词【%s】: …%s…" % (w, ctx(body, pos)))
    else:
        print("    ✓ 正文纯净")

def check_thunder(cfg, text, r):
    words = cfg_get(cfg, "thunder", [])
    if not words:
        return
    print("【2】AI雷霆比喻  黑名单 %d 词" % len(words))
    hits = hit_list(text, words)
    for w, pos in hits:
        print("    ⚠ 命中【%s】: …%s…" % (w, ctx(text, pos)))
        r.add_warn("雷霆比喻【%s】: …%s…" % (w, ctx(text, pos)))
    if not hits:
        print("    ✓ 无雷霆比喻")

def check_metaphors(cfg, text, r):
    marks = ["像", "如", "似", "仿佛", "宛如", "如同", "恰似", "好似", "好比", "犹如"]
    print("【3】比喻清单 (人工逐条判断是否日常可感)")
    body = strip_markdown(strip_dialogue(text))
    for w in ["如今", "如果", "假如", "比如", "例如", "似乎", "似的", "疑似", "如同", "如是"]:
        body = body.replace(w, "  ")
    found = []
    for s in split_sents(body):
        if any(m in s for m in marks):
            found.append(s.strip())
    for s in found:
        print("    · %s" % s)
    mx = cfg_get(cfg, "metaphor_max", 5)
    mark = "✓" if len(found) <= mx else ("✗" if strict(cfg) else "△")
    print("    共 %d 条 (参考 ≤%d) %s" % (len(found), mx, mark))
    if len(found) > mx:
        gate(cfg, r, "比喻数量", "%d条" % len(found), "≤%d条" % mx)
    r.add_note("比喻 %d 条请逐条自查: 画面见过没有? 落进市井/生活经验?" % len(found))

def check_rhythm(cfg, text, r):
    print("【4】句长节奏 (完整句口径, 对话/系统消息不计入)")
    body = strip_markdown(strip_dialogue(text))
    body = body.replace(""", " ").replace(""", " ").replace("【】", " ")
    sents = [s for s in split_full(body) if s.strip()]
    lens = [len(s) for s in sents]
    if not lens:
        return
    short_n, long_n = cfg_get(cfg, "short_len", 12), cfg_get(cfg, "long_len", 30)
    avg = sum(lens) / len(lens)
    shorts = [s for s in sents if len(s) <= short_n]
    longs = [s for s in sents if len(s) >= long_n]
    ps = len(shorts) / len(lens) * 100
    pl = len(longs) / len(lens) * 100
    lo, hi = cfg_get(cfg, "short_pct_min", 15), cfg_get(cfg, "short_pct_max", 45)
    lmin = cfg_get(cfg, "long_pct_min", 5)
    print("    完整句 %d | 均长 %.1f 字 | 碎短句(≤%d) %.0f%% | 长句(≥%d) %.0f%%"
          % (len(lens), avg, short_n, ps, long_n, pl))
    if ps > hi:
        m = "✗" if strict(cfg) else "△"
        print("    %s 碎短句 %.0f%% > 参考 %d%% (像打电报)" % (m, ps, hi))
        gate(cfg, r, "碎短句占比", "%.0f%%" % ps, "≤%d%%" % hi)
    elif ps < lo:
        m = "✗" if strict(cfg) else "△"
        print("    %s 碎短句 %.0f%% < 参考 %d%% (缺爆点节奏)" % (m, ps, lo))
        gate(cfg, r, "碎短句占比", "%.0f%%" % ps, "≥%d%%" % lo)
    else:
        print("    ✓ 碎短句 %.0f%% 在区间 %d~%d%%" % (ps, lo, hi))
    if pl < lmin:
        m = "✗" if strict(cfg) else "△"
        print("    %s 长句 %.0f%% < 参考 %d%% (缺铺陈绵延感)" % (m, pl, lmin))
        gate(cfg, r, "长句占比", "%.0f%%" % pl, "≥%d%%" % lmin)
    runs, cur = [], 0
    for s in sents:
        if len(s) <= short_n:
            cur += 1
        else:
            if cur >= 4:
                runs.append(cur)
            cur = 0
    if cur >= 4:
        runs.append(cur)
    for x in runs[:3]:
        print("    ⚠ 连续 %d 个碎短句，建议插长句破节奏" % x)
        r.add_warn("连续 %d 个碎短句" % x)

def check_paragraphs(cfg, text, r):
    print("【5】段落节奏")
    body = strip_markdown(text)
    body = body.replace(""", " ").replace(""", " ").replace("【】", " ")
    paras = [p for p in re.split(r"\n\s*\n", body) if cjk(p) > 0]
    if not paras:
        print("    ⚠ 无段落")
        return
    avg = sum(cjk(p) for p in paras) / len(paras)
    one_line = sum(1 for p in paras if len(re.findall(r"[。！？…]", p)) == 1)
    p_one = one_line / len(paras) * 100
    mx = cfg_get(cfg, "para_avg_max", 45)
    mn = cfg_get(cfg, "one_line_para_min", 30)
    mark_avg = "✓" if avg <= mx else ("✗" if strict(cfg) else "△")
    mark_one = "✓" if p_one >= mn else ("✗" if strict(cfg) else "△")
    print("    段落 %d | 均长 %.1f 字 %s | 一句一段 %.0f%% %s"
          % (len(paras), avg, mark_avg, p_one, mark_one))
    if avg > mx:
        gate(cfg, r, "平均段长", "%.1f字" % avg, "≤%d字" % mx)
    if p_one < mn:
        gate(cfg, r, "一句一段%", "%.0f%%" % p_one, "≥%d%%" % mn)

def check_dialogue(cfg, text, r):
    print("【6】对话占比")
    ds = dialogues(text)
    total = cjk(strip_markdown(text))
    if not total:
        return
    dc = sum(cjk(d) for d in ds)
    ratio = dc / total
    lo, hi = cfg_get(cfg, "dialogue_ratio_min", 0.30), cfg_get(cfg, "dialogue_ratio_max", 0.60)
    ok = lo <= ratio <= hi
    mark = "✓" if ok else ("✗" if strict(cfg) else "△")
    print("    对话 %d 字 / 总 %d 字 = %.0f%% (参考 %d~%d%%) %s" % (dc, total, ratio * 100, lo * 100, hi * 100, mark))
    if not ok:
        gate(cfg, r, "对话占比", "%.0f%%" % (ratio * 100), "%d~%d%%" % (lo * 100, hi * 100))

def check_explain(cfg, text, r):
    print("【7】解释/说教/上帝视角  [红线]")
    words = cfg_get(cfg, "explanation", []) + cfg_get(cfg, "godview", []) + cfg_get(cfg, "preach", [])
    if not words:
        return
    body = strip_markdown(text)
    hits = hit_list(body, words)
    if hits:
        for w, pos in hits:
            print("    ✗ 【%s】: …%s…" % (w, ctx(body, pos)))
            r.add_s1("解释/说教/上帝视角【%s】" % w)
    else:
        print("    ✓ 无解释/说教/上帝视角")

def check_info_leak(cfg, text, r):
    print("【8】金手指硬泄露（对外人说系统术语）  [红线]")
    hard = cfg_get(cfg, "info_hard", [])
    soft = cfg_get(cfg, "info_soft", [])
    body = strip_markdown(strip_dialogue(text))
    hits = hit_list(body, hard)
    for w, pos in hits:
        print("    ✗ 【%s】: …%s…" % (w, ctx(body, pos)))
        r.add_s1("金手指硬泄露【%s】" % w)
    if not hits:
        print("    ✓ 无金手指硬泄露")

def check_density(cfg, text, r):
    print("【9】密度检查（/千字）")
    body = strip_markdown(text)
    total = cjk(body)
    if not total:
        return
    rows = [
        ("副词", cfg_get(cfg, "adverbs", [])),
        ("连接词", cfg_get(cfg, "connectives", [])),
        ("成语", cfg_get(cfg, "idioms", [])),
        ("'的'字", ["的"]),
    ]
    for name, words in rows:
        n = sum(text.count(w) for w in words)
        pk = per1000(n, total)
        ref = cfg_get(cfg, name.replace("'", "") + "_per_1000", 999)
        ok = pk <= ref
        mark = "✓" if ok else ("✗" if strict(cfg) else "△")
        print("    %s: %.1f (参考 ≤%s) %s" % (name, pk, ref, mark))
        if not ok:
            gate(cfg, r, name, "%.1f" % pk, "≤%s" % ref)

def check_character_fingerprint(cfg, text, r):
    print("【10】角色指纹（每角色至少一个标志词）")
    chars = cfg_get(cfg, "characters", [])
    if not chars:
        return
    for ch in chars:
        fp_key = "fingerprint_" + ch
        fps = cfg_get(cfg, fp_key, [])
        if not fps:
            continue
        found = [w for w in fps if w in text]
        if found:
            print("    %s ✓ %s" % (ch, found))
        else:
            print("    %s ⚠ 指纹缺失: %s" % (ch, fps))
            r.add_warn("角色【%s】指纹缺失" % ch)

def check_gaze(cfg, text, r):
    print("【11】视线密度")
    words = cfg_get(cfg, "gaze_words", GAZE_DEFAULT)
    body = strip_markdown(strip_dialogue(text))
    total = cjk(body)
    if not total:
        return
    n = sum(body.count(w) for w in words)
    pk = per1000(n, total)
    ref = cfg_get(cfg, "gaze_per_1000", 25)
    mark = "✓" if pk <= ref else ("✗" if strict(cfg) else "△")
    print("    视线词 %d 次 = %.1f/千字 (参考 ≤%d) %s" % (n, pk, ref, mark))
    if pk > ref:
        gate(cfg, r, "视线密度", "%.1f" % pk, "≤%d" % ref)
        r.add_warn("视线密度偏高，可能'看来看去'")

def check_gesture(cfg, text, r):
    print("【12】神态/动作复用")
    words = cfg_get(cfg, "gesture_words", GESTURE_DEFAULT)
    body = strip_markdown(strip_dialogue(text))
    mx = cfg_get(cfg, "gesture_reuse_max", 3)
    for w in words:
        n = body.count(w)
        if n >= mx:
            print("    ⚠ 【%s】出现 %d 次 ≥%d 次" % (w, n, mx))
            r.add_warn("神态动作【%s】复用 %d 次" % (w, n))
    if not any(body.count(w) >= mx for w in words):
        print("    ✓ 无过度复用")

def check_hook(cfg, text, r):
    print("【13】章末钩子")
    sents = split_full(text)
    if not sents:
        print("    ⚠ 无完整句")
        return
    last = sents[-1].strip()[-50:] if sents else ""
    hooks = ["？", "！", "……", "——", "——", "悬念", "倒", "悬", "惊", "险"]
    hit = any(h in last for h in hooks)
    print("    末句: …%s" % last)
    if hit:
        print("    ✓ 含钩子信号")
    else:
        print("    ⚠ 末句缺钩子信号（建议加 ? ! … 等）")
        r.add_warn("章末缺钩子")

# ---------------- 主逻辑 ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chapter", help="章节 .md 路径")
    ap.add_argument("-c", "--config", required=True, help="书配置 .yaml/.json")
    ap.add_argument("--json", help="导出 JSON 报告路径")
    ap.add_argument("--strict", action="store_true", help="强制 strict 模式")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.strict:
        cfg["strict"] = True
    text = load_text(args.chapter)
    r = R()

    print("=" * 60)
    print("novel_check · 章节体检")
    print("=" * 60)
    check_words(cfg, text, r)
    check_banned(cfg, text, r)
    check_thunder(cfg, text, r)
    check_metaphors(cfg, text, r)
    check_rhythm(cfg, text, r)
    check_paragraphs(cfg, text, r)
    check_dialogue(cfg, text, r)
    check_explain(cfg, text, r)
    check_info_leak(cfg, text, r)
    check_density(cfg, text, r)
    check_character_fingerprint(cfg, text, r)
    check_gaze(cfg, text, r)
    check_gesture(cfg, text, r)
    check_hook(cfg, text, r)

    print("=" * 60)
    print("【红线】%d  处（必改）" % len(r.s1))
    for x in r.s1:
        print("  ·", x)
    print("【警告】%d  处" % len(r.warn))
    for x in r.warn:
        print("  ·", x)
    print("【数值偏离】%d  处" % len(r.ranges))
    for name, got, ref in r.ranges:
        print("  · %s: 实测 %s vs 参考 %s" % (name, got, ref))
    print("【建议】%d  条" % len(r.notes))
    for x in r.notes:
        print("  ·", x)
    print("=" * 60)

    data = {
        "red_lines": r.s1,
        "warnings": r.warn,
        "ranges": [{"name": n, "got": g, "ref": r} for n, g, r in r.ranges],
        "notes": r.notes,
    }
    if args.json:
        open(args.json, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
        print("已导出 JSON: %s" % args.json)

    if r.s1:
        sys.exit(1)

if __name__ == "__main__":
    main()
