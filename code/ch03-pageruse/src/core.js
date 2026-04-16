import fs from 'fs/promises';
import path from 'path';

export function safeNowIso() {
  return new Date().toISOString();
}

export async function listScenarioIds(scenariosDir) {
  const entries = await fs.readdir(scenariosDir, { withFileTypes: true });
  return entries
    .filter((e) => e.isFile() && e.name.endsWith('.json'))
    .map((e) => e.name.replace(/\.json$/, ''))
    .sort();
}

export async function loadScenario(scenariosDir, id) {
  const p = path.join(scenariosDir, `${id}.json`);
  const raw = await fs.readFile(p, 'utf-8');
  const scenario = JSON.parse(raw);

  if (!scenario || typeof scenario !== 'object') {
    throw new Error(`invalid scenario JSON: ${id}`);
  }
  if (!scenario.id) scenario.id = id;
  return scenario;
}

/**
 * Command validation strategy:
 * - strict allowlist of command "stems" (e.g., top, free, vmstat)
 * - no pipes, redirects, subshells, backticks, $(), &&, ||
 * - no quotes (to avoid injection into prompts and to keep parsing simple)
 * - a max length limit
 *
 * This lab is about reasoning, not shell syntax.
 */
export function validateCommand(input, policy = {}) {
  const maxLen = policy.maxLen ?? 120;
  if (input.length === 0) return { ok: false, error: 'empty command' };
  if (input.length > maxLen) return { ok: false, error: `command too long (>${maxLen})` };

  // block common shell metacharacters
  const forbidden = /[|&;<>`\n\r]|\$\(|\$\{|\}\)|\\/;
  if (forbidden.test(input)) {
    return { ok: false, error: 'unsupported shell features: pipes/redirection/subshells are not allowed' };
  }

  // disallow quotes to reduce prompt trickery
  if (/['"]/g.test(input)) {
    return { ok: false, error: 'quotes are not allowed in this lab terminal' };
  }

  // collapse whitespace
  const normalized = input.trim().replace(/\s+/g, ' ');

  const tokens = normalized.split(' ');
  const stem = tokens[0];

  const allow = policy.allow || defaultAllowlist();
  if (!allow.includes(stem)) {
    return { ok: false, error: `command not allowed: ${stem}` };
  }

  // optional per-command regex checks
  const rules = policy.rules || {};
  const rule = rules[stem];
  if (rule && rule.regex) {
    const re = new RegExp(rule.regex);
    if (!re.test(normalized)) {
      return { ok: false, error: rule.error || `command arguments rejected by policy for ${stem}` };
    }
  }

  return { ok: true, normalized };
}

export function defaultAllowlist() {
  return [
    'help',
    'date',
    'uname',
    'uptime',
    'whoami',

    // CPU/memory basics
    'top',
    'free',
    'vmstat',
    'mpstat',

    // /proc snapshots
    'cat',
    'grep',

    // common oncall commands
    'dmesg',
    'journalctl',
    'ss',
    'netstat',
    'ps',

    // tracing-style summary commands (fake)
    'perf',
    'sar',

    // cgroup
    'systemd-cgls',
    'systemd-cgtop',
  ];
}

export function buildLlmMessages({ scenario, command }) {
  const system = {
    role: 'system',
    content: [
      'You are a Linux host. You are returning the output of commands typed by a student in a training lab.',
      'The terminal is simulated. Do NOT claim to actually execute commands. Instead, generate realistic command output.',
      'You MUST remain consistent with the given scenario state and ground-truth facts.',
      'If the command is unknown or unsupported, reply with a short error like a real shell would.',
      'Output format rules:',
      '- Return ONLY the command output (no explanations).',
      '- Use fixed-width formatting where appropriate.',
      '- Keep outputs short but realistic (avoid huge dumps).',
    ].join('\n'),
  };

  const context = {
    role: 'user',
    content: JSON.stringify(
      {
        scenario: {
          id: scenario.id,
          title: scenario.title,
          narrative: scenario.narrative,
          now: scenario.now,
          host: scenario.host,
          alerts: scenario.alerts,
          groundTruth: scenario.groundTruth,
          terminal: {
            persona: scenario.terminal?.persona,
            filesystem: scenario.terminal?.filesystem,
            policy: scenario.terminal?.policy,
            help: scenario.terminal?.help,
          },
          commandLibrary: scenario.commandLibrary,
        },
        command,
      },
      null,
      2
    ),
  };

  return [system, context];
}

export async function callLlm({ scenario, messages }) {
  const mode = (process.env.LLM_MODE || scenario.llm?.mode || 'openai').toLowerCase();

  if (mode === 'mock') {
    const output = mockOutput({ scenario, command: JSON.parse(messages[1].content).command });
    return { output, model: 'mock', mode: 'mock' };
  }

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return {
      output:
        'error: LLM not configured. Set OPENAI_API_KEY or run with LLM_MODE=mock\n',
      model: null,
      mode,
    };
  }

  const model = process.env.OPENAI_MODEL || scenario.llm?.model || 'gpt-4o-mini';
  const baseUrl = process.env.OPENAI_BASE_URL || scenario.llm?.baseUrl || 'https://api.openai.com/v1';

  const resp = await fetch(`${baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages,
      temperature: scenario.llm?.temperature ?? 0.2,
    }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    return {
      output: `error: LLM request failed (${resp.status})\n${text}\n`,
      model,
      mode,
    };
  }

  const data = await resp.json();
  const content = data?.choices?.[0]?.message?.content;
  return { output: (content || '').trimEnd() + '\n', model, mode };
}

function mockOutput({ scenario, command }) {
  // deterministic, scenario-aware minimal outputs for offline testing
  const lib = scenario.commandLibrary || {};
  if (lib[command]) return lib[command];

  const stem = command.split(/\s+/)[0];

  if (stem === 'help') {
    return (scenario.terminal?.help || 'No help available.\n') + '\n';
  }

  // very small set of generic fallbacks
  if (stem === 'date') {
    return `${scenario.now || new Date().toUTCString()}\n`;
  }

  return `bash: ${stem}: command output not available in mock mode\n`;
}
