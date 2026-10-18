from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timezone
from falkordb import FalkorDB

GRAPH_NAME = os.getenv("FALKORDB_GRAPH", "ClassGraph")
FALKORDB_HOST = os.getenv("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", "6379"))
FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD") or None


class GraphUnavailable(RuntimeError):
    """Raised when FalkorDB cannot be reached or queried."""


def get_graph():
    try:
        client = FalkorDB(
            host=FALKORDB_HOST,
            port=FALKORDB_PORT,
            password=FALKORDB_PASSWORD,
        )
        return client.select_graph(GRAPH_NAME)
    except Exception as exc:
        raise GraphUnavailable(
            "Start FalkorDB first. Run `docker compose up -d` and check `docker ps`."
        ) from exc


def check_connection():
    graph = get_graph()
    graph.query("RETURN 1 AS ok")
    return True


def initialize_graph():
    graph = get_graph()
    # Creating the graph with a harmless query is enough; FalkorDB creates it on use.
    graph.query("CREATE INDEX FOR (s:Student) ON (s.id)")
    graph.query("CREATE INDEX FOR (t:Topic) ON (t.id)")
    graph.query("CREATE INDEX FOR (m:Memory) ON (m.id)")
    return True


def _rows(query, params=None):
    graph = get_graph()
    result = graph.query(query, params or {})
    return result.result_set


def seed_demo_data():
    # Synthetic records only. MERGE makes this safe to run repeatedly.
    queries = [
        """MERGE (s:Student {id:'demo_student'})
           SET s.name='Demo Student', s.created_at='2026-10-15'""",
        """MERGE (s:Student {id:'demo_student_2'})
           SET s.name='Second Demo Student', s.created_at='2026-10-15'""",
        """MERGE (sub:Subject {id:'dbms'})
           SET sub.name='Database Management Systems'""",
        """MERGE (sql:Topic {id:'sql_basics'})
           SET sql.name='SQL Basics', sql.difficulty='beginner'
           MERGE (rel:Topic {id:'relational_model'})
           SET rel.name='Relational Model', rel.difficulty='beginner'
           MERGE (joins:Topic {id:'sql_joins'})
           SET joins.name='SQL Joins', joins.difficulty='intermediate'
           MERGE (norm:Topic {id:'normalization'})
           SET norm.name='Normalization', norm.difficulty='intermediate'
           MERGE (keys:Topic {id:'candidate_keys'})
           SET keys.name='Candidate Keys', keys.difficulty='beginner'
           MERGE (sub)-[:CONTAINS]->(sql)
           MERGE (sub)-[:CONTAINS]->(rel)
           MERGE (sub)-[:CONTAINS]->(joins)
           MERGE (sub)-[:CONTAINS]->(norm)
           MERGE (sub)-[:CONTAINS]->(keys)
           MERGE (sql)-[:PREREQUISITE_OF]->(joins)
           MERGE (rel)-[:PREREQUISITE_OF]->(norm)
           MERGE (keys)-[:PREREQUISITE_OF]->(norm)""",
        """MATCH (s:Student {id:'demo_student'})
           MATCH (t:Topic {id:'normalization'})
           MERGE (e:LearningEvent {id:'event_demo_normalization'})
           SET e.result='needs_revision', e.score=40, e.timestamp='2026-10-15T10:00:00Z'
           MERGE (s)-[:HAS_EVENT]->(e)
           MERGE (e)-[:ABOUT]->(t)""",
        """MATCH (s:Student {id:'demo_student'})
           MATCH (t:Topic {id:'sql_basics'})
           MERGE (e:LearningEvent {id:'event_demo_sql'})
           SET e.result='completed', e.score=85, e.timestamp='2026-10-15T09:00:00Z'
           MERGE (s)-[:HAS_EVENT]->(e)
           MERGE (e)-[:ABOUT]->(t)""",
        """MATCH (s:Student {id:'demo_student'})
           MATCH (t:Topic {id:'candidate_keys'})
           MERGE (e:LearningEvent {id:'event_demo_keys'})
           SET e.result='completed', e.score=75, e.timestamp='2026-10-15T09:30:00Z'
           MERGE (s)-[:HAS_EVENT]->(e)
           MERGE (e)-[:ABOUT]->(t)""",
    ]
    for query in queries:
        _rows(query)
    return True


