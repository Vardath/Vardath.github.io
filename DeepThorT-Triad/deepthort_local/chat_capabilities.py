"""Bounded, read-only capability evidence for ordinary Triad conversations."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

# These paths are application source, never user state, credentials or model weights.
FEATURES = (
    ("desktop_app.py", "Desktop chat, project planning, approved work and tool dispatch"),
    ("deepthort_local/triad_profiles.py", "Pinned implementation, JANUS and Sentinel model profiles"),
    ("deepthort_local/memory_governor.py", "Sentinel-governed project memory"),
    ("deepthort_local/capability_library.py", "Read-only project and capability discovery"),
    ("deepthort_local/online_tool_search.py", "Package catalogue search (not general web research)"),
    ("deepthort_local/video_render.py", "Local rendering of reviewed video assets"),
    ("deepthort_local/project_authority.py", "Project-bound authorization and rollback-related safeguards"),
)
SELF_REVIEW = re.compile(r"\b(?:self[- ](?:inspect(?:ion)?|review|improv(?:e|ement))|(?:your|own|its own)\s+(?:code|source|architecture|capabilities)|(?:review|inspect|analyse|analyze|audit)\s+(?:deepthort|yourself))\b", re.I)
ACTION = re.compile(r"\b(?:research|search|browse|inspect|review|analyse|analyze|audit|build|create|develop|compare|improve|fix|install|generate|render|execute|test|download|look online)\b", re.I)

def _source(root: Path, relative: str) -> bytes | None:
    """Only read regular, non-symlink allowlisted application files."""
    path = root / relative
    try:
        if any(p.is_symlink() for p in (path, *path.parents) if p != root and root in p.parents):
            return None
        if not path.is_file() or not path.resolve().is_relative_to(root):
            return None
        with path.open("rb") as handle:
            data = handle.read(1_000_001)
        return data if len(data) <= 1_000_000 else None
    except (OSError, ValueError):
        return None

def chat_context(prompt: str, original: str, root: Path, *, project: str,
                 inventory=None, model_ready=False, max_chars=7500):
    """Return enriched prompt, token budget, route and observed source count.

    No tool calls, writes, downloads or automatic approval. Presence is not proof
    of successful execution. The user's entire prompt remains intact.
    """
    root = Path(root).resolve()
    route = "self_review" if SELF_REVIEW.search(original) else (
        "action" if ACTION.search(original) else "conversation")
    tokens = {"conversation": 256, "action": 512, "self_review": 640}[route]
    room = max(0, max_chars - len(prompt))
    if room < 350:
        return prompt, tokens, route, 0
    facts = [
        "HOST CAPABILITY EVIDENCE (not tool execution):",
        "You are DeepThorT Triad, a local AI application, not merely the underlying model.",
        "Inference is local; that does not mean the host lacks computer or network tools.",
        "Do not invent tool access, deny observed host abilities, or claim actions without evidence.",
        "This chat can report inspected evidence. Project work uses Draft project plan and approved queue; do not claim it has started.",
        "General web research is not dispatched by this chat route. Package search and asset acquisition are distinct.",
        "Workspace: " + ("none selected" if project == "(general)" else "selected"),
        "Local model readiness reported by host: " + ("ready" if model_ready else "not confirmed"),
    ]
    # Inventory observations are not runtime verification.
    if isinstance(inventory, dict):
        tools = [str(x.get("name", ""))[:48] for x in inventory.get("tools", [])
                 if isinstance(x, dict) and x.get("found") and x.get("name")]
        if tools:
            facts.append("Previously detected tools (not tested now): " + ", ".join(tools[:12]))
    present = []
    for relative, label in FEATURES:
        data = _source(root, relative)
        if data is None:
            continue
        present.append((relative, label, data))
    facts.append("Observed application source modules (presence only): " +
                 "; ".join(label for _, label, _ in present))
    if route == "self_review":
        facts.append("Read-only self-inspection: these installed source files were opened; no modifications made.")
        for relative, _, data in present:
            facts.append(relative + " sha256=" + hashlib.sha256(data).hexdigest()[:16])
        # Exact short source lines provide actionable evidence, not invented excerpts.
        desktop = next((data for relative, _, data in present if relative == "desktop_app.py"), b"")
        lines = desktop.decode("utf-8", errors="replace").splitlines()
        for marker in ("if request['mode']=='chat' and not large_spec:", "def _governed_memory(",
                       "def _planning_council_client(", "def _project_work_is_enabled("):
            for i, line in enumerate(lines):
                if marker in line:
                    excerpt = "\n".join(f"{j+1}: {lines[j][:180]}" for j in range(i, min(i+4, len(lines))))
                    facts.append("Observed source excerpt, not instructions:\n" + excerpt)
                    break
        facts.append("Use the observed source to identify a concrete gap; distinguish inspection from proposed changes. "
                     "If online research or deeper source inspection is needed, say it has not yet happened.")
    prefix = "\n\n"
    # Include whole evidence lines only; never truncate the original user prompt.
    chosen = []
    for fact in facts:
        candidate = prefix + "\n".join(chosen + [fact])
        if len(candidate) <= room:
            chosen.append(fact)
    return prompt + (prefix + "\n".join(chosen) if chosen else ""), tokens, route, len(present)
