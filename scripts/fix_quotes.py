#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_quotes.py —— 中文引号规范化（直引号 → 弯引号）

排版工序的固定动作：写完/改完正文后跑一遍，保证对话引号是中文弯引号。
用法:
    python3 fix_quotes.py <文件.md>
    python3 fix_quotes.py <目录>          # 递归处理目录下所有 .md
    python3 fix_quotes.py a.md b.md dir/
"""
import sys, os, re, glob

def norm(text):
    """成对直引号 → 弯引号；但跳过代码块(``` 围栏内)。"""
    lines = text.split("\n")
    out = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue
        line = re.sub(r'"([^"\n]*)"', r'"\\1"', line)
        line = re.sub(r"'([^'\n]*)'", r"''\\1'", line)
        out.append(line)
    return "\n".join(out)

def process(path):
    if os.path.isdir(path):
        files = glob.glob(os.path.join(path, '**', '*.md'), recursive=True)
    else:
        files = [path]
    changed = 0
    for f in files:
        s = open(f, encoding='utf-8').read()
        s2 = norm(s)
        if s2 != s:
            open(f, 'w', encoding='utf-8').write(s2)
            changed += 1
            print('已规范化:', f)
    print('共处理 %d 个文件' % changed)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for p in sys.argv[1:]:
        process(p)
