# OperaDemo - RAG Document Intelligence

**A proof-of-concept showing that small LLMs (≤7B parameters), paired with a well-engineered retrieval pipeline, can answer financial document questions accurately - without sending data to large cloud models.**

Stack: Blazor .NET 9 · FastAPI · Mistral-7B via HuggingFace · Hybrid BM25 + dense retrieval

---

## What it does and why I built it

Financial services firms face a real tension with LLM adoption: the most capable models (GPT-4, Claude Opus) require sending data to external cloud providers, which conflicts with data sovereignty requirements under GDPR, MiFID II, and local regulations like JFSC. At the same time, on-premise deployments of large models are expensive and slow.

This project tests the hypothesis that **the intelligence is in the retrieval architecture, not the model size**. If you give a 7B model the right 400 words of context, it doesn't need to have memorised everything - it just needs to read and synthesise.

The application lets you upload financial PDFs (fund prospectuses, annual reports, compliance documents) and ask natural language questions. It retrieves the most relevant chunks using hybrid search, passes them as context to Mistral-7B, then validates the answer before returning it with confidence scores and source citations.

---

## Design decisions

**Hybrid retrieval (BM25 + dense embeddings)**
Financial documents contain both precise terminology ("redemption fee", specific percentages) and semantic concepts ("early exit costs", "liquidity terms"). BM25 handles exact keyword matching well; dense embeddings handle semantic similarity. Combined with equal weighting, they cover both cases better than either alone.

**Multi-stage validation**
Small models hallucinate more than large ones. Rather than hiding this, the pipeline explicitly checks: retrieval quality (minimum similarity threshold), source alignment (answer tokens appear in retrieved chunks), hallucination patterns (contradictory statements, unsupported specifics), and numerical accuracy (every number in the answer must appear verbatim in the source). Each query returns a confidence level and warnings - making the system honest about its limitations rather than confidently wrong.

**Append-only document indexing**
On startup the pipeline indexes the sample documents. Uploaded documents are appended to the existing index rather than replacing it, so the pool of retrievable knowledge grows with each upload. Deduplication by source prevents double-indexing the same file.

**Blazor + Python split**
Python has the best ecosystem for RAG and LLM work. Blazor lets me demonstrate .NET skills and produces a cleaner, more production-representative frontend than a Python-served HTML page. The two communicate over a typed HTTP API, which mirrors real enterprise patterns.

**HuggingFace router API**
For a proof-of-concept running in a Codespace, a local model isn't practical. The HuggingFace router API lets Mistral-7B run remotely while keeping the architecture identical to what a local Ollama deployment would look like - the provider is swappable with one config change.

---

## How to run it

### GitHub Codespace (recommended)

1. Fork or upload this repo to GitHub
2. Click **Code → Codespaces → Create codespace**
3. Wait ~2-3 minutes for automatic setup
4. In the terminal:

```bash
cp .env.example .env
# Edit .env and add your HuggingFace token
# Get one free at https://huggingface.co/settings/tokens
# Accept the model license at https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2

bash start.sh
```

5. Open the **Ports** tab - click the link for port 5000 (Blazor UI) or 8000 (API dashboard)

### Local (devcontainer)

**Prerequisites:** Docker Desktop, VS Code with Dev Containers extension

1. Clone the repo and open the folder in VS Code
2. When prompted, click **Reopen in Container** (or `Ctrl+Shift+P` → "Reopen in Container")
3. Once the container is ready, run the same steps as above in the integrated terminal

The devcontainer installs all Python and .NET 9 dependencies automatically.

### Ports

| Port | Service |
|------|---------|
| 5000 | Blazor frontend |
| 8000 | Python API + status dashboard |
| 8000/docs | Swagger UI |

---

## Next steps

**Replace HuggingFace with local Ollama**
For a production deployment at a firm with data sovereignty requirements, the HuggingFace API would be replaced with Ollama running on-premise. The provider abstraction in `src/llm/providers.py` makes this a single config change - add an `OllamaProvider` class and point `LLM_PROVIDER` at it.

**Fine-tune on domain documents**
The current setup uses a general-purpose Mistral-7B checkpoint. Fine-tuning on firm-specific fund documents and Q&A pairs would meaningfully improve accuracy for that specific vocabulary and document structure. This can be done on a single GPU at relatively low cost.

**Evaluation framework**
Right now quality is assessed manually. A proper eval set - a benchmark of questions with known correct answers drawn from the sample documents - would let you measure retrieval recall, answer accuracy, and hallucination rate automatically, and compare the effect of changing chunk size, top-k, or model.

**Audit trail**
In a regulated environment every query, retrieved context, answer, and confidence score should be logged with a timestamp and user ID. This is straightforward to add to the `/query` endpoint and would be a prerequisite for any compliance use case.

**Role-based document access**
Currently all uploaded documents are visible to all queries. In practice you'd want document-level permissions - an analyst seeing only their funds, a compliance officer seeing everything, a client seeing only their own portfolio documents.

---

## Project structure

```
OperaDemo/
├── main.py                        # FastAPI app and API endpoints
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template (copy to .env)
├── start.sh / start-backend.sh / start-frontend.sh
│
├── src/
│   ├── llm/
│   │   ├── base_provider.py       # LLM provider interface
│   │   └── providers.py           # HuggingFace implementation
│   ├── rag/
│   │   ├── document_processor.py  # PDF chunking
│   │   ├── retriever.py           # Hybrid BM25 + dense search
│   │   └── pipeline.py            # RAG orchestration
│   └── validation/
│       └── validator.py           # Multi-stage answer validation
│
├── OperaDemoWeb/                  # Blazor .NET 9 frontend
│   ├── Components/Pages/Home.razor
│   ├── Services/ApiService.cs
│   └── Models/
│
├── sample_documents/              # Pre-loaded fund PDFs
├── templates/api-dashboard.html   # API status page (port 8000)
└── .devcontainer/                 # Codespace/devcontainer config
```
