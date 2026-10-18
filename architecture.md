# Architecture

1. Streamlit receives the user's question and selected demo student.
2. `agent.py` asks `graph_store.py` for graph-backed context and prior memories.
3. FalkorDB executes Cypher queries to retrieve learning events, prerequisite paths, and persisted memory.
4. The agent sends that evidence to the configured Ollama model.
5. If Ollama is unavailable, a clearly labelled deterministic fallback uses retrieved graph data.
6. The interaction is saved as a `Memory` node connected to the student.
7. The UI displays the answer, evidence, and memory-save status.

FalkorDB is required for graph-grounded responses. The fallback does not simulate a graph connection.
