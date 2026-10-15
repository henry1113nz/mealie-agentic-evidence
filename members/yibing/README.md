# Yibing 的实验记录检查点

这是截至 2026 年 10 月 13 日的真实进度。A 和 C 已完成记录并已 push，B 按本人决定跳过。

- A：一次完整尝试结束，提交 827d7d186；SQLite 3182 通过、16 跳过，mypy 通过。事后 Codex 审核发现两处 PostgreSQL 测试提前返回，未由协调 AI 修改。详见 wf-a/log.md、notes.md 和 runs/s01/supplemental/。
- B：原始计划和修订提案已保存，但按本人决定跳过，没有 B 实现结果。
- C：C1-C7 已完成；最终独立测量 3277 通过、6 失败、18 跳过，SQLAlchemy 文件/模型为 0，mypy 为 0。
- Push：`yibing/wf-a` 和 `yibing/wf-c` 已推送到 GitHub，远程提交哈希已核对。
- 报告：report-draft/ 中是更新后的 P1 Word/PDF，包含 A、跳过 B 的说明和 C 结果。
- 贡献：contribution-summary.md 汇总本学期实际 issue、PR 和分支尝试，另交 P3。

原始 prompts、可见对话、提交、测量、失败与修复记录都保存在各工作流目录。transcripts/s01-native/ 包含主会话与子会话的可见记录，不含隐藏推理。时间/token 使用实际记录；缺失的费用、人工审核分钟数不编造。

coordinator/ 保留准备、独立 Codex 审核、计量适配器和报告生成过程。setup.json 是实验开始前的请求配置快照，实际生效配置以 setup.md、settings-observation.json 和 native session-tree.json 为准。协调与报告工作不计入实验 AI 时间，也不冒充人工审核。

没有 AI push、对外发送消息、提交最终报告或代填同伴互评。此目录是自己的证据覆盖包，不是独立 Git 仓库。最终上传时仅复制到真实证据仓库的 members/yibing/，不得覆盖其他成员或重建远端历史。
