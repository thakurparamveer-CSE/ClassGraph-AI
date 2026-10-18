# ClassGraph AI

**Graph-powered, explainable learning assistant for Class+**  
Built for the Graph Hacks: Context for AI Agents hackathon concept.

## Features

- FalkorDB graph context with Cypher queries.
- Student → learning event → topic relationships.
- Topic prerequisite paths and graph evidence.
- Persistent memory stored as `Memory` nodes in FalkorDB.
- Streamlit chat, graph explorer, memory view, and dashboard.
- Ollama local LLM integration.
- Clearly labelled deterministic fallback if Ollama is unavailable.
- Synthetic demo data and basic tests.

## Requirements

- Python 3.10+
- Docker Desktop (or a reachable FalkorDB instance)
- Optional: Ollama and a model such as `llama3.2:3b`

## Quick start — Windows PowerShell

```powershell
cd ClassGraph-AI
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
docker compose up -d
```

Wait until FalkorDB starts. Then optionally install/run Ollama:

```powershell
ollama pull llama3.2:3b
```

Create a local `.env` by copying `.env.example` and adjust settings if needed. The application loads `.env` automatically.

Start the app:

```powershell
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

## First run

1. In the sidebar, click **Initialize / seed demo graph**.
2. Select `demo_student`.
3. Ask: `What should I revise next, and why?`
4. Expand **Graph evidence used**.
5. Open **Memory** and confirm that the interaction was saved.
6. Ask a second question and verify previous memory is included in the context.
7. Open **Graph Explorer** to see the topic links.

## FalkorDB browser

Open http://localhost:3000. The graph service uses port 6379; the browser UI is normally available on port 3000.

## Tests

```powershell
pytest -q
```

The tests cover the deterministic fallback. For a full integration test, start FalkorDB and verify seed repeatability, graph queries, memory persistence, and student isolation manually.

## Troubleshooting

### `docker` is not recognized
Install Docker Desktop, start it, then reopen VS Code/PowerShell.

### FalkorDB connection refused
Run `docker compose ps` and `docker logs classgraph-falkordb`. Ensure port 6379 is available.

### Ollama connection error
Install/start Ollama and run `ollama pull llama3.2:3b`. The app should fall back to graph-based deterministic responses if Ollama cannot be reached.

### Streamlit command not found
Activate `.venv` and run `python -m streamlit run app.py`.

### Graph index already exists
If your FalkorDB version reports an index already exists during initialization, the app may still have created the index successfully. Inspect the logs and graph browser. You can comment out the index lines in `initialize_graph()` if needed.

## Privacy and security

- Demo identities and learning data are synthetic.
- Do not commit `.env`, API keys, passwords, or private student data.
- This is a hackathon prototype, not a production student-record system.
- Do not present generated recommendations as official academic assessments.

## Deliverables to complete before submission

- Public GitHub repository.
- Working demo video.
- README and graph schema.
- Demo proof showing graph evidence and memory across sessions.
- Selected track(s).
- Disclosure of AI coding assistants and tools used.
- Final checks against the official hackathon rules and submission form.

## Current prototype limitations

- Authentication is a demo student selector, not production authentication.
- The graph schema is intentionally small.
- The app does not yet import the existing Class+ Django database.
- Multi-agent coordination and MCP tools are future extensions, not claimed as implemented.
