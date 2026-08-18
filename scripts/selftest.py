#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest.py —— 包自检：一次跑通全部脚本 + 全部示例，防回归。

用法:
    python3 scripts/selftest.py        # 在包根目录或任意目录运行均可

检查项:
  1. scripts/ 下所有脚本语法可解析
  2. 每本示例书的每一章跑 novel_check，红线(必改)必须为 0
  3. state / plotlines / misunderstood 三件套 round-trip
  4. fix_quotes 幂等(已规范文本第二次运行 0 改动)
退出码: 0=全过, 1=有失败
"""
import os, sys, json, subprocess, tempfile, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
CONFIGS = os.path.join(ROOT, "configs")
EXAMPLES = os.path.join(ROOT, "examples")

fails = []
def ok(msg): print("  ✓", msg)
def bad(msg):
    print("  ✗", msg)
    fails.append(msg)

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

print("=" * 60)
print("selftest · 包自检")
print("=" * 60)

# 1. 语法
print("[1] 脚本语法")
for f in sorted(glob.glob(os.path.join(SCRIPTS, "*.py"))):
    r = run([sys.executable, "-m", "py_compile", f])
    (ok if r.returncode == 0 else bad)(os.path.basename(f))

# 2. 章节体检
print("[2] 示例章节体检(红线必须为 0)")
total_ch = 0
example_books = glob.glob(os.path.join(EXAMPLES, "*"))
for bookdir in example_books:
    if not os.path.isdir(bookdir):
        continue
    book = os.path.basename(bookdir)
    chapters = sorted(glob.glob(os.path.join(bookdir, "章节", "*.md")))
    if not chapters:
        continue
    cfg = os.path.join(CONFIGS, "example.yaml")
    for ch in chapters:
        total_ch += 1
        jpath = tempfile.mktemp(suffix=".json")
        r = run([sys.executable, os.path.join(SCRIPTS, "novel_check.py"),
                 ch, "-c", cfg, "--json", jpath])
        if r.returncode != 0:
            bad(os.path.basename(ch) + " (脚本异常)")
            continue
        try:
            data = json.load(open(jpath, encoding="utf-8"))
        except Exception:
            bad(os.path.basename(ch) + " (json 解析失败)")
            continue
        finally:
            if os.path.exists(jpath):
                os.remove(jpath)
        if data.get("red_lines"):
            bad("%s/%s 红线 %d 处" % (book, os.path.basename(ch), len(data["red_lines"])))
        else:
            ok("%s/%s" % (book, os.path.basename(ch)))
print("  共体检 %d 章" % total_ch)

# 3. 三件套 round-trip
print("[3] 台账/状态机 round-trip")
tmp = tempfile.mkdtemp()
run([sys.executable, os.path.join(SCRIPTS, "state.py"), "init", "5", "--book", tmp])
run([sys.executable, os.path.join(SCRIPTS, "state.py"), "mark", "1", "起草", "--book", tmp])
r = run([sys.executable, os.path.join(SCRIPTS, "state.py"), "next", "--book", tmp])
(ok if "第1章" in r.stdout else bad)("state.py next 指向正确")
run([sys.executable, os.path.join(SCRIPTS, "plotlines.py"), "add", "V01", "测试伏笔", "--ch", "1", "--book", tmp])
run([sys.executable, os.path.join(SCRIPTS, "plotlines.py"), "close", "V01", "--ch", "2", "--book", tmp])
r = run([sys.executable, os.path.join(SCRIPTS, "plotlines.py"), "list", "--closed", "--book", tmp])
(ok if "已填" in r.stdout else bad)("plotlines 挖/销/查")
run([sys.executable, os.path.join(SCRIPTS, "misunderstood.py"), "add", "M01", "甲", "乙", "误会", "--ch", "1", "--book", tmp])
r = run([sys.executable, os.path.join(SCRIPTS, "misunderstood.py"), "list", "--all", "--book", tmp])
(ok if "M01" in r.stdout else bad)("misunderstood 挖/查")

# 4. fix_quotes 幂等
print("[4] fix_quotes 幂等")
chapters = []
for bookdir in example_books:
    if os.path.isdir(bookdir):
        chapters += glob.glob(os.path.join(bookdir, "章节", "*.md"))
if chapters:
    run([sys.executable, os.path.join(SCRIPTS, "fix_quotes.py")] + chapters)
    r2 = run([sys.executable, os.path.join(SCRIPTS, "fix_quotes.py")] + chapters)
    changed = [l for l in r2.stdout.splitlines() if l.startswith("已规范化")]
    (ok if not changed else bad)("fix_quotes 第二次运行 0 改动")

print("=" * 60)
if fails:
    print("结果: ✗ 失败 %d 项" % len(fails))
    for f in fails:
        print("   -", f)
    sys.exit(1)
else:
    print("结果: ✓ 全部通过")
