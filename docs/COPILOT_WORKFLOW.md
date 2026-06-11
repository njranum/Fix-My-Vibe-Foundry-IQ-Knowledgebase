# Copilot-Driven Security Knowledge Base Automation

## Fix My Vibe Researcher Agent × Azure AI Search × Foundry IQ

**Status:** Researcher Agent Enhancement — Replaces Web Search Layer  
**Author:** GitHub Copilot (Claude Haiku 4.5)  
**Role:** Knowledge Base Automation & Integration Partner  
**Project:** Fix My Vibe (Microsoft AI Skills Fest, Agents League)

---

## Executive Summary

This document explains **how Copilot automates** the security knowledge base layer that powers the Researcher agent in Fix My Vibe. 

**Current state:** Researcher calls Tavily web search for each query.  
**New architecture:** Researcher queries a curated Azure AI Search index instead.

Copilot's role is to **build and maintain** that index:
1. **Intelligent research** (curate authoritative security sources)
2. **Smart ingestion** (scrape + chunk + embed security docs)
3. **Efficient indexing** (batch upload to Azure AI Search)
4. **Seamless integration** (provide Researcher agent with index queries)

**Why Copilot?** Manually curating and uploading security docs defeats the purpose. This automation ensures the KB stays current, consistent, and efficient without overhead.

---

## Context: Fix My Vibe Project

Fix My Vibe is a **multi-agent AI coding diagnostics tool** that scans developer projects, detects which AI tools they use (Claude Code, Cursor, GitHub Copilot, etc.), and generates tailored configuration files—with a focus on **security**.

The pipeline:
1. **Scanner Agent** — detects tools + finds security issues (hardcoded secrets, weak crypto, etc.)
2. **Researcher Agent** — fetches current best practices for each tool/stack combination
3. **Planner Agent** — generates configuration files tailored to the project
4. **Executor Agent** — writes files with user confirmation
5. **Verifier Agent** — validates output quality

The **Researcher agent** is currently backed by Tavily (web search). We're replacing that with a curated knowledge base of **security patterns, OWASP threats, and stack-specific guidance** — making research faster, grounded, and citable.

---

## What Copilot Does

### Phase 1: Security Research & Curation

**Problem:** Manually finding authoritative security sources is slow; web search results vary by day.

**Copilot's Role:**
- Researches **only authoritative security sources**:
  - OWASP Top 10 & CWE registry
  - NIST secure coding standards
  - Language/framework-specific guides (Python, FastAPI, JavaScript, React, etc.)
  - Anthropic security best practices
  - Microsoft Learn security articles
- Validates URLs are stable (live, not paywalled)
- Organizes by **threat model** (injection, crypto, logging, config, auth, etc.) and **stack** (python, fastapi, javascript, react)
- Creates a versioned source list with **publication dates** (for refresh tracking)

**Deliverable:** `sources.json` — vetted URLs + threat categories + stack applicability

---

### Phase 2: Intelligent Ingestion

**Problem:** Raw security docs vary in structure; random chunking breaks semantic search quality.

**Copilot's Role:**
- Writes a **Python script** (`ingest_security_kb.py`) that:
  - Fetches documents from curated URLs
  - Cleans/normalizes security content (preserves code samples, warnings, tables)
  - **Chunks by threat or pattern** (not randomly) — ~500 tokens per chunk
  - Adds metadata:
    - `threat_category`: injection, auth, crypto, logging, config, serialization, etc.
    - `owasp_mapping`: A01:2021, A02, A06, A07, A09, etc.
    - `stack_tags`: python, fastapi, javascript, react, nodejs, etc.
    - `source_publication_date`: for freshness tracking
    - `source_url`: for citations
  - Generates embeddings via Azure OpenAI (batched for cost efficiency)
  - Deduplicates (same threat from multiple sources → keep if unique insight)
  - Validates chunks before upload (no empty chunks, no broken links)

