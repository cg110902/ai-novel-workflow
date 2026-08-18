#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
misunder.py —— 误会台账 CLI（喜剧/误会流专用，多书目录）

误会流喜剧的命根子：谁误会了谁、误会成什么、戳破没有。忘了记 = 雪球崩坏。

用法:
    python3 misunderstood.py add M05 "周德厚" "陈闲" "上头派来查私库的人" --ch 1 --book ../新书
    python3 misunderstood.py burst M05 --ch 20 --book ../新书      # 戳破误会
    python3 misunderstood.py list --open --book ../新书
    python3 misunderstood.py export --book ../新书
"""
import sys, os, json, argparse

def db_path(args):
    d = args.book or "."
    return os.path.join(d, "misunderstandings.json")

def load(p):
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return []

def save(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def cmd_add(a):
    p = db_path(a)
    data = load(p)
    if any(x["id"] == a.id for x in data):
        print("已存在误会 %s" % a.id); return
    data.append({"id": a.id, "who": a.who, "about": a.about, "content": a.content,
                 "degree": a.degree or "将信将疑", "opened_ch": a.ch or "-",
                 "burst_ch": None, "status": "open"})
    save(p, data)
    print("已登记误会 %s: %s 以为 %s 是「%s」@第%s章" % (a.id, a.who, a.about, a.content, a.ch))

def cmd_burst(a):
    p = db_path(a)
    data = load(p)
    for x in data:
        if x["id"] == a.id:
            x["status"] = "burst"; x["burst_ch"] = a.ch or "-"
            save(p, data)
            print("已戳破误会 %s @第%s章" % (a.id, a.ch))
            return
    print("未找到误会 %s" % a.id)

def cmd_list(a):
    p = db_path(a)
    data = load(p)
    for x in data:
        if a.open and x["status"] != "open":
            continue
        if a.burst and x["status"] != "burst":
            continue
        mark = "◻ 未戳破" if x["status"] == "open" else "■ 已戳破"
        print("%s [%s] 第%s章: %s 以为 %s 是「%s」(程度:%s)%s"
              % (mark, x["id"], x["opened_ch"], x["who"], x["about"], x["content"], x["degree"],
                 (" | 第%s章破" % x["burst_ch"]) if x["burst_ch"] else ""))

def cmd_export(a):
    p = db_path(a)
    data = load(p)
    op = [x for x in data if x["status"] == "open"]
    bu = [x for x in data if x["status"] == "burst"]
    lines = ["# 误会台账", "", "> 规则：挖一个记一个，戳破一个销一个。",
             "", "## 未戳破的误会", "", "| # | 谁误会了谁 | 误会成什么 | 程度 | 埋设章 |",
             "|---|---|---|---|---|"]
    for x in op:
        lines.append("| %s | %s → %s | %s | %s | %s |" % (x["id"], x["who"], x["about"], x["content"], x["degree"], x["opened_ch"]))
    lines += ["", "## 已戳破的误会", "", "| # | 谁误会了谁 | 误会成什么 | 埋设章 | 戳破章 |",
              "|---|---|---|---|---|"]
    for x in bu:
        lines.append("| %s | %s → %s | %s | %s | %s |" % (x["id"], x["who"], x["about"], x["content"], x["opened_ch"], x["burst_ch"]))
    out = os.path.join(a.book or ".", "误会台账.md")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("已导出 %s（未戳破 %d / 已戳破 %d）" % (out, len(op), len(bu)))

def main():
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--book", default=None, help="书目录")
    ap = argparse.ArgumentParser(parents=[parent])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("add", parents=[parent]); p1.add_argument("id"); p1.add_argument("who")
    p1.add_argument("about"); p1.add_argument("content")
    p1.add_argument("--degree"); p1.add_argument("--ch")
    p2 = sub.add_parser("burst", parents=[parent]); p2.add_argument("id"); p2.add_argument("--ch")
    p3 = sub.add_parser("list", parents=[parent]); p3.add_argument("--open", action="store_true")
    p3.add_argument("--burst", action="store_true"); p3.add_argument("--all", action="store_true")
    sub.add_parser("export", parents=[parent])
    a = ap.parse_args()
    if a.cmd == "add": cmd_add(a)
    elif a.cmd == "burst": cmd_burst(a)
    elif a.cmd == "list": cmd_list(a)
    elif a.cmd == "export": cmd_export(a)

if __name__ == "__main__":
    main()
