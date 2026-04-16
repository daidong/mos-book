import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

import {
  listScenarioIds,
  loadScenario,
  validateCommand,
  buildLlmMessages,
  callLlm,
  safeNowIso,
} from './src/core.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

app.use(express.json({ limit: '256kb' }));
app.use('/static', express.static(path.join(__dirname, 'static')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

app.get('/api/health', (req, res) => {
  res.json({ ok: true, ts: safeNowIso() });
});

app.get('/api/scenarios', async (req, res) => {
  const ids = await listScenarioIds(path.join(__dirname, 'scenarios'));
  res.json({ scenarios: ids });
});

app.get('/api/scenario/:id', async (req, res) => {
  const scenario = await loadScenario(path.join(__dirname, 'scenarios'), req.params.id);
  res.json({ scenario });
});

app.post('/api/command', async (req, res) => {
  const { scenarioId, input } = req.body || {};

  if (typeof scenarioId !== 'string' || typeof input !== 'string') {
    return res.status(400).json({ error: 'scenarioId and input are required strings' });
  }

  const scenario = await loadScenario(path.join(__dirname, 'scenarios'), scenarioId);

  const trimmed = input.trim();
  const v = validateCommand(trimmed, scenario.terminal?.policy);
  if (!v.ok) {
    return res.status(400).json({ error: v.error, help: scenario.terminal?.help || null });
  }

  const messages = buildLlmMessages({ scenario, command: trimmed });
  const result = await callLlm({ scenario, messages });

  res.json({
    ok: true,
    command: trimmed,
    output: result.output,
    model: result.model,
    mode: result.mode,
  });
});

const port = process.env.PORT ? Number(process.env.PORT) : 3000;
app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`PagerUSE server listening on http://localhost:${port}`);
});
