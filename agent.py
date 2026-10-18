from dotenv import load_dotenv
load_dotenv()

import json
import os
import uuid
import requests
from graph_store import (
    get_student_context, get_recent_memories, save_memory, GraphUnavailable
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def _fallback_answer(question, context):
    events = context.get("learning_events", [])
    prerequisites = context.get("prerequisites", [])
    needs_revision = [
        e["topic"] for e in events
        if str(e.get("result", "")).lower() in {"needs_revision", "incorrect", "weak"}
        or (isinstance(e.get("score"), (int, float)) and e["score"] < 60)
    ]
    q = question.lower()
    if any(word in q for word in ["revise", "next", "study", "weak", "recommend"]):
        if needs_revision:
            answer = "Based on the graph's learning events, start by revising **" + ", ".join(sorted(set(needs_revision))) + "**."
        else:
            answer = "I don't see a low-score or needs-revision event for this student yet. Try reviewing a topic quiz so the graph has evidence to personalize the next recommendation."
    else:
        answer = "I retrieved the student's learning events, topic prerequisites, and previous memories from FalkorDB. Ask what to revise next, or ask about a prerequisite relationship to explore the graph evidence."
    if prerequisites:
        sample = [f"{p['prerequisite']} → {p['next_topic']}" for p in prerequisites[:5]]
        answer += "\n\nSome prerequisite links in the graph: " + "; ".join(sample) + "."
    answer += "\n\n*Note: Ollama was unavailable, so this is a deterministic response based on graph data, not an LLM-generated answer.*"
    return answer


def _call_ollama(question, context):
    prompt = f"""You are ClassGraph AI, an educational assistant.
Answer the student's question using only the provided graph context.
Do not invent learning results or relationships. If the context is insufficient, say so.
Explain recommendations with short evidence paths. Do not claim certainty about a student's ability.
Be concise and helpful.

QUESTION:
{question}

GRAPH CONTEXT JSON:
{json.dumps(context, ensure_ascii=False, default=str)}

Return:
1. Answer
2. Why this answer (cite topic/event/relationship names from context)
3. Suggested next step
"""
    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    answer = data.get("response", "").strip()
    if not answer:
        raise RuntimeError("Ollama returned an empty response.")
    return answer


def answer_question(student_id, question):
    # FalkorDB context retrieval is mandatory; the LLM never answers from an empty graph.
    context = get_student_context(student_id)
    memories = get_recent_memories(student_id, limit=5)
    context["recent_memories"] = memories
    evidence = []
    for event in context.get("learning_events", []):
        evidence.append(
            f"Learning event: {event.get('topic')} — result={event.get('result')}, score={event.get('score')}"
        )
    for relation in context.get("prerequisites", []):
        evidence.append(
            f"Prerequisite: {relation.get('prerequisite')} → {relation.get('next_topic')}"
        )
    for memory in memories[:3]:
        evidence.append(f"Memory from {memory.get('session_id')}: {memory.get('content')[:180]}")

    try:
        answer = _call_ollama(question, context)
        llm_used = True
    except (requests.RequestException, RuntimeError, ValueError):
        answer = _fallback_answer(question, context)
        llm_used = False

    session_id = st_session_id()
    memory_content = f"Question: {question}\nAssistant answer: {answer[:700]}"
    try:
        save_memory(student_id, session_id, memory_content)
        memory_note = f"Saved to FalkorDB memory (session {session_id})."
    except Exception as exc:
        memory_note = f"Answer generated, but saving memory failed: {exc}"

    if llm_used:
        memory_note += f" Model: {OLLAMA_MODEL}."
    return {
        "answer": answer,
        "evidence": evidence[:15],
        "memory_note": memory_note,
    }


def st_session_id():
    # One stable session ID per Python process is sufficient for this demo;
    # the UI session is intentionally not used as a security identity.
    if not hasattr(st_session_id, "_value"):
        st_session_id._value = str(uuid.uuid4())[:8]
    return st_session_id._value