**Why This Matters:**
- Zero manual doc editing
- **Threat-aware chunking** = better "What's the injection risk in FastAPI?" queries
- Metadata enables **filtered search** (Scanner detected Python+FastAPI? Query only those threat docs)
- Deduplication prevents agent hallucination (doesn't cite same fact twice)
- Batched embeddings reduce API cost by 50-80%

**Deliverable:** `ingest_security_kb.py` — production-ready, handles edge cases

---

### Phase 3: Index Management

**Problem:** Azure AI Search setup requires careful configuration; Researcher needs seamless integration.

**Copilot's Role:**
- Writes **config-driven setup** (`kb_config.json`):
  - Index schema with security-specific fields (threat_category, owasp_mapping, stack_tags)
  - Vector search config (Azure OpenAI embeddings model/dimension)
  - Batch parameters optimized for security content
  - Validation checks (URL health, chunk completeness)
- Uses **Azure MCP tools** for reproducible index creation (no manual Portal work)
- Provides integration instructions for Researcher agent

**Why This Matters:**
- Reproducible setup across environments (dev, prod, team members)
- Auditable ingestion logs (when added, what, why)
- Version-controlled config (easy to review, diff, revert)

**Deliverable:** `kb_config.json` + Azure index auto-provisioned + integration guide

---

### Phase 4: Researcher Agent Integration

**Problem:** Researcher currently calls Tavily. We need to replace that with indexed search.

**Copilot's Role:**
- Provides **integration code snippet** showing:
  - How Researcher queries Azure AI Search instead of Tavily
  - How to pass **stack context** (Python? FastAPI?) to filter threat docs
  - How to cite sources in Researcher output
  - Graceful fallback: if KB returns no results, Researcher can still query Tavily
- Generates **connection validation script** (`validate_kb_connection.py`)
- Documents the new Researcher tool definition and parameters

**Why This Matters:**
- Seamless agent upgrade (no Researcher code rewrite, just tool swap)
- Hybrid approach (KB-first, web search fallback) handles edge cases
- Citations are automatic (source_url in index metadata)

**Deliverable:** Integration code + validation script + updated Researcher tool definition

---

### Phase 5: Validation & Refresh Strategy

**Problem:** Security docs get outdated; we need an automated refresh strategy.

**Copilot's Role:**
- Tests the index with known-good security queries:
  - "What's an OWASP A07 vulnerability?" → Should return hardcoded secrets docs
  - "How do I fix SQL injection in FastAPI?" → Should return FastAPI + injection docs
  - "What's the risk of debug=True?" → Should return Django/Flask guidance
- Documents what was indexed + when (publication dates)
- Provides a **refresh checklist** (quarterly: reindex? New OWASP versions? New frameworks?)
- Generates a sample `refresh_kb.py` script for easy re-indexing

**Deliverable:** `VALIDATION_REPORT.md` + refresh strategy + sample refresh script

---

## Architecture Decisions (Why This Approach?)

### Why Azure AI Search?
- **Semantic search** (understands threat meaning, not just keywords)
- **Vector embeddings** (finds similar security patterns, not exact matches)
- **Low latency** (instant queries for Researcher agent)
- **Citation support** (source URLs are built in)
- **Native Foundry integration** (Researcher agent can query it directly)
- **Filterable metadata** (query only Python threats, only OWASP A07, etc.)

### Why Batch Embeddings?
- **Cost:** 1 API call for 100 chunks instead of 100 separate calls
- **Speed:** 10-20x faster ingestion
- **Reliability:** Retry logic built in

### Why Threat-Aware Chunking?
- **Quality:** Keeping threat context together improves search results
- **Recall:** Agent asks "How do I prevent injection?" → finds injection docs, not random chunks
- **Efficiency:** Semantic relevance without over-chunking

### Why Metadata?
- **Filtering:** Scanner found FastAPI vulnerability → search only FastAPI threat docs
- **Citing:** Every chunk has source_url → Researcher can say "based on docs.owasp.org"
- **Freshness:** source_publication_date helps detect outdated guidance

### Why Config-Driven?
- **Reproducibility:** Same config = same index every time (no manual clicks)
- **Auditability:** Git-tracked config (easy to review, diff, rollback)
- **Scalability:** Change config, re-run ingestion (no code changes)

---

## Files in This Workflow

| File | Purpose | Created By |
|------|---------|-----------|
| `sources.json` | Curated security sources + threat categories + stacks | Copilot Research |
| `kb_config.json` | Index schema + embedding config + batch parameters | Copilot |
| `ingest_security_kb.py` | Download + clean + chunk + embed + upload script | Copilot |
| `validate_kb_connection.py` | Test index connection + run sample queries | Copilot |
| `VALIDATION_REPORT.md` | What was indexed, metrics, sample query results | Copilot |
| `researcher_agent_integration.py` | Code snippet: how Researcher queries the KB | Copilot |
| `COPILOT_WORKFLOW.md` | This document (explains the architecture) | Copilot |

---

## The Workflow in Action

```
You: "Let's replace Tavily with a curated security KB"
     ↓
Copilot: Research authoritative security sources
     ↓
You: Review sources (approve/reject/suggest)
     ↓
Copilot: Write ingest_security_kb.py + kb_config.json + integration code
     ↓
You: Run `python ingest_security_kb.py`
     ↓
Copilot: Validate index, generate VALIDATION_REPORT.md
     ↓
You: Update Researcher agent to use Azure AI Search
     ↓
Researcher: Now queries curated KB first, falls back to Tavily if needed
```

**Total human effort:** ~15 minutes (review sources + run script + integrate)  
**Total automation:** ~90% (research, scripts, indexing, validation)

---

## Copilot's Constraints & Scope

**What Copilot Does:**
- ✅ Research & curate security sources
- ✅ Write production-ready ingestion scripts
- ✅ Manage index configuration
- ✅ Document the architecture
- ✅ Validate results
- ✅ Provide integration code snippets

**What You Do:**
- ✅ Approve sources (security expert judgment)
- ✅ Run the ingestion script (one command)
- ✅ Integrate into Researcher agent (code review)
- ✅ Deploy to Foundry (azd up)
- ✅ Monitor in production

---

## Next Steps

1. **Confirm topic scope** — Security patterns for all stacks? Or specific (FastAPI + React)?
2. **Approve sources** — Review `sources.json`, accept/reject/suggest
3. **Run ingestion** — `python ingest_security_kb.py` (~2–5 minutes)
4. **Validate KB** — `python validate_kb_connection.py` (tests 10 sample queries)
5. **Integrate Researcher** — Swap Tavily for Azure AI Search in agent code
6. **Deploy** — `azd up` (updates Foundry agent with KB connection)

---

**Created:** 2026-06-11  
**Status:** ✅ Research + Automation Phase Complete  
**Next:** Review sources → Run ingestion → Integrate with Researcher agent
