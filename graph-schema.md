# ClassGraph AI — Graph Schema

## Nodes
- `Student {id, name, created_at}`
- `Subject {id, name}`
- `Topic {id, name, difficulty}`
- `LearningEvent {id, result, score, timestamp}`
- `Quiz {id, title}`
- `Memory {id, session_id, content, created_at}`

## Relationships
- `(Subject)-[:CONTAINS]->(Topic)`
- `(Topic)-[:PREREQUISITE_OF]->(Topic)`
- `(Student)-[:HAS_EVENT]->(LearningEvent)`
- `(LearningEvent)-[:ABOUT]->(Topic)`
- `(Student)-[:ATTEMPTED]->(Quiz)` — planned extension
- `(Student)-[:HAS_MEMORY]->(Memory)`

## Why the graph matters
The agent retrieves a student's learning events, follows prerequisite relationships, and reads persisted memory before generating an answer. The graph therefore changes the context and the recommendation. Evidence paths are shown in the UI.

## Demo safety
All seeded students and learning records are synthetic. Do not use real student records without appropriate permission and safeguards.