def get_student_ids():
    rows = _rows("MATCH (s:Student) RETURN s.id ORDER BY s.id")
    return [row[0] for row in rows if row and row[0]]


def get_graph_overview():
    counts = {}
    for label, key in [
        ("Student", "students"),
        ("Topic", "topics"),
        ("Memory", "memories"),
        ("LearningEvent", "learning_events"),
    ]:
        rows = _rows(f"MATCH (n:{label}) RETURN count(n)")
        counts[key] = int(rows[0][0]) if rows and rows[0][0] is not None else 0
    return counts


def get_student_context(student_id):
    events = _rows(
        """MATCH (s:Student {id:$student_id})-[:HAS_EVENT]->(e:LearningEvent)-[:ABOUT]->(t:Topic)
           RETURN t.name, e.result, e.score, e.timestamp
           ORDER BY e.timestamp DESC LIMIT 20""",
        {"student_id": student_id},
    )
    memories = _rows(
        """MATCH (s:Student {id:$student_id})-[:HAS_MEMORY]->(m:Memory)
           RETURN m.content, m.session_id, m.created_at
           ORDER BY m.created_at DESC LIMIT 8""",
        {"student_id": student_id},
    )
    prerequisites = _rows(
        """MATCH (a:Topic)-[:PREREQUISITE_OF]->(b:Topic)
           RETURN a.name, b.name LIMIT 30"""
    )
    return {
        "student_id": student_id,
        "learning_events": [
            {"topic": r[0], "result": r[1], "score": r[2], "timestamp": r[3]}
            for r in events
        ],
        "memories": [
            {"content": r[0], "session_id": r[1], "created_at": r[2]}
            for r in memories
        ],
        "prerequisites": [
            {"prerequisite": r[0], "next_topic": r[1]} for r in prerequisites
        ],
    }


def get_evidence_paths(student_id):
    rows = _rows(
        """MATCH (s:Student {id:$student_id})-[:HAS_EVENT]->(e:LearningEvent)-[:ABOUT]->(weak:Topic)
           OPTIONAL MATCH (weak)-[:PREREQUISITE_OF*0..2]->(related:Topic)
           RETURN DISTINCT weak.name, related.name, e.result
           LIMIT 30""",
        {"student_id": student_id},
    )
    paths = []
    for row in rows:
        topic, related, result = row[0], row[1], row[2]
        if topic:
            reason = f"Previous learning event recorded as '{result}'."
            if related and related != topic:
                reason += f" Graph path links {topic} to {related}."
            paths.append({"topic": topic, "related": related or topic, "reason": reason})
    return paths


def get_recent_memories(student_id, limit=20):
    rows = _rows(
        """MATCH (s:Student {id:$student_id})-[:HAS_MEMORY]->(m:Memory)
           RETURN m.session_id, m.content, m.created_at
           ORDER BY m.created_at DESC LIMIT $limit""",
        {"student_id": student_id, "limit": int(limit)},
    )
    return [
        {"session_id": r[0], "content": r[1], "created_at": r[2]}
        for r in rows
    ]


def save_memory(student_id, session_id, content):
    now = datetime.now(timezone.utc).isoformat()
    memory_id = f"{student_id}:{session_id}:{now}"
    _rows(
        """MATCH (s:Student {id:$student_id})
           CREATE (m:Memory {id:$memory_id, session_id:$session_id,
                             content:$content, created_at:$created_at})
           CREATE (s)-[:HAS_MEMORY]->(m)
           RETURN m.id""",
        {
            "student_id": student_id,
            "session_id": session_id,
            "content": content[:1200],
            "created_at": now,
            "memory_id": memory_id,
        },
    )
    return memory_id
