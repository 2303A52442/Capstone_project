"""RAG retrieval service providing external domain knowledge for skills, career requirements, and learning resources.

This service uses local vector embeddings via scikit-learn TF-IDF to retrieve verified external
learning resources and benchmarks to enrich recommendations and Career Twin guidance without
hallucinating or modifying structured candidate facts.
"""

from typing import Any

# Curated external knowledge base
CURATED_KNOWLEDGE_BASE: list[dict[str, Any]] = [
    {
        "id": "kb_python_01",
        "topic": "Python",
        "category": "Programming",
        "title": "Production Python & FastAPI Architecture",
        "description": "Standard production practices for asynchronous API design, Pydantic validation, dependency injection, and PEP8 conformance.",
        "resource_url": "https://fastapi.tiangolo.com/tutorial/",
        "recommended_exercises": [
            "Implement asynchronous repository patterns with SQLAlchemy 2.0",
            "Write pytest fixtures with isolated in-memory test databases",
        ],
        "benchmark_level_4": "Ability to design layered architectures, manage connection pools, handle async concurrency, and structure testable microservices.",
    },
    {
        "id": "kb_sql_01",
        "topic": "SQL",
        "category": "Data",
        "title": "Relational Data Modeling & Query Optimization",
        "description": "Relational schema normalization (3NF), complex multi-table joins, window functions, and indexing strategies in PostgreSQL.",
        "resource_url": "https://www.postgresql.org/docs/current/queries.html",
        "recommended_exercises": [
            "Analyze query performance using EXPLAIN ANALYZE on multi-join queries",
            "Design composite indexes to eliminate sequential scans on filtered foreign keys",
        ],
        "benchmark_level_4": "Proficiency in query planning, transaction isolation levels, indexing (B-Tree, GIN), and writing CTEs for reporting.",
    },
    {
        "id": "kb_system_design_01",
        "topic": "System Design",
        "category": "Architecture",
        "title": "Distributed Systems & Scalable API Design",
        "description": "Principles of horizontal scaling, stateless services, caching tiers (Redis), asynchronous queues, and database sharding.",
        "resource_url": "https://github.com/donnemartin/system-design-primer",
        "recommended_exercises": [
            "Design an idempotent recommendation feedback pipeline with audit logs",
            "Model database partitioning and read-replica strategies for high read-throughput",
        ],
        "benchmark_level_4": "Ability to model trade-offs between consistency and availability (CAP theorem), rate limiting, caching strategies, and telemetry.",
    },
    {
        "id": "kb_testing_01",
        "topic": "Testing",
        "category": "Engineering",
        "title": "Automated Testing & Continuous Verification",
        "description": "Unit testing, integration testing, API test clients, deterministic fixtures, and test coverage metrics.",
        "resource_url": "https://docs.pytest.org/en/stable/",
        "recommended_exercises": [
            "Implement parameterized regression tests for edge cases",
            "Build automated end-to-end integration tests using mock external services",
        ],
        "benchmark_level_4": "Consistent test-driven practices, test isolation, mock abstractions, and regression suites.",
    },
    {
        "id": "kb_react_01",
        "topic": "React",
        "category": "Frontend",
        "title": "Component-Driven Architecture & State Management",
        "description": "Modern React hooks, state synchronization, memoization, accessible forms, and modular CSS integration.",
        "resource_url": "https://react.dev/learn",
        "recommended_exercises": [
            "Build reusable data-table components with loading and error boundaries",
            "Refactor prop-drilling into clean context and custom hook patterns",
        ],
        "benchmark_level_4": "Deep understanding of render lifecycles, reconciliation, hooks optimization, and clean component interfaces.",
    },
    {
        "id": "kb_docker_01",
        "topic": "Docker",
        "category": "DevOps",
        "title": "Containerization & Multi-Stage Production Builds",
        "description": "Dockerfiles, multi-stage builds, non-root container users, volume mounts, and container health checks.",
        "resource_url": "https://docs.docker.com/get-started/",
        "recommended_exercises": [
            "Create an optimized multi-stage Docker build for a FastAPI + PostgreSQL service",
            "Configure Docker Compose for local development with healthcheck dependencies",
        ],
        "benchmark_level_3": "Ability to containerize backend and frontend services, manage environment variables, and structure compose environments.",
    },
]


class SkillKnowledgeRetriever:
    """In-memory TF-IDF semantic knowledge retriever."""

    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = documents
        self._vectorizer = None
        self._doc_vectors = None
        self._is_ready = False
        self._initialize_index()

    def _initialize_index(self) -> None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            corpus = [
                f"{doc['topic']} {doc['category']} {doc['title']} {doc['description']} "
                f"{' '.join(doc.get('recommended_exercises', []))} {doc.get('benchmark_level_4', '')}"
                for doc in self.documents
            ]
            self._vectorizer = TfidfVectorizer(stop_words="english", lowercase=True)
            self._doc_vectors = self._vectorizer.fit_transform(corpus)
            self._is_ready = True
        except Exception:
            self._is_ready = False

    def retrieve(self, query: str, top_k: int = 2) -> list[dict[str, Any]]:
        """Retrieve top relevant external knowledge documents for a given skill or goal."""
        if not query or not self.documents:
            return []

        if self._is_ready and self._vectorizer and self._doc_vectors is not None:
            try:
                from sklearn.metrics.pairwise import cosine_similarity
                query_vec = self._vectorizer.transform([query])
                scores = cosine_similarity(query_vec, self._doc_vectors)[0]
                ranked_indices = scores.argsort()[::-1]

                results = []
                for idx in ranked_indices[:top_k]:
                    if scores[idx] > 0.05:
                        doc = dict(self.documents[idx])
                        doc["similarity_score"] = round(float(scores[idx]), 3)
                        doc["source_type"] = "external_curated_knowledge"
                        results.append(doc)
                if results:
                    return results
            except Exception:
                pass

        # Fallback keyword match
        normalized = query.lower()
        matched = [
            {**doc, "similarity_score": 1.0, "source_type": "external_curated_knowledge"}
            for doc in self.documents
            if doc["topic"].lower() in normalized or doc["category"].lower() in normalized
        ]
        return matched[:top_k]


# Global retriever instance
retriever = SkillKnowledgeRetriever(CURATED_KNOWLEDGE_BASE)


def get_external_skill_guidance(skill_name: str) -> dict[str, Any] | None:
    """Retrieve external learning guidance for a skill, respecting candidate facts separation."""
    results = retriever.retrieve(skill_name, top_k=1)
    if results:
        return results[0]
    return None
