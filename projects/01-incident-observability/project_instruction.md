# Project 01 学生指南（Project Instruction）

## 你将做什么（一句话）
把一次“线上事故”做成可以在 Ubuntu VM 里稳定复现的 **Incident-in-a-Box**，并用 **可观测性证据链**把现象定位到 OS/运行时机制；全班用 **Red/Blue** 形式互相出题与解题。

> 项目主页：`README.md`  
> 评分细则：`RUBRIC.md`

---

## 重要说明：本课最低要求按 MS 档执行

本课程是研究生 OS 课，因此本项目的“完成线”按 **MS 档**定义：

- 每个场景至少 **2 条独立证据 + 1 条反证/排除项（negative control）**
- 每个 mitigation 必须有 **before/after p50/p95/p99**（或至少 p50/p99）以及**机制指标**验证
- 3 个场景必须覆盖三类机制：
  1) 调度/并发（Week 3–4）
  2) cgroup v2 资源边界（Week 5–6）
  3) 存储/写回 tail（Week 8）

---

## 适合谁选

- 适合喜欢“排障/证据/复盘”的同学；对写脚本、看日志、做实验更有兴趣。
- **研究生（默认）**：把“症状→资源→机制”的链路做扎实，并能做可重复的 before/after 验证。
- **博士生**：把“可诊断性”做成工程化体系（evidence contract、反作弊、评分接口、鲁棒性讨论）。

---

## 先修/准备清单（开始前 1–2 天内搞定）

- 环境：Ubuntu（建议 22.04+）VM，能运行 Docker（或 systemd 服务）
- 基础工具：`bash`, `make`, `curl`, `jq`（可选），`pidstat/vmstat/iostat/ss/top`
- 观测信号（VM 友好优先）：
  - PSI：`/proc/pressure/*`
  - `/proc/vmstat`, `/proc/*`
  - cgroup v2：`cpu.stat`, `memory.current`, `memory.stat`, `io.stat`
- 重要约束：很多 VM 里 `perf` 的 **硬件 PMU 事件**不可用；不要把核心结论建立在 cache-miss 这类计数上。

---

## 你需要交付什么（对学生最重要）

你最终交付的是一个“别人拿到就能跑”的事故包。

### 必交交付物
- `run.sh`（或等价命令）：一键完成
  1) 启动目标服务 + 负载
  2) 启动采集（日志/指标）
  3) 触发事故（注入）
  4) 导出结果包（例如 `results/<timestamp>.tar.gz`）
- `REPRODUCE.md`：干净 VM 上的复现步骤与依赖
- `results/`：原始日志 + 解析后的图/表/时间线
- 报告（方法学 + 证据链 + 机制解释 + 缓解验证）与答辩 slides

### Red/Blue 角色说明（班级组织形式由老师定）
- **Red（出题）**：3 个场景（梯度：单因子→双因子→误导性症状），每个都要有 ground truth + evidence contract（2+1）。
- **Blue（解题）**：对每个场景给出时间线、机制级 root cause、至少一个 mitigation 并验证（percentiles + 机制指标）。

---

## 本项目核心难点（你要把力气花在这里）

1) **可诊断的场景设计**：让系统“变坏”很容易，让别人“靠证据”把根因找出来很难。  
2) **机制级 ground truth**：要落到具体机制（throttling/reclaim/writeback/runqueue/锁等），不是“CPU 高/内存满”。  
3) **可复现与抗噪**：VM 抖动、采样误差、依赖漂移会毁掉证据链。

---

## 脚手架（可选但强烈建议用）

- Red team scaffold：`red_team/`
- Blue team scaffold：`blue_team/`

其中包含：场景模板、注入/清理脚本样例、VM 友好的采集与解析脚本。

---

## 前两周怎么开始（建议的最小路径）

- W1：确定服务与指标（p50/p95/p99、error rate），写 1 页设计草案
- W2：把 baseline 跑通：一键启动 + 负载 + 采集 + 结果打包

当你能稳定产出 baseline 的 p99 曲线与对应的 OS 信号（PSI/cgroup/vmstat），你就已经走在正确路线上。
