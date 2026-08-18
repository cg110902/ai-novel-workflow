# ai-novel-workflow · 通用 AI 网文创作流程（SKILL 包）

把「AI 第一稿不能用」变成「可验收连载」的完整流水线。**Agent 即引擎，无需外部 LLM API。**

## 这是什么形态？
一个 **SKILL 包** = 三层合一：
- **指令层**：`AGENTS.md` + `SKILL.md`（agent 入口）+ `docs/`（总纲、Rubric、读感终审、去AI味、深度诊断）
- **工具层**：`scripts/`（7 个零依赖 python 脚本，含自检）+ `configs/`（书配置）
- **模板层**：`templates/`（每本书的骨架）+ `examples/`（三本成品书示例）

## 核心原则（读感第一，终审在用户）
- 脚本是**体检报告**，不是**及格线**；红线（禁用词/泄露/说教/设定冲突）必改，数值偏出只作提示。
- **终审由用户负责**：用户是第一读者、最终裁决；Agent 交付前用《读感终审清单》自检预审。
- 检测标准**动态**：随题材、章节类型、用户反馈调。

## 怎么用
### 方式 A：给 Agent 加载（推荐，本包原生场景）
把整个目录交给任意能读文件的 Agent，说：
> 加载这个 skill：`ai-novel-workflow`，然后我要开新书……

### 方式 B：当普通仓库用（BYOK 版）
脚本零依赖、openai 兼容接口友好。

### 方式 C：合并进你自己的项目
目录结构自包含，直接拖进你的仓库即可。

## 自检
```bash
python3 scripts/selftest.py    # 全过 = 没改坏；任何 ✗ 都要修
```

## 目录导航
```
ai-novel-workflow/
├── AGENTS.md / SKILL.md     # agent 入口（先读这两个）
├── README.md / VERSION / CHANGELOG.md
├── docs/                    # 总纲 / Rubric / 读感终审 / 去AI味 / 深度诊断 / 复盘
├── scripts/                 # 7 个零依赖工具（含 selftest 自检）
├── configs/                 # 书配置（换题材只换这个）
├── templates/               # 新书骨架模板（00-指令书 ~ 05-误会台账）
└── examples/                # 三本成品书（格式示范 + 风格锚，可删）
```

## 许可
自用 / 商用项目自由使用；脚本零第三方依赖，可直接分发。
