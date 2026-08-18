#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
state.py —— 章节生产状态机（9 道工序逐章打钩 + 断点恢复 + 多书目录）

用法:
    python3 state.py init 30 --book ../新书-祸害修仙界
    python3 state.py mark 4 起草 --book ../新书-祸害修仙界
    python3 state.py status --book ../新书-祸害修仙界
    python3 state.py next --book ../新书-祸害修仙界
默认 --book 为当前目录。每本书一个 state.json，互不覆盖。
"""
import sys, os, json, argparse

STEPS = ["情报包", "锁细纲", "起草", "双盲批判", "定向重写", "去AI味", "排版", "一致性", "回灌"]

def db_path(args):
    d = args.book or "."
    return os.path.join(d, "state.json")

def load(p):
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return None

def save(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def cmd_init(a):
    p = db_path(a)
    save(p, {"total": int(a.n), "chapters": {}})
    print("已建 %d 章进度 → %s" % (int(a.n), p))

def cmd_mark(a, done=True):
    p = db_path(a)
    d = load(p)
    if d is None:
        print("先 init"); return
    if a.step not in STEPS:
        print("工序名必须是: %s" % "、".join(STEPS)); return
    ch = str(int(a.ch))
    c = d["chapters"].setdefault(ch, {})
    c[a.step] = done
    save(p, d)
    print("第%s章 · %s → %s" % (ch, a.step, "✓" if done else "·"))

def cmd_status(a):
    p = db_path(a)
    d = load(p)
    if d is None:
        print("尚无进度，先 python3 state.py init N"); return
    print("总章节: %d | 工序: %s" % (d["total"], "→".join(STEPS)))
    print("-" * 66)
    print("章".ljust(5) + "".join(s[:1].ljust(3) for s in STEPS) + "进度")
    for i in range(1, d["total"] + 1):
        c = d["chapters"].get(str(i), {})
        marks = "".join(("✓".ljust(3) if c.get(s) else "·".ljust(3)) for s in STEPS)
        done = sum(1 for s in STEPS if c.get(s))
        bar = "█" * (done * 2) + "░" * ((len(STEPS) - done) * 2)
        print(str(i).ljust(5) + marks + "%d/%d %s" % (done, len(STEPS), bar))
    for i in range(1, d["total"] + 1):
        c = d["chapters"].get(str(i), {})
        for s in STEPS:
            if not c.get(s):
                print("-" * 66)
                print("▶ 下一步: 第%d章 · 工序「%s」" % (i, s))
                return
    print("-" * 66)
    print("▶ 全部完成")

def cmd_next(a):
    p = db_path(a)
    d = load(p)
    if d is None:
        print("先 init"); return
    for i in range(1, d["total"] + 1):
        c = d["chapters"].get(str(i), {})
        for s in STEPS:
            if not c.get(s):
                print("第%d章 · 「%s」" % (i, s))
                return
    print("全部完成")

def main():
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--book", default=None, help="书目录(存 state.json 的位置)")
    ap = argparse.ArgumentParser(parents=[parent])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("init", parents=[parent]); p1.add_argument("n")
    p2 = sub.add_parser("mark", parents=[parent]); p2.add_argument("ch"); p2.add_argument("step")
    p3 = sub.add_parser("unmark", parents=[parent]); p3.add_argument("ch"); p3.add_argument("step")
    sub.add_parser("status", parents=[parent])
    sub.add_parser("next", parents=[parent])
    a = ap.parse_args()
    if a.cmd == "init": cmd_init(a)
    elif a.cmd == "mark": cmd_mark(a, True)
    elif a.cmd == "unmark": cmd_mark(a, False)
    elif a.cmd == "status": cmd_status(a)
    elif a.cmd == "next": cmd_next(a)

if __name__ == "__main__":
    main()
