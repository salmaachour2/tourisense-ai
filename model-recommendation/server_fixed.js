const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

const DEFAULT_GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions';
const DEFAULT_GROQ_MODEL = process.env.GROQ_MODEL || 'openai/gpt-oss-20b';

function normalizeGroqApiUrl(rawUrl) {
  if (!rawUrl) return DEFAULT_GROQ_API_URL;
  const url = String(rawUrl).trim();
  if (!url) return DEFAULT_GROQ_API_URL;
  if (url.includes('api.groq.ai') && url.includes('your-model')) return DEFAULT_GROQ_API_URL;
  return url;
}

function getGroqConfig() {
  const apiUrl = normalizeGroqApiUrl(process.env.GROQ_API_URL);
  process.env.GROQ_API_URL = apiUrl;
  return {
    apiUrl,
    apiKey: process.env.GROQ_API_KEY,
    model: process.env.GROQ_MODEL || DEFAULT_GROQ_MODEL
  };
}

const samplesPath = path.join(__dirname, 'samples.json');
let samples = { samples: [] };
try {
  samples = JSON.parse(fs.readFileSync(samplesPath, 'utf8'));
} catch (e) {
  console.warn('No samples.json found or invalid');
}

function simpleMatch(requestQuery, sampleQuery) {
  const rq = (requestQuery || '').toLowerCase();
  const sq = (sampleQuery || '').toLowerCase();
  const tokens = sq.split(/\W+/).filter(Boolean);
  return tokens.some(t => rq.includes(t));
}

function buildGroqChatPayload(prompt, model, extraOptions = {}) {
  return {
    model: model || DEFAULT_GROQ_MODEL,
    messages: [{ role: 'user', content: prompt }],
    ...extraOptions
  };
}

app.post('/api/recommendations', (req, res) => {
  const { query, governorate, maxResults } = req.body || {};
  const limit = Math.min(12, Math.max(1, maxResults || 5));

  // Try to find matching sample responses
  for (const s of samples.samples || []) {
    if (governorate && s.request && s.request.governorate) {
      if ((s.request.governorate || '').toLowerCase() === (governorate || '').toLowerCase()) {
        return res.json({ results: (s.response && s.response.results || []).slice(0, limit) });
      }
    }
    if (simpleMatch(query, s.request && s.request.query)) {
      return res.json({ results: (s.response && s.response.results || []).slice(0, limit) });
    }
  }

  // fallback: combine all sample results and slice
  const all = [];
  for (const s of samples.samples || []) {
    if (s.response && Array.isArray(s.response.results)) {
      all.push(...s.response.results);
    }
  }
  // remove duplicates by id
  const uniq = [];
  const seen = new Set();
  for (const r of all) {
    if (!r || !r.id) continue;
    if (seen.has(r.id)) continue;
    seen.add(r.id);
    uniq.push(r);
  }

  return res.json({ results: uniq.slice(0, limit) });
});

// helper: get local recommendations (reuse matching logic)
function getLocalRecommendations(query, governorate, limit=5) {
  const limitNum = Math.min(12, Math.max(1, limit || 5));
  // try exact governorate match first
  for (const s of samples.samples || []) {
    if (governorate && s.request && s.request.governorate) {
      if ((s.request.governorate || '').toLowerCase() === (governorate || '').toLowerCase()) {
        return (s.response && s.response.results || []).slice(0, limitNum);
      }
    }
    if (simpleMatch(query, s.request && s.request.query)) {
      return (s.response && s.response.results || []).slice(0, limitNum);
    }
  }
  // fallback: all unique
  const all = [];
  for (const s of samples.samples || []) {
    if (s.response && Array.isArray(s.response.results)) all.push(...s.response.results);
  }
  const uniq = [];
  const seen = new Set();
  for (const r of all) {
    if (!r || !r.id) continue;
    if (seen.has(r.id)) continue;
    seen.add(r.id);
    uniq.push(r);
  }
  return uniq.slice(0, limitNum);
}

// POST /api/ai_with_data
// Body: { query: string, governorate?: string, model?: string, top_k?: number }
app.post('/api/ai_with_data', async (req, res) => {
  const { apiUrl, apiKey, model: defaultModel } = getGroqConfig();
  if (!apiKey) {
    return res.status(500).json({ error: 'GROQ_API_KEY not configured in environment' });
  }

  const { query, governorate, model, top_k } = req.body || {};
  if (!query) return res.status(400).json({ error: 'Missing `query` in request body' });

  const recs = getLocalRecommendations(query, governorate, top_k || 5);
  const dataContext = JSON.stringify(recs, null, 2);
  const userPrompt = `User query: "${query}"` + (governorate ? `, governorate: "${governorate}"` : '');
  const instruction = `You are TouriSense, a friendly and accurate travel assistant specialized in Tunisia. Use ONLY the provided DATA below (do NOT invent facts). Be conversational: if the user greets you (\"hi\", \"hello\", \"salam\"), reply warmly and ask how you can help. If the user requests \"hotels\", \"period\", \"dates\" or similar, honor the constraint and highlight items that match the requested period/season. Provide a short human-friendly paragraph and then return the recommendations in a clear JSON array named RESULTS (objects with id, title, reason, score). Also include a followUps array (2-4 suggested follow-up questions).`;

  const payload = {
    model: model || defaultModel,
    messages: [
      { role: 'system', content: instruction },
      { role: 'user', content: `${userPrompt}\n\nDATA:\n${dataContext}` }
    ]
  };

  try {
    const resp = await axios.post(apiUrl, payload, {
      headers: {
        Authorization: 'Bearer ' + apiKey,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });
    return res.json({ data: resp.data, recommendations: recs });
  } catch (err) {
    console.error('Groq API error', err.response ? err.response.data : err.message);
    return res.json({ data: { error: 'Groq API request failed', details: err.response ? err.response.data : err.message }, recommendations: recs });
  }
});

const DEFAULT_PORT = Number(process.env.PORT) || 3000;
function startServer(port = DEFAULT_PORT) {
  const server = app.listen(port, () => console.log(`Recommendation mock server running on port ${port}`));
  server.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
      const nextPort = port + 1;
      console.warn(`Port ${port} is busy, retrying on ${nextPort}`);
      process.env.PORT = String(nextPort);
      startServer(nextPort);
      return;
    }
    throw error;
  });
}
startServer(DEFAULT_PORT);

// --- GROQ AI proxy -------------------------------------------------
// POST /api/ai
// Body: { prompt: string, model?: string, options?: object }
app.post('/api/ai', async (req, res) => {
  const { apiUrl, apiKey, model: defaultModel } = getGroqConfig();
  if (!apiKey) {
    return res.status(500).json({ error: 'GROQ_API_KEY not configured in environment' });
  }

  const { prompt, model, options } = req.body || {};
  if (!prompt) return res.status(400).json({ error: 'Missing `prompt` in request body' });

  const payload = buildGroqChatPayload(prompt, model || defaultModel, options || {});

  try {
    const resp = await axios.post(apiUrl, payload, {
      headers: {
        Authorization: 'Bearer ' + apiKey,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });
    return res.json(resp.data);
  } catch (err) {
    console.error('Groq API error', err.response ? err.response.data : err.message);
    return res.status(500).json({ error: 'Groq API request failed', details: err.response ? err.response.data : err.message });
  }
});