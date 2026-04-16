# Project 03 学生指南（Project Instruction）

## 你将做什么（一句话）
把 **LLM 推理**当作一个“服务器工作负载”，在 Ubuntu VM（CPU-first）里系统测量 **TTFT / tokens/s / p95/p99**，用 **cgroup/PSI/proc** 等证据解释资源限制如何影响 tail，并验证缓解。

> 项目主页：`README.md`  
> 评分细则：`RUBRIC.md`

---

## 适合谁选

- 适合对“现代工作负载 + OS 机制 + 方法学”感兴趣的同学。
- 你不需要 GPU；但你需要愿意把实验做得可重复、可解释。

---

## 先修/准备清单（开始前 1–2 天内搞定）

- Ubuntu VM（建议 4+ vCPU / 8GB+ RAM；具体写进报告）
- 能跑一个本地推理栈（推荐从 **`llama.cpp`** 开始，原因是 CPU 友好、可控、文档多）
- 基础观测工具：`pidstat`, `vmstat`, `iostat`, `time`
- 证据链信号（VM 友好）：
  - PSI：`/proc/pressure/*`
  - cgroup v2：`cpu.stat`, `memory.current`, `memory.stat`, `io.stat`
  - `/proc/vmstat`、进程 `/proc/<pid>` 相关信息
- 重要约束：VM 里 perf 硬件 PMU 可能不可用；不要依赖硬件 cache events。

---

## 你需要交付什么

### 必交交付物
- 一键脚本 `run.sh`：
  - 运行推理 workload（CLI 或 HTTP 都可，但要定义清楚“请求”）
  - 收集指标与 OS 信号
  - 输出结果到 `results/`
- `collect/`：采集脚本（至少 PSI + cgroup + pidstat/vmstat 之一）
- `results/`：
  - TTFT、tokens/s、p95/p99（至少一组固定 prompt/输出长度）
  - 资源实验（CPU quota 与 memory limit）前后对比图/表
- 报告与答辩 slides

---

## 必做实验（选题时就要确认你能做）

1) **变量 sweep ≥ 3 个维度**（例如：context length、output length、并发、线程数、模型大小/量化等）
2) **cgroup v2 CPU quota**：展示 throttling 如何影响 TTFT/p99/tokens/s，并用 `cpu.stat` 等证据解释
3) **cgroup v2 memory limit**：展示 tight memory 下的 reclaim/fault/OOM 风险，并用 `memory.current/memory.stat` + PSI memory 等解释
4) 至少 **2 个缓解**（建议一个系统层、一个应用层），并做 before/after

---

## 怎么衡量“做到了什么程度”

最终按 `RUBRIC.md` 打分；这里给你一个自检梯度。

### 最低达标（UG 友好）
- 能稳定跑通一个推理栈
- 完成部分 sweep + 完成 CPU quota 或 memory limit 其中一个
- 至少 1 个缓解有效且解释成立

### 标准完成（MS 建议目标）
- 3 个 sweep 都做
- CPU quota + memory limit 都完成
- TTFT/tokens/s/p99 指标齐全，且口径解释清楚
- 两个缓解都有对照（before/after）

### Stretch（PhD/加分）
- 冷启动/热启动拆解（加载模型文件、触页、page cache 等）
- tail 来源解释更完整（排队、上下文切换、抖动、reclaim/IO）并做 ablation

---

## 本项目核心难点（你要把力气花在这里）

1) **指标口径与重复性**：TTFT/tokens/s/p99 的测量边界要讲清楚，不然结论不可比。  
2) **从资源限制到机制证据链**：不能只说“quota 小所以慢”，必须用 cgroup/PSI/proc 信号证明路径。  
3) **解释 tail（p99）而不是只看均值**：p99 往往来自排队与抖动，需要定位关键阶段。

---

## 选题建议（降低踩坑）

- 从最简单的“单机单进程 CLI”开始，再逐步引入并发与服务化。
- 把 prompt 与输出长度固定，先做到稳定 baseline，再做变量 sweep。
- 把采集自动化：每次实验自动记录参数（线程数、并发、模型版本、VM 配置）。

---

## 前两周怎么开始（建议的最小路径）

- W1：选推理栈（llama.cpp）+ 定义请求格式（prompt/输出长度）+ 指标口径
- W2：
  - baseline harness：重复跑 N 次，输出 TTFT/tokens/s/p99
  - 同步把 PSI/cgroup/pidstat 采集串起来

当你能稳定复现“同一配置下的 TTFT/p99 分布”，并能在同一时间线上对齐 OS 信号，你就能开始 quota/memory 实验了。
