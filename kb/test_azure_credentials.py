#!/usr/bin/env python3
"""
test_azure_credentials.py

Diagnostics for Azure AI Search + Azure OpenAI / AI Foundry credentials.
Tests connectivity, lists deployments, and attempts a real embedding call.
"""

import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

# ── helpers ──────────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}OK{RESET}    {msg}")
def warn(msg): print(f"  {YELLOW}WARN{RESET}  {msg}")
def fail(msg): print(f"  {RED}FAIL{RESET}  {msg}")
def info(msg): print(f"        {msg}")


# ── Azure AI Search ───────────────────────────────────────────────────────────

def test_search():
    print("\n━━━ Azure AI Search ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "").rstrip("/")
    key      = os.getenv("AZURE_SEARCH_KEY", "")

    if not endpoint or not key:
        fail("AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY not set")
        return

    url = f"{endpoint}/indexes?api-version=2024-07-01"
    try:
        r = requests.get(url, headers={"api-key": key}, timeout=10)
        if r.status_code == 200:
            indexes = [i["name"] for i in r.json().get("value", [])]
            ok(f"Connected — {len(indexes)} index(es): {indexes or '(none)'}")
        else:
            fail(f"HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        fail(str(e))


# ── Azure OpenAI / AI Foundry helpers ─────────────────────────────────────────

API_VERSIONS = [
    "2024-10-21",
    "2024-08-01-preview",
    "2024-12-01-preview",
    "2024-02-15-preview",
    "2023-12-01-preview",
]

DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def _probe_models(base: str, key: str) -> bool:
    """Try /openai/models; return True if successful."""
    for ver in API_VERSIONS:
        url = f"{base}/openai/models?api-version={ver}"
        try:
            r = requests.get(url, headers={"api-key": key}, timeout=10)
            if r.status_code == 200:
                models = r.json().get("data", [])
                embed  = [m["id"] for m in models if m.get("capabilities", {}).get("embeddings")]
                ok(f"/openai/models ({ver}) → {len(models)} models, embedding-capable: {embed or '(none)'}")
                return True
            else:
                info(f"/openai/models ({ver}) → HTTP {r.status_code}: {r.text[:120]}")
        except Exception as e:
            info(f"/openai/models ({ver}) → ERR {e}")
    return False


def _probe_deployments(base: str, key: str):
    """Try /openai/deployments; print whatever we find."""
    for ver in API_VERSIONS[:3]:
        url = f"{base}/openai/deployments?api-version={ver}"
        try:
            r = requests.get(url, headers={"api-key": key}, timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", r.json())
                ok(f"/openai/deployments ({ver}) →")
                info(json.dumps(data, indent=4))
                return
            else:
                info(f"/openai/deployments ({ver}) → HTTP {r.status_code}: {r.text[:120]}")
        except Exception as e:
            info(f"/openai/deployments ({ver}) → ERR {e}")


def _probe_embedding(base: str, key: str) -> bool:
    """Try a real embedding call; return True if successful."""
    for ver in API_VERSIONS:
        url = f"{base}/openai/deployments/{DEPLOYMENT}/embeddings?api-version={ver}"
        try:
            r = requests.post(
                url,
                headers={"api-key": key, "Content-Type": "application/json"},
                json={"input": ["test connectivity"]},
                timeout=15,
            )
            if r.status_code == 200:
                dims = len(r.json()["data"][0]["embedding"])
                ok(f"Embedding call ({ver}) → {dims} dims — WORKING!")
                return True
            else:
                info(f"Embedding ({ver}) → HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            info(f"Embedding ({ver}) → ERR {e}")
    return False


def test_openai_endpoint(base: str, key: str, label: str):
    base = base.rstrip("/")
    print(f"\n━━━ {label} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  endpoint : {base}")
    print(f"  key      : {key[:8]}{'*' * max(0, len(key) - 8)} ({len(key)} chars)")
    print(f"  model    : {DEPLOYMENT}")

    if not base or not key:
        fail("Endpoint or key is empty — skipping")
        return

    _probe_models(base, key)
    _probe_deployments(base, key)
    working = _probe_embedding(base, key)

    if working:
        ok("This endpoint+key combination works for embeddings ✓")
    else:
        warn("No embedding variant succeeded — see details above")


# ── AI Foundry project-scoped path ────────────────────────────────────────────

def test_foundry_project_endpoint():
    """Try the /api/projects/<name>/openai/... path used by newer AI Foundry hubs."""
    project_ep = "https://njr-fmv-hackathon-resource.services.ai.azure.com/api/projects/njr-fmv-hackathon"
    key = os.getenv("AZURE_OPENAI_KEY", "")

    base = project_ep.rstrip("/")
    print(f"\n━━━ AI Foundry project-scoped endpoint ━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  endpoint : {base}")
    print(f"  key      : {key[:8]}{'*' * max(0, len(key) - 8)} ({len(key)} chars)")

    for ver in API_VERSIONS:
        url = f"{base}/openai/deployments/{DEPLOYMENT}/embeddings?api-version={ver}"
        try:
            r = requests.post(
                url,
                headers={"api-key": key, "Content-Type": "application/json"},
                json={"input": ["test connectivity"]},
                timeout=15,
            )
            if r.status_code == 200:
                dims = len(r.json()["data"][0]["embedding"])
                ok(f"Embedding ({ver}) → {dims} dims — WORKING via project path!")
                return
            else:
                info(f"Embedding ({ver}) → HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            info(f"Embedding ({ver}) → ERR {e}")

    warn("Project-scoped path also did not produce embeddings")


# ── entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Azure credential diagnostics")
    print("=" * 66)

    test_search()

    env_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    env_key      = os.getenv("AZURE_OPENAI_KEY", "")

    # 1. Endpoint from .env (as-is)
    test_openai_endpoint(env_endpoint, env_key, ".env AZURE_OPENAI_ENDPOINT (current)")

    # 2. AI Foundry hub base URL
    test_openai_endpoint(
        "https://njr-fmv-hackathon-resource.services.ai.azure.com",
        env_key,
        "AI Foundry hub base (services.ai.azure.com)",
    )

    # 3. Cognitive Services variant (some hubs expose this alias)
    test_openai_endpoint(
        "https://njr-fmv-hackathon-resource.cognitiveservices.azure.com",
        env_key,
        "Cognitive Services alias",
    )

    # 4. Project-scoped path
    test_foundry_project_endpoint()

    print("\n" + "=" * 66)
    print("Done. Fix .env AZURE_OPENAI_ENDPOINT to whichever endpoint said WORKING above.")
