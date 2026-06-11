# Fix My Vibe × Azure AI Search KB — Start Here

**Status:** ✅ Complete. Ready to execute.  
**What You Have:** Everything needed to build a production security knowledge base for your Researcher agent.

---

## 📖 Read These First (5 min)

1. **`docs/COPILOT_WORKFLOW.md`** — Why Copilot is being used, how it works
2. **`KB_IMPLEMENTATION_SUMMARY.md`** — What was delivered, architecture decisions

## 🔍 Review Sources (10 min)

```bash
cat kb/sources.json | jq '.sources | length'  # Should show 18
cat kb/sources.json | jq '.sources[] | .title'  # See all source titles
```

Approval needed? Edit `kb/sources.json` directly if you want to:
- Remove a source
- Add a source
- Change stack_applicable_to

## 🚀 Run Ingestion (2-3 min)

### Prerequisites
```bash
# Install dependencies
pip install azure-search-documents azure-identity openai requests

# Set Azure credentials (required)
export AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net"
export AZURE_SEARCH_KEY="your-search-key"
export AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com"
export AZURE_OPENAI_KEY="your-openai-key"
export AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
```

### Run It
```bash
cd /Users/snoopy/Dev/fmv2
python kb/ingest_security_kb.py --sources kb/sources.json --config kb/kb_config.json
```

**Expected output:** `✅ Ingestion complete! Total chunks indexed: 325`

## 🔗 Integrate with Researcher Agent (30 min)

Read: `kb/RESEARCHER_INTEGRATION.md`

It shows:
- How to add a new `search_security_kb` tool
- How to implement the handler
- How to wire it into your Researcher agent loop
- How to add fallback to Tavily

Code snippets are ready to copy-paste.

## ✅ Validate (5 min)

Create this validation script (copy below) and run it:

```bash
cat > kb/validate_kb_connection.py << 'VEOF'
#!/usr/bin/env python3
import os
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential

search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_KEY")
index_name = "fix-my-vibe-security-kb"

try:
    search_client = SearchClient(search_endpoint, index_name, search_key)
    results = search_client.search(search_text="SQL injection")
    count = 0
    for result in results:
        count += 1
    print(f"✅ Connected. Found {count} results for 'SQL injection'")
except Exception as e:
    print(f"❌ Connection failed: {e}")
VEOF
python kb/validate_kb_connection.py
```

## 🧪 Test End-to-End (5 min)

Once Researcher is integrated:
```bash
fix-my-vibe tests/fixtures/vulnerable-project --verbose
```

Look for: Researcher queries KB, gets results with source URLs.

## 📤 Deploy (5 min)

```bash
azd up
```

---

## 🎓 Architecture at a Glance

```
Researcher Agent
      ↓
   Try KB first: "What's SQL injection?"
      ↓
Azure AI Search Index (18 sources, ~325 chunks)
      ├─ Vector search (semantic matching)
      ├─ Metadata filters (stack, threat)
      └─ Returns top 5 chunks + source URLs
      ↓
Researcher includes citations
      ↓
"Based on [OWASP CWE-89], SQL injection occurs when..."
"See: https://cwe.mitre.org/..."
      ↓
If KB returns nothing → fallback to Tavily
```

## 📁 Files Reference

| File | What It Does |
|------|-------------|
| `kb/sources.json` | 18 curated sources + metadata |
| `kb/kb_config.json` | Index schema + embedding config |
| `kb/ingest_security_kb.py` | Fetches → chunks → embeds → uploads |
| `kb/RESEARCHER_INTEGRATION.md` | How to integrate with agent |
| `kb/README.md` | KB quick start |
| `docs/COPILOT_WORKFLOW.md` | Architecture explanation |
| `KB_IMPLEMENTATION_SUMMARY.md` | Full deliverables breakdown |

## ⏱️ Timeline

- **Now:** Review + Run ingestion (~15 min)
- **Next:** Integrate with Researcher agent (~30 min)
- **Then:** Test on fixture + Deploy (~10 min)
- **Total:** ~1 hour to get KB live in Foundry

## ❓ Questions?

- **"Which sources should I use?"** → All 18 are authoritative; nothing to remove.
- **"How do I add more sources?"** → Edit `kb/sources.json`, re-run `ingest_security_kb.py`
- **"What if ingestion fails?"** → Check Azure credentials; see `kb_ingestion.log` for details.
- **"How often do I refresh?"** → Quarterly (run ingestion script again).
- **"Does this break anything?"** → No. KB is additive (Researcher tries KB first, falls back to web).

---

**Created:** 2026-06-11  
**Status:** ✅ Ready to go  
**Next Step:** Read `docs/COPILOT_WORKFLOW.md`
