# Project 02 评分细则（Rubric）— Mini-K8s 多跳服务：QoS/Cgroups 与端到端 Tail Latency

目标不是“把 K8s 跑起来”，而是做一个 **端到端 tail latency 的机制解释 + 可验证缓解**。

> 课程定位：研究生 OS 课。  
> **最低要求按 MS 档执行**；低于 MS 档的产出属于“未达基线”。

---

## 0. 分档（以 MS 为基线）

### UG 档（低于基线，仅供参考）
- 多跳能跑，但证据不足；
- 主要靠单一信号或“经验猜测”；
- 缓解缺少干净的 before/after。

### MS 档（基线 / 标准完成）
- 至少 **2 个干扰实验**都完成，并能把 p99 归因到关键路径上的某一 hop/资源/机制；
- 每个干扰与缓解都必须满足“证据三件套”（**硬门槛**，缺一项视为该实验未完成）：
  1) **两条独立证据（跨层次观测）**：至少跨两层（应用/用户态指标 + OS/资源控制/K8s 控制面指标）。
     - 例：应用 latency 日志/直方图 + cgroup/PSI/iostat/pidstat/kubectl events 之一
  2) **一条排除性对照（控制变量/反例）**：明确说明“为什么不是某个常见替代解释”。
     - 例：`iostat` 稳定→排除 IO；`cpu.stat` 无 throttling→排除 quota
  3) **before/after 的分位数 + 机制指标**：p50/p95/p99（或至少 p50/p99）+ 一个机制指标随之变化（PSI、cpu.stat throttled、iostat await、OOM/eviction 事件等）

### PhD 档（研究型/加分）
- 有清晰的“关键路径”建模（哪一跳主导 p99、为何）；
- 处理方法学问题（抖动、重试放大、测量偏差）；
- 做 ablation（逐项关闭干扰/重试/限流）。

---

## 1. 必交（否则上限封顶）

- 多跳：至少 **两跳内部依赖**（不算 loadgen）。
- 指标：p50/p95/p99 + throughput + error rate（至少记录）。
- K8s/cgroup：必须包含 **requests/limits → cgroup 行为** 与 **QoS class** 的清晰实验。
- 缓解：两类缓解都要有：
  1) **资源/OS/K8s 层**（requests/limits、QoS、隔离、priority 等）
  2) **应用层**（timeout、backoff、batch、cache、admission control 等）
- 环境记录：`uname -r`、VM 配置（vCPU/RAM）、kind/k3s 版本。

---

## 2. 打分方式（100 分制建议）

### A. 系统搭建与可复现性（25）
-（10）一条命令（或 3 步以内）启动集群 + 部署 + 产生 baseline 结果
-（8）资源预算明确：VM 配置、节点数、镜像大小控制（laptop-friendly）
-（7）复现脚本与清理脚本（避免残留资源影响结果）

### B. 测量方法学与指标口径（20）
-（8）loadgen 可控、稳定（warmup、重复次数、固定并发/速率）
-（7）延迟统计口径正确（p99 的窗口、采样数、直方图/日志）
-（5）噪声讨论：VM 抖动、GC/编译、缓存冷热等

### C. 机制解释与证据链（35）
至少做 **2 个干扰实验**，每个按 17.5 分计：
-（6）能把“端到端 p99 坏”归因到某一 hop/资源（关键路径定位）
-（6）能落到机制（quota throttling→runqueue delay；reclaim→faults；writeback→IO 等待；netem→重传/排队）
-（5）两条独立证据（跨层次观测：应用指标 + OS/资源控制/K8s 指标）
-（0.5）一条排除性对照（控制变量/反例）写清楚

> 说明：证据三件套是本课程的 MS 基线要求。
> 若某个干扰实验缺少“排除性对照”或缺少“机制指标随之变化”，该实验最多按“定位到资源但机制未闭环”给分。

### D. 缓解与验证（20）
-（10）资源/OS/K8s 层缓解：before/after 分位数 + 机制指标 + 解释
-（10）应用层缓解：同上（例如 timeout/backoff 避免重试风暴、admission control 控制队列长度等）

**加分（最多 +10）**：
- +5：做了参数 sweep 并画出“limit/requests vs p99”的曲线（而非单点对比）
- +5：把关键路径用简化队列模型解释（Little’s Law/排队论直觉）并与观测一致

---

## 3. 本项目核心难点

1) **端到端与 hop 级归因**：p99 是系统级现象，难点是证明“哪一跳在拖尾”。
2) **K8s 抽象与内核机制打通**：能说清 requests/limits/QoS 最终如何落到 cgroup 行为（throttling/OOM/eviction）。
3) **方法学与噪声控制**：在 VM 的 kind/k3s 上做严谨实验比“跑一个 demo”难。

---

## 4. 交付物清单

- `deploy/`：清晰的 manifests（或 helm/kustomize）
- `run.sh`：一键 baseline + 干扰 + 缓解
- `collect/`：至少包含 cgroup/PSI/K8s event 的采集
- `results/`：原始日志 + 图/表（端到端 p99 + 至少一个 hop 级证据）
- 报告与 slides
