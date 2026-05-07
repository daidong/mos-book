# PagerUSE

PagerUSE is the Chapter 3 starter app for the oncall-simulation lab. The
required path focuses on memory-pressure-induced tail latency: working-set
growth, reclaim, major faults, and evidence-based exclusion of competing
causes.

## What it does

The app serves a small web UI with:

- an alert panel;
- scenario context;
- a restricted terminal for observation commands.

The terminal is simulated. It does **not** execute commands on the host.
Outputs come either from deterministic scenario fixtures (`LLM_MODE=mock`) or
from an optional LLM backend.

## Quick start

```bash
cd code/ch03-pageruse
npm install
LLM_MODE=mock npm start
```

Open <http://localhost:3000>.

## Main files

```text
code/ch03-pageruse/
├── server.js
├── src/
│   └── core.js
├── scenarios/
├── static/
└── use_checklist.md
```

## Workflow

Use the lab handout in
`src/part1-foundations/ch03-tail-latency/lab-pageruse.md` as the source of
truth. A good submission should preserve:

1. initial hypotheses before command exploration;
2. a RED pass from the service view;
3. a USE pass across CPU, memory, disk, and network;
4. the order of commands issued;
5. two supporting signals and one exclusion check;
6. a memory-pressure mechanism explanation, not just a guess;
7. the Part I synthesis table from the lab handout.

## Notes

- `LLM_MODE=mock` is recommended for deterministic grading.
- The command policy intentionally blocks pipes, redirects, and quotes.
- `use_checklist.md` is the template students should copy and fill in.
