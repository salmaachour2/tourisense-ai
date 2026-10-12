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

function buildGroqChatPayload(prompt, model, extraOptions = {}) {
  return {
    model: model || DEFAULT_GROQ_MODEL,
    messages: [{ role: 'user', content: prompt }],
    ...extraOptions
  };
}

function simpleMatch(requestQuery, sampleQuery) {
  const rq = (requestQuery || '').toLowerCase();
  const sq = (sampleQuery || '').toLowerCase();
  const tokens = sq.split(/\W+/).filter(Boolean);
  return tokens.some(t => rq.includes(t));
}

function extractPhones(text) {
  if (!text) return [];
  const matches = [...text.matchAll(/(?:\+|00)?(?:216|\d{2,4})[\s.-]?(?:\d{2,3})[\s.-]?(?:\d{2,3})[\s.-]?(?:\d{2,3})/g)];
  return matches.map(m => m[0].replace(/\s+/g, '').replace(/[-.]/g, ' ')).slice(0, 3);
}

function extractUrls(text) {
  if (!text) return [];
  const matches = [...text.matchAll(/https?:\/\/[^\s)\]>"']+/gi)];
  return [...new Set(matches.map(m => m[0]))].slice(0, 5);
}

function stripHtml(text) {
  return String(text || '').replace(/<[^>]*>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
}

function decodeHtmlEntity(text) {
  return String(text || '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/&apos;/g, "'");
}

async function webSearch(query) {
  const term = String(query || '').trim();
  if (!term) return [];

  try {
    const ddgUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(term)}`;
    const resp = await axios.get(ddgUrl, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      timeout: 15000
    });

    const html = resp.data || '';
    const matches = [...html.matchAll(/<a rel="nofollow" class="result-link" href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi)];
    const results = [];

    for (const match of matches) {
      const title = decodeHtmlEntity(stripHtml(match[2] || ''));
      const url = decodeHtmlEntity(match[1] || '').trim();
      if (!title || !url) continue;
      results.push({ title, url });
      if (results.length >= 5) break;
    }

    return results;
  } catch (e) {
    return [];
  }
}

async function fetchPublicPlaceInfo(placeName) {
  const name = String(placeName || '').trim();
  if (!name) return null;

  const result = {
    title: name,
    address: null,
    website: null,
    phone: null,
    imageUrl: null,
    sourceUrl: null,
    note: 'Public enrichment lookup'
  };

  try {
    const wikiUrl = `https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts|pageimages|info&redirects=1&exintro=1&explaintext=1&piprop=original&titles=${encodeURIComponent(name + ' Tunisia')}`;
    const wikiResp = await axios.get(wikiUrl, { timeout: 15000 });
    const pages = wikiResp.data && wikiResp.data.query && wikiResp.data.query.pages ? Object.values(wikiResp.data.query.pages) : [];
    const page = pages[0];
    if (page) {
      result.sourceUrl = page.fullurl || null;
      if (page.original && page.original.source) result.imageUrl = page.original.source;
      const summary = (page.extract || '').trim();
      if (summary) result.note = summary.slice(0, 220);
    }
  } catch (e) {
    // Public lookup is optional; ignore failures.
  }

  try {
    const geoUrl = `https://nominatim.openstreetmap.org/search?format=jsonv2&q=${encodeURIComponent(`${name} Tunisia`)}`;
    const geoResp = await axios.get(geoUrl, {
      headers: { 'User-Agent': 'TouriSense/1.0' },
      timeout: 15000
    });
    const first = Array.isArray(geoResp.data) ? geoResp.data[0] : null;
    if (first && first.display_name) {
      result.address = first.display_name;
      result.sourceUrl = result.sourceUrl || `https://www.openstreetmap.org/${first.osm_type}/${first.osm_id}`;
    }
  } catch (e) {
    // Ignore geocoding failures.
  }

  try {
    const ddgQuery = encodeURIComponent(`${name} Tunisia official website phone`);
    const ddgUrl = `https://html.duckduckgo.com/html/?q=${ddgQuery}`;
    const ddgResp = await axios.get(ddgUrl, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      timeout: 15000
    });
    const html = ddgResp.data || '';
    const urls = extractUrls(html);
    if (urls.length) result.website = urls.find(u => !u.includes('duckduckgo.com')) || urls[0];
    const phoneMatches = extractPhones(html);
    if (phoneMatches.length) result.phone = phoneMatches[0];
  } catch (e) {
    // Ignore search failures.
  }

  if (!result.imageUrl) {
    result.imageUrl = 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80';
  }

  return result;
}

async function enrichForAdditionalInfo(query, recs) {
  const q = (query || '').toLowerCase();
  const wantsExtra = /(phone|telephone|contact|website|site web|email|adresse|address|opening|hours|ouverture|photo|picture|image|map|location|booking|reservation|official|price|prix|budget|cost|tarif)/i.test(q);
  if (!wantsExtra) return { publicResults: null, webResults: [] };

  const publicResults = [];
  const targetPlaces = Array.isArray(recs) && recs.length ? recs.slice(0, 3) : [];

  for (const rec of targetPlaces) {
    const item = await fetchPublicPlaceInfo(rec.title || rec.id);
    if (item) publicResults.push(item);
  }

  const webResults = await webSearch(q.length > 120 ? q.slice(0, 120) : q);
  const broaderQuery = Array.isArray(recs) && recs.length ? `${q} ${recs.map(r => r.title || r.id).join(' ')}` : q;
  const extraWebResults = webResults.length ? webResults : await webSearch(broaderQuery);

  return {
    publicResults: publicResults.length ? publicResults : null,
    webResults: extraWebResults.length ? extraWebResults : []
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

  const { publicResults, webResults } = await enrichForAdditionalInfo(query, recs);

  const dataContext = JSON.stringify(recs, null, 2);
  const userPrompt = `User query: "${query}"` + (governorate ? `, governorate: "${governorate}"` : '');
  const instruction = `You are TouriSense, a friendly and accurate travel assistant specialized in Tunisia. Use the local DATA as a starting point, but do not let it limit the answer. If the user asks for details not present in the local dataset (phone numbers, websites, addresses, opening hours, photos, official links, price, budget, dates, or general tourism facts), search the WEB_SEARCH_RESULTS and PUBLIC_ENRICHMENT blocks below and answer using verified public information when available. Do not invent facts or fabricate phone numbers, prices, or links. If no verified public evidence exists, say clearly that the information is not available instead of guessing. Be conversational: if the user greets you ("hi", "hello", "salam"), reply warmly and ask how you can help. If the user requests "hotels", "period", "dates", "price", "budget", "cost", "tarif" or similar, answer using available data and include price estimates only when supported by the DATA or WEB_SEARCH_RESULTS. Include any fields you can verify: estimatedCostPerDay, budgetLevel, imageUrl, galleryUrls, governorate, description, phone, website, address, sourceUrl. Provide a short human-friendly paragraph and then return the recommendations in a clear JSON array named RESULTS (objects with id, title, reason, score, description, governorate, estimatedCostPerDay, budgetLevel, imageUrl, galleryUrls). Also include a followUps array (2-4 suggested follow-up questions).`;
  const publicContext = publicResults ? `\n\nPUBLIC_ENRICHMENT:\n${JSON.stringify(publicResults, null, 2)}` : '';
  const webContext = webResults.length ? `\n\nWEB_SEARCH_RESULTS:\n${JSON.stringify(webResults, null, 2)}` : '';
  const prompt = `${instruction}\n\nDATA:\n${dataContext}${publicContext}${webContext}\n\n${userPrompt}`;

  const payload = {
    model: model || defaultModel,
    messages: [
      { role: 'system', content: instruction },
      { role: 'user', content: `${userPrompt}\n\nDATA:\n${dataContext}${publicContext}${webContext}` }
    ]
  };

  try {
    const resp = await axios.post(apiUrl, payload, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });
    return res.json({ data: resp.data, recommendations: recs, enrichment: publicResults || null, webResults: webResults || [] });
  } catch (err) {
    console.error('Groq API error', err.response ? err.response.data : err.message);
    return res.json({ data: { error: 'Groq API request failed', details: err.response ? err.response.data : err.message }, recommendations: recs, enrichment: publicResults || null, webResults: webResults || [] });
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
        Authorization: `Bearer ${apiKey}`,
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
