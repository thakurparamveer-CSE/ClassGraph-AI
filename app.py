from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from graph_store import (
    check_connection, initialize_graph, seed_demo_data, get_student_context,
    get_recent_memories, get_graph_overview, get_evidence_paths, save_memory,
    get_student_ids, GraphUnavailable
)
from agent import answer_question

st.set_page_config(page_title="ClassGraph AI", page_icon="🧠", layout="wide")

st.title("🧠 ClassGraph AI")
st.caption("A graph-powered learning assistant for Class+ — with persistent memory and explainable recommendations.")

with st.sidebar:
    st.header("Setup & demo")
    st.write("Uses FalkorDB for connected learning context and Ollama for local LLM responses.")
    if st.button("Check FalkorDB connection", use_container_width=True):
        try:
            check_connection()
            st.success("FalkorDB connection is working.")
        except Exception as exc:
            st.error(f"FalkorDB is not available: {exc}")
    if st.button("Initialize / seed demo graph", use_container_width=True):
        try:
            initialize_graph()
            seed_demo_data()
            st.success("Demo graph is ready.")
        except Exception as exc:
            st.error(f"Could not seed graph: {exc}")
    st.divider()
    student_ids = ["demo_student", "demo_student_2"]
    try:
        discovered = get_student_ids()
        if discovered:
            student_ids = sorted(set(student_ids + discovered))
    except Exception:
        pass
    student_id = st.selectbox("Demo student", student_ids, key="student_id")
    st.caption("Use synthetic demo identities only. Do not enter real student records.")

tab_chat, tab_graph, tab_memory, tab_about = st.tabs(
    ["💬 Ask ClassGraph", "🕸️ Graph Explorer", "🧠 Memory", "ℹ️ About"]
)

with tab_chat:
    st.subheader("Ask a learning question")
    st.write("Try: **What should I revise next, and why?**")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("evidence"):
                with st.expander("Graph evidence used"):
                    for item in msg["evidence"]:
                        st.write(f"• {item}")
            if msg.get("memory_note"):
                st.caption(msg["memory_note"])

    question = st.chat_input("Ask about topics, prerequisites, quizzes, or revision...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Retrieving graph context and reasoning..."):
                try:
                    result = answer_question(student_id, question)
                    st.markdown(result["answer"])
                    if result.get("evidence"):
                        with st.expander("Graph evidence used", expanded=True):
                            for item in result["evidence"]:
                                st.write(f"• {item}")
                    if result.get("memory_note"):
                        st.caption(result["memory_note"])
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "evidence": result.get("evidence", []),
                        "memory_note": result.get("memory_note", "")
                    })
                except GraphUnavailable as exc:
                    message = f"FalkorDB is required for graph-grounded answers. {exc}"
                    st.error(message)
                    st.session_state.messages.append({"role": "assistant", "content": message})
                except Exception as exc:
                    message = f"Something went wrong: {exc}"
                    st.error(message)
                    st.session_state.messages.append({"role": "assistant", "content": message})

with tab_graph:
    st.subheader("Graph overview")
    try:
        overview = get_graph_overview()
        a, b, c = st.columns(3)
        a.metric("Students", overview.get("students", 0))
        b.metric("Topics", overview.get("topics", 0))
        c.metric("Memories", overview.get("memories", 0))
        st.markdown("#### Learning relationships")
        paths = get_evidence_paths(student_id)
        if paths:
            for path in paths:
                st.write(f"**{path['topic']}** → {path['related']}  \nReason: {path['reason']}")
        else:
            st.info("No evidence paths yet. Click **Initialize / seed demo graph** in the sidebar.")
        st.markdown("#### Graph context for this student")
        context = get_student_context(student_id)
        st.json(context)
    except Exception as exc:
        st.warning("Connect FalkorDB and seed the demo graph to explore relationships.")
        st.code(str(exc))

with tab_memory:
    st.subheader("Persistent memory across sessions")
    st.write("Memories are stored as graph nodes, so they remain available after the browser chat is cleared.")
    try:
        memories = get_recent_memories(student_id)
        if memories:
            for memory in memories:
                with st.container(border=True):
                    st.caption(f"Session: {memory.get('session_id', 'unknown')} · {memory.get('created_at', '')}")
                    st.write(memory.get("content", ""))
        else:
            st.info("No saved memories yet. Ask a question in the chat after seeding the graph.")
    except Exception as exc:
        st.warning(f"Memory view unavailable: {exc}")

with tab_about:
    st.subheader("How it works")
    st.markdown("""
    1. **Retrieve:** the agent queries FalkorDB for the student's learning events, related topics and past memories.
    2. **Reason:** it builds a context packet from graph results before asking the language model to answer.
    3. **Explain:** the response includes graph evidence and the relationships used.
    4. **Remember:** the interaction is saved as a `Memory` node connected to the student.

    **Tech stack:** Python · Streamlit · FalkorDB · Cypher · Ollama (optional local LLM).

    If Ollama is unavailable, the app uses a clearly labelled deterministic response based on retrieved graph data. Graph retrieval itself still requires FalkorDB.
    """)
    st.markdown("See `README.md` for setup, troubleshooting, tests and demo instructions.")
