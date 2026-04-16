# Project 02 学生指南（Project Instruction）

## 你将做什么（一句话）
在 Ubuntu VM 里搭一个 **mini-K8s（kind/k3s）** 的 **多跳服务**，让端到端 **p99 tail latency** 在可控条件下变坏，用 **K8s/cgroup + OS 信号**解释“哪一跳、为什么”，并验证缓解。

> 项目主页：`README.md`  
> 评分细则：`RUBRIC.md`

---

## 适合谁选

- 适合对“容器/调度/QoS/cgroup”感兴趣、愿意做端到端实验的同学。
- 如果你只想“把 K8s 跑起来看个 demo”，不适合；本项目更像一个小型性能研究/证据链项目。

---

## 先修/准备清单（开始前 1–2 天内搞定）

- 环境：Ubuntu VM；推荐至少 4 vCPU / 8GB RAM（越大越轻松，但要在报告里写清预算）。
- 工具：Docker（kind 需要），`kubectl`，以及基础观测工具 `pidstat/vmstat/iostat/ss`。
- K8s 选型（建议二选一）：
  - **kind（默认推荐）**：可复现性好，适合课程
  - k3s：如果你更熟也可以
- 重要约束：VM 里 perf 硬件 PMU 往往不可用；不要依赖 cache-miss 这类硬件事件。

---

## 你需要交付什么

### 必交交付物
- 一个 3–4 组件的多跳系统（至少两跳内部依赖）
- 一键脚本 `run.sh`：
  - 部署 baseline
  - 运行 loadgen
  - 收集指标与 OS 信号
  - 能跑干扰实验与缓解实验
- `collect/`：至少能采集
  - cgroup v2 stats（`cpu.stat`, `memory.current`, `memory.stat`, `io.stat`）
  - PSI（`/proc/pressure/*`）
  - 以及至少一种传统工具（`pidstat/vmstat/iostat/ss`）或 K8s events
- `results/`：端到端 p50/p95/p99 + 至少一个 hop 级定位证据（日志或指标）
- 报告与答辩 slides

---

## 必做实验（选题时就要确认你能做）

你必须清楚展示：

1) **requests/limits → cgroup 行为**（例如 CPU quota throttling、memory limit）
2) **QoS class 差异**（Guaranteed/Burstable/BestEffort 至少比较一次）
3) 至少 **2 个不同的 tail latency 放大器**（二选二）：
   - CPU throttling
   - tight memory limit → reclaim/fault/OOM/eviction 相关
   - 写放大/写回/fsync 尖刺
   - `tc netem` 网络损伤（延迟/丢包）

---

## 怎么衡量“做到了什么程度”

最终按 `RUBRIC.md` 打分；这里给你一个自检梯度。

### 最低达标（UG 友好）
- 多跳跑通 + baseline p99 稳定
- 至少 1 个干扰实验能稳定把 p99 拉坏，并给出机制解释 + 一个缓解

### 标准完成（MS 建议目标）
- 2 个干扰实验都完成
- 每个干扰都有 **≥2 个独立信号** 支撑（例如：cpu.stat throttling + PSI cpu；memory.current + PSI memory）
- 两类缓解都完成：
  - 资源/OS/K8s 层（requests/limits/QoS/隔离等）
  - 应用层（timeout/backoff/admission control/cache 等）

### Stretch（PhD/加分）
- 能明确说明关键路径：端到端 p99 是哪一跳拖尾，为什么是它
- 做参数 sweep（例如不同 limit 下的 p99 曲线），而不只是单点对比

---

## 本项目核心难点（你要把力气花在这里）

1) **端到端 p99 的 hop 级归因**：证明“哪一跳在拖尾”比把 p99 拉坏更难。  
2) **K8s 抽象落到内核机制**：requests/limits/QoS 最终如何变成 cgroup throttling/OOM/reclaim。  
3) **方法学控噪**：VM + kind/k3s 抖动大，必须做重复、warmup、固定负载口径。

---

## 选题建议（降低踩坑）

- 多跳服务建议从“最小可测系统”开始：gateway → service-a → service-b，再加一个 writer/db。
- 把“可观测性”当成第一等公民：每一跳至少要能打出带时间戳的 latency 日志，或导出简单直方图。
- 把干扰做得“机制清晰”：CPU quota 与 memory limit 通常最干净。

---

## 前两周怎么开始（建议的最小路径）

- W1：选 kind/k3s + 画出服务拓扑 + 定义 p99 指标口径
- W2：
  - baseline 部署与 loadgen 稳定
  - 写下你将如何采集：端到端 + 至少一个 hop + OS 信号（PSI/cgroup）

当你能在 `results/` 里稳定产出 baseline p99 曲线，并能读到 pod 的 `cpu.stat/memory.current`，你就可以开始做干扰了。
