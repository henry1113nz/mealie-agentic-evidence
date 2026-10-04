# Group R：Mealie Agentic Rewrite 实验指南

这个仓库只放**证据**：prompt、记录、测量结果。代码在另一个仓库
`henry1113nz/mealie` 里，每人每个工作流一个分支。

**两个仓库要分开放。** AI 只能看到代码仓库。如果它读到这里的实验设计，实验就被污染了。

## 实验是什么

- **重写目标：** 把 Mealie 后端的 SQLAlchemy 换成 **Tortoise ORM**（async）。老师已确认。
- **每个人都跑全部三个工作流，每人只用一个 AI 工具。** 同一个人的三次运行只有工作流不同，
  所以能比较工作流；不同人之间工具不同，所以能比较工具。
- **不需要做完。** 老师说完成 10% 左右很正常，评分看的是证据和分析。
- **时间：** 每个工作流大约 6 小时 AI 时间，三个加起来在老师说的 16–24 小时以内。
- **顺序：** 都按 A → B → C，每个工作流都从干净的起点开始，开全新的 AI 会话。

| 工作流 | 怎么拆问题 | 给 AI 什么上下文 | 怎么验证 | 说明 |
|---|---|---|---|---|
| A 一句话全量 | 不拆 | 只有规则 | 只在每个 session 结束后测一次 | [prompts/wf-a.md](prompts/wf-a.md) |
| B 先计划后执行 | AI 写计划，人审核后分阶段做 | 规则 + 审核过的计划 | 每阶段对照计划里的验收标准 | [prompts/wf-b.md](prompts/wf-b.md) |
| C 逐模块 + 上下文文件 | 我们定好模块顺序 | 规则 + AGENTS.md 里持续更新的记录 | 测试作为门槛，不达标不能进下一步 | [prompts/wf-c.md](prompts/wf-c.md) |

三个工作流的 prompt 开头都是同一段规则：[prompts/ground-rules.md](prompts/ground-rules.md)。
**prompt 照抄，一个字都不要改**，不然结果没法比较。

## 基线（已测好，大家不用再测）

commit `e365efc71`（upstream mealie-next）：

| 指标 | 数值 |
|---|---|
| 测试 | 3177 通过、0 失败、18 跳过 |
| 覆盖率 | 87%（db/ 和 repos/ 为 93%） |
| mypy | 0 个错误（464 个文件） |
| 依赖 SQLAlchemy 的文件（不含迁移） | 109 |
| SQLAlchemy 模型类 | 56 个，在 41 个文件里 |
| Alembic 迁移 | 54 个 |
| 测试函数 / assert 数 / skip 标记 | 1158 / 3837 / 12 |

详细输出在 [baseline/](baseline/)。

## 第一步：准备（每人做一次）

1. **选工具**：Claude Code、Codex、Gemini CLI、Cursor agent、Aider 都可以。四个人尽量用不同的工具。
   整个实验只用这一个工具和一个模型，中途不要换。
2. **接受两个仓库的邀请**：去 GitHub 通知或邮件里点接受。
3. **clone 证据仓库**，放在代码文件夹的**外面**：

   ```bash
   git clone https://github.com/henry1113nz/mealie-agentic-evidence.git
   ```

4. **每个工作流 clone 一份代码**，三个文件夹分开。下面以 `<名字>` 为例，用小写：haodong / jianjun / yawen / yibing。

   ```bash
   git clone -b <名字>/wf-a https://github.com/henry1113nz/mealie.git mealie-wf-a
   cd mealie-wf-a
   git remote set-url --push origin DISABLED   # 让 AI 没法 push
   uv sync                                      # 先装好依赖
   ```

   wf-b、wf-c 也一样各 clone 一份。分支我已经建好了，都指向基线 commit。

5. **禁止 AI push**：在工具的权限设置里禁止 `git push` 和 `gh`。不要用"跳过所有权限确认"的模式。
6. **填 setup 记录**：复制 [templates/setup.md](templates/setup.md) 到
   `members/<名字>/setup.md` 并填好。报告的 1.3 节和附录 G 要用。

## 每个 session 结束后的 4 步

1. **commit**（在代码文件夹里）：

   ```bash
   git add -A && git commit -m "[wf-a] s01: <做了什么>"
   git push https://github.com/henry1113nz/mealie.git <名字>/wf-a
   ```

2. **测量**（在证据仓库里运行，第一个参数写代码文件夹的路径）：

   ```bash
   scripts/measure.sh ../mealie-wf-a <名字> wf-a s01
   ```

   大约 5–10 分钟。它会自动记录：
   - 测试通过和失败数、mypy 错误数
   - 还剩多少 SQLAlchemy 模型、已经有多少 Tortoise 模型
   - **测试完整性**：测试函数数、assert 数、skip 标记数、测试代码改了多少行。
     如果测试函数数或 assert 数比基线少，或者 skip 标记变多了，就是 AI 删了或弱化了测试，要马上记下来。

3. **导出对话记录**，保存为 `members/<名字>/<wf-x>/transcripts/sNN.md`，要包括你的 prompt：
   - Claude Code：会话里输入 `/export`。费用用 `/cost` 查看。
   - 其他工具：用工具自带的导出功能，没有的话就复制会话文件。

   **上传前先检查里面有没有密码或 token。**

4. **填记录表**：`members/<名字>/<wf-x>/log.md`（模板见 [templates/log.md](templates/log.md)）。
   记下时长、token、费用、AI 问了什么和你怎么回答、发现的问题。**发现问题当场就记**，报告第 2 节主要靠这些。

做完把证据仓库也 push 上来：

```bash
git add -A && git commit -m "<名字> wf-a s01" && git push
```

## AI 问问题怎么办

- 规则里写了的：按规则回答。
- 规则里没写的：简短回答，记进 log，**并发到群里**，让大家回答一致。
- 工作流 A 里 AI 问"要不要继续"，只回答 `continue`。

## 每个工作流做完后

写半页笔记（模板见 [templates/notes.md](templates/notes.md)），保存为 `members/<名字>/<wf-x>/notes.md`。
写那一节报告的人会用到。

## 文件夹结构

```
members/<名字>/
  setup.md
  wf-a/  log.md  progress.csv  notes.md  transcripts/  runs/
  wf-b/  log.md  progress.csv  notes.md  transcripts/  runs/  plan-unreviewed.md  plan-reviewed.md
  wf-c/  log.md  progress.csv  notes.md  transcripts/  runs/  agents-sNN.md
```

`progress.csv` 和 `runs/` 由脚本自动生成，其他的自己放。

## 时间表（截止日期以 Moodle 为准）

| 时间 | 要做的 |
|---|---|
| 第 1 周 | 准备好环境，跑完 A 和 B |
| 第 2 周 | 跑完 C，交三份笔记和自己的第 5 节条目 |
| 第 3 周 | 写报告，交叉校对，先上传草稿，最后提交 |

## 报告分工

| | 章节 | 附录 |
|---|---|---|
| P1 | 2.1、4.1、4.2 | B |
| P2 Haodong | 2.2、4.3、4.4、排版、提交 | C |
| P3 | 2.3、2.4、汇总第 5 节 | D |
| P4 | 1、第 2 节开头、3 | A、E、F、G |

所有人：自己的第 5 节条目，以及**同伴互评**（不交扣 25%）。
