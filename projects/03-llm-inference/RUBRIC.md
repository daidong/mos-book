# Project 03 评分细则（Rubric）— LLM Inference 服务器性能剖析（CPU-first）

本项目把 LLM 推理当作“服务器工作负载”，核心产出是：**指标 → 观测 → OS 机制 → 缓解验证**。

> 课程定位：研究生 OS 课。  
> **最低要求按 MS 档执行**；低于 MS 档的产出属于“未达基线”。

---

## 0. 分档（以 MS 为基线）

### UG 档（低于基线，仅供参考）
- 能跑通但证据链不完整；
- quota/memory 实验做不全或解释停留在“资源高/低”。

### MS 档（基线 / 标准完成）
- 3 个变量 sweep 都做（至少 3 个变量维度）；
- CPU quota + memory limit 都完成；
- TTFT / tokens/s / p99 三个指标齐全；
- 每个关键实验都满足“证据三件套”（**硬门槛**，缺一项视为该实验未完成）：
  1) **两条独立证据（跨层次观测）**：至少跨两层（应用/用户态指标 + OS/资源控制指标）。
     - 例：TTFT/p99/tokens/s + cgroup/PSI/pidstat/vmstat/iostat
  2) **一条排除性对照（控制变量/反例）**：明确说明“为什么不是某个常见替代解释”。
     - 例：`iostat` 稳定→排除 IO；`cpu.stat` 无 throttling→排除 quota；PSI memory 低→排除 reclaim
  3) **before/after 分位数 + 机制指标**：p50/p95/p99（或至少 p50/p99）+ 一个机制指标随之变化（throttled_usec、PSI、major faults 等）
- 至少 2 个缓解都有 before/after。

### PhD 档（研究型/加分）
- 冷启动/热启动的机制拆解（文件 IO、page cache、亲和性等）；
- 解释 tail 的来源（排队、并发、上下文切换、抖动）；
- 做 ablation（线程数/并发/kv-cache 相关设置）并形成可复用方法学。

---

## 1. 必交（否则上限封顶）

- 工作负载：明确“请求”定义（CLI or HTTP），固定 prompt + 输出长度（或说明随机性控制）。
- 指标：至少 **TTFT、tokens/s、p95/p99 latency**。
- 资源实验：必须包含
  1) **cgroup v2 CPU quota**；
  2) **cgroup v2 memory limit**。
- 证据：必须使用 VM 友好信号（PSI/cgroup/proc/pidstat 等），不能依赖 perf PMU cache counters。
- 环境记录：`uname -r`、VM 配置、模型版本/量化、线程数。

---

## 2. 打分方式（100 分制建议）

### A. 可复现性与基线稳定性（25）
-（10）一键跑：能生成 baseline 结果（含指标与日志）
-（8）重复性：至少 N=5（或说明 N）并报告方差/箱线图/置信区间之一
-（7）环境记录：模型版本/量化/线程数/VM 配置写清楚

### B. 测量方法学与指标口径（20）
-（8）TTFT/tokens/s 的测量口径可解释（日志时间戳、统计方式）
-（7）并发与排队处理清楚（client 并发、server 队列/线程池）
-（5）噪声来源讨论（缓存冷热、首次加载、CPU 频率、VM 抖动）

### C. 资源实验与机制解释（35）
-（18）CPU quota 实验：
  - 指标变化（TTFT/p99/tokens/s）
  - 两条独立证据（跨层次观测；例如：应用指标 + `cpu.stat` throttled 或 PSI cpu/pidstat）
  - 一条排除性对照（例如：`iostat` 稳定→排除 IO）
  - 机制解释（throttling→排队/可运行等待/关键阶段变长）
-（17）memory limit 实验：
  - 指标变化
  - 两条独立证据（跨层次观测；例如：应用指标 + memory.current/memory.stat + PSI memory 或 major faults 近似）
  - 一条排除性对照（例如：`cpu.stat` 无 throttling→排除 quota）
  - 机制解释（reclaim/fault/可能 OOM）

### D. 缓解与验证（20）
-（10）系统层缓解（亲和性/线程数/预热/避免 swap/cgroup 调整等）
-（10）应用层缓解（并发控制、admission control、prompt 约束、缓存/批处理若可行）

缓解验证必须包含：before/after 分位数 + 一个机制指标随之变化。

**加分（最多 +10）**：
- +5：把冷启动拆成“加载模型文件/触页/编译 JIT(若有)”等阶段，并给出时间占比
- +5：用简单模型解释 tokens/s 上限（CPU 利用率、线程扩展性、上下文切换开销）并与数据吻合

---

## 3. 本项目核心难点

1) **指标口径与可重复性**：LLM 推理有大量非确定性因素（缓存、线程、并发队列），难点是把实验变成“可对比”。
2) **从资源限制到机制**：CPU quota/memory limit 不是“变慢”的同义词，必须用 cgroup/PSI/proc 信号证明路径。
3) **tail 的来源解释**：p99 往往来自排队与抖动（throttling、reclaim、IO），难点是把 tail 归因到关键阶段。

---

## 4. 交付物清单

- `server/`：如何运行推理服务/CLI
- `bench/`：负载生成器（并发/速率可控）
- `collect/`：PSI + cgroup + pidstat/vmstat 等采集
- `experiments/`：变量 sweep 配置
- `results/`：原始日志 + 解析图/表
- 报告与 slides
