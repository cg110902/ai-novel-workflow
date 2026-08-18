#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plotlines.py —— 伏笔台账 CLI（挖一个记一个，填一个销一个，多书目录）

用法:
    python3 plotlines.py add V11 "伏笔内容" --ch 4 --plan "第20章回收" --book ../新书
    python3 plotlines.py close V03 --ch 25 --book ../新书
    python3 plotlines.py list --open --book ../新书
    python3 plotlines.py export --book ../新书
默认 --book 为当前目录。
"""
import sys, os, json, argparse

def db_path(args):
    d = args.book or "."
    return os.path.join(d, "plotlines.json")

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
        print("已存在伏笔 %s，先 close 或换 id" % a.id); return
    data.append({"id": a.id, "content": a.content, "opened_ch": a.ch or "-",
                 "plan": a.plan or "-", "closed_ch": None, "status": "open"})
    save(p, data)
    print("已登记伏笔 %s @第%s章: %s" % (a.id, a.ch, a.content))

def cmd_close(a):
    p = db_path(a)
    data = load(p)
    for x in data:
        if x["id"] == a.id:
            x["status"] = "closed"; x["closed_ch"] = a.ch or "-"
            save(p, data)
            print("已回收伏笔 %s @第%s章" % (a.id, a.ch))
            return
    print("未找到伏笔 %s" % a.id)

def cmd_list(a):
    p = db_path(a)
    data = load(p)
    for x in data:
        if a.open and x["status"] != "open":
            continue
        if a.closed and x["status"] != "closed":
            continue
        mark = "◻ 未填" if x["status"] == "open" else "■ 已填"
        print("%s [%s] 第%s章埋: %s | 计划: %s%s"
              % (mark, x["id"], x["opened_ch"], x["content"], x["plan"],
                 (" | 第%s章收" % x["closed_ch"]) if x["closed_ch"] else ""))

def cmd_export(a):
    p = db_path(a)
    data = load(p)
    rows_open = [x for x in data if x["status"] == "open"]
    rows_closed = [x for x in data if x["status"] == "closed"]
    lines = ["# 伏笔台账", "", "> 规则：挖一个记一个，填一个销一个。",
             "", "## 未填伏笔", "", "| # | 伏笔内容 | 埋设章节 | 计划回收 |",
             "|---|---|---|---"]
    for x in rows_open:
        lines.append("| %s | %s | %s | %s |" % (x["id"], x["content"], x["opened_ch"], x["plan"]))
    lines += ["", "## 已填伏笔", "", "| # | 伏笔内容 | 埋设章节 | 回收章节 |",
              "|---|---|---|---"]
    for x in rows_closed:
        lines.append("| %s | %s | %s | %s |" % (x["id"], x["content"], x["opened_ch"], x["closed_ch"]))
    out = os.path.join(a.book or ".", "伏笔台账.md")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("已导出 %s（未填 %d / 已填 %d）" % (out, len(rows_open), len(rows_closed)))

def main():
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--book", default=None, help="书目录")
    ap = argparse.ArgumentParser(parents=[parent])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("add", parents=[parent]); p1.add_argument("id"); p1.add_argument("content")
    p1.add_argument("--ch"); p1.add_argument("--plan")
    p2 = sub.add_parser("close", parents=[parent]); p2.add_argument("id"); p2.add_argument("--ch")
    p3 = sub.add_parser("list", parents=[parent]); p3.add_argument("--open", action="store_true")
    p3.add_argument("--closed", action="store_true"); p3.add_argument("--all", action="store_true")
    sub.add_parser("export", parents=[parent])
    a = ap.parse_args()
    if a.cmd == "add": cmd_add(a)
    elif a.cmd == "close": cmd_close(a)
    elif a.cmd == "list": cmd_list(a)
    elif a.cmd == "export": cmd_export(a)

if __name__ == "__main__":
    main()
