# Project 04 学生指南（Project Instruction）

## 你将做什么（一句话）
把 **SWE-agent（或同类 coding agent）**当作一个复杂系统：它由 LLM 调用、工具调用、子进程、IO 组成。你要做一个 **可复现 benchmark pack + 全链路 profiling 报告生成器**，并用 **cgroup/PSI** 解释资源约束如何改变成功率与失败模式。

> 项目主页：`README.md`  
> 评分细则：`RUBRIC.md`

---

## 适合谁选

- 适合对“agent runtime / 工具调用 / 可复现实验 / 失败模式”感兴趣的同学。
- 适合喜欢工程化（日志 schema、自动化分析、对照实验）。
- 如果你不想处理外部变量（LLM API、网络、依赖安装），需要谨慎：本项目核心挑战之一就是控制变量。

---

## 先修/准备清单（开始前 1–2 天内搞定）

- Ubuntu VM（能跑 Python/Node 工具链）
- 能跑通 SWE-agent（或你选定的 agent）的最小 demo
- 基础观测工具：`pidstat`, `vmstat`, `iostat`, `ss`
- 证据链信号（VM 友好）：
  - PSI：`/proc/pressure/*`
  - cgroup v2：`cpu.stat`, `memory.current`, `memory.stat`
- 如果用远端 LLM API：
  - 必须写清模型/参数
  - 必须写清成本上限与估算（并在实验中遵守）

---

## 你需要交付什么

### 1) 任务包（benchmark pack，必交）
- 10–20 个任务（小而稳定比“大而漂”重要）
- 每个任务必须包含：
  - 输入 repo + issue 描述
  - 成功判定（tests pass / diff matches / oracle 输出）
  - timeout budget

### 2) 全链路 profiling 日志 + 报告生成器（必交）
- 每次运行输出 machine-readable 日志（建议 JSONL）
- 至少包含：
  - tool call 开始/结束时间、命令/参数摘要、退出码
  - （若有）LLM 等待时间
  - 本地 CPU 时间/资源使用（RSS 峰值、上下文切换近似等）
- 自动生成 summary：
  - 成功率
  - 总时长分解（LLM 等待 vs 工具执行 vs 本地 CPU）
  - 失败模式统计（循环、震荡、改错文件、flaky tests 等）

### 3) 资源约束实验（必交）
- cgroup v2 CPU quota throttling
- cgroup v2 memory limit
- 必须解释机制（用信号证明），而不是只说“更慢/更容易失败”。

---

## 怎么衡量“做到了什么程度”

最终按 `RUBRIC.md` 打分；这里给你一个自检梯度。

### 最低达标（UG 友好）
- 10 个任务里至少 5 个能稳定跑完（成功或失败都可，但要可复现）
- JSONL 日志有基本字段
- CPU quota 或 memory limit 至少一个实验完成并解释

### 标准完成（MS 建议目标）
- 10–20 个任务 pack
- 时间分解齐全（LLM 等待/工具执行/本地 CPU）
- CPU quota + memory limit 都完成
- 至少 1 个策略/缓解（timeouts、tool allowlist、缓存依赖等）有对照验证

### Stretch（PhD/加分）
- 失败模式 taxonomy 规范化并可自动分类
- 对策略副作用做量化（例如减少循环但降低成功率）并给出改进

---

## 本项目核心难点（你要把力气花在这里）

1) **把 agent 行为变成可度量系统**：没有日志 schema 与自动化分析，后续结论都站不住。  
2) **外部变量太多**：模型/网络/依赖/仓库状态会引入噪声；你需要控制变量、做对照。  
3) **机制解释而非经验总结**：资源约束如何触发具体失败模式（OOM、超时、循环）必须有证据链。

---

## 选题建议（降低踩坑）

- 任务包尽量选择：能离线跑、依赖少、测试时间可控。
- 先把“日志与可复现”打稳，再谈“agent 改进”。
- 把成本/配额写进实验计划：不控制成本会让实验不可持续。

---

## 前两周怎么开始（建议的最小路径）

- W1：选定 agent 版本 + 设计任务格式（YAML/JSON 都可）
- W2：
  - 跑通 1 个任务端到端
  - 输出 JSONL 日志（至少记录 tool call 起止与结果）

当你能稳定重放同一任务，并得到一致的“成功/失败类型 + 时间分解”，就可以扩展任务 pack 并开始 cgroup 实验。
