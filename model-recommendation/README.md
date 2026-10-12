# TouriSense model-recommendation prototype

Instructions to build embeddings and run the recommendation API.

Run the commands below from this `model-recommendation` directory.

1. Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Extract catalog from `samples.json` (optional, already included):

```bash
python ml/extract_catalog.py
```

3. Build embeddings and FAISS index:

```bash
python ml/build_embeddings.py
```

4. Run the API:

```bash
uvicorn app:app --reload --port 8000
```

5. Example request (curl):

```bash
curl -X POST http://localhost:8000/recommend -H "Content-Type: application/json" -d '{"query":"plage tranquille pour famille","lang":"fr","top_k":5}'
```

6. Groq AI agent (Node proxy)

Set these environment variables before starting the Node server (`server.js`):

```powershell
setx GROQ_API_URL "https://api.groq.com/openai/v1/chat/completions"
setx GROQ_API_KEY "your_groq_api_key_here"
setx GROQ_MODEL "openai/gpt-oss-20b"
```

Then install Node deps and start the server:

```bash
npm install
npm start
```

Example request to the Groq proxy (from the chatbot/server):

```bash
curl -X POST http://localhost:3000/api/ai \
	-H "Content-Type: application/json" \
	-d '{"prompt":"Recommande 3 destinations balnéaires en Tunisie pour une famille","model":"openai/gpt-oss-20b"}'
```

Example request that augments the prompt with local data (retrieval-augmented):

```bash
curl -X POST http://localhost:3000/api/ai_with_data \
	-H "Content-Type: application/json" \
	-d '{"query":"plage tranquille pour famille","governorate":"Nabeul","model":"openai/gpt-oss-20b","top_k":5}'
```

The `/api/ai_with_data` endpoint will fetch the top local recommendations from `samples.json` (or your catalog), include them as JSON context in the prompt, call the Groq model, and return both the model output and the recommendations used.

Note: `server.js` expects `GROQ_API_URL` and `GROQ_API_KEY` to be set. The proxy forwards the `prompt` to the configured Groq endpoint and returns the model output.

Next steps: enrich `data/catalog.json` with your full destinations dataset, add more training `samples.json` entries in French/Arabic/English, then rebuild embeddings.
Recommendation model for TouriSense.ai (root)
------------------------------------------------

This folder contains the specification, prompts and sample responses for the recommendation model that will power the "Grand public" chatbot. Files are in French and targeted to Tunisia.

Files:
- `spec.md` — API contract (input / output / HTTP example)
- `prompts.md` — system and user prompt templates + few examples
- `samples.json` — example requests/responses for Tunisia

Place this folder at the project root so backend engineers and data scientists can use it as the canonical model spec.
