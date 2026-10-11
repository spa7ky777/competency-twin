"""Generate the editable prototype curriculum seed file.

Run this only when changing the academic prototype taxonomy. The generated JSON
is what the application reads at startup; no curriculum is hardcoded in the UI.
"""

import json
from pathlib import Path


CURRICULUM = [
    ("ADA", "Analysis and Design of Algorithms", [
        ["Algorithm Analysis", "Asymptotic Notations", "Time and Space Complexity", "Recurrence Relations"],
        ["Divide and Conquer", "Binary Search", "Merge Sort", "Quick Sort"],
        ["Greedy Algorithms", "Minimum Spanning Trees", "Prim's Algorithm", "Kruskal's Algorithm", "Huffman Coding"],
        ["Dynamic Programming", "0/1 Knapsack", "Longest Common Subsequence", "Matrix Chain Multiplication"],
        ["Graph Algorithms", "BFS and DFS", "Shortest Path Algorithms", "Dijkstra's Algorithm", "Backtracking"],
    ]),
    ("DBMS", "Database Management Systems", [
        ["Database Fundamentals", "DBMS Architecture", "Data Models", "ER Model", "Relational Model"],
        ["Relational Algebra", "SQL Basics", "SQL Queries", "Joins", "Aggregate Functions", "Nested Queries"],
        ["Functional Dependencies", "Normalization", "1NF", "2NF", "3NF", "BCNF"],
        ["Transactions", "ACID Properties", "Concurrency Control", "Serializability", "Deadlocks"],
        ["Indexing", "B-Trees", "Hashing", "Query Processing", "Database Recovery"],
    ]),
    ("AI", "Artificial Intelligence", [
        ["Introduction to Artificial Intelligence", "Intelligent Agents", "Problem Solving", "State Space Representation", "Search Problems"],
        ["Uninformed Search", "BFS", "DFS", "Uniform Cost Search", "Informed Search", "A* Algorithm"],
        ["Knowledge Representation", "Propositional Logic", "Predicate Logic", "Inference", "Rule-Based Systems"],
        ["Uncertainty in AI", "Probability", "Bayesian Reasoning", "Bayesian Networks", "Decision Making"],
        ["Machine Learning Basics", "Supervised Learning", "Unsupervised Learning", "Reinforcement Learning", "AI Applications"],
    ]),
    ("DMS", "Discrete Mathematical Structures", [
        ["Set Theory", "Relations", "Functions", "Mathematical Induction", "Proof Techniques"],
        ["Logic", "Propositional Logic", "Predicate Logic", "Boolean Algebra", "Logical Equivalence"],
        ["Counting Principles", "Permutations", "Combinations", "Pigeonhole Principle", "Recurrence Relations"],
        ["Graph Theory", "Graph Representations", "Trees", "Graph Traversal", "Connectivity"],
        ["Algebraic Structures", "Groups", "Subgroups", "Rings", "Boolean Structures"],
    ]),
    ("MONGO", "Mongo DB", [
        ["Introduction to NoSQL", "MongoDB Architecture", "Documents and Collections", "BSON", "MongoDB Installation and Setup"],
        ["CRUD Operations", "Insert Operations", "Query Operations", "Update Operations", "Delete Operations"],
        ["MongoDB Operators", "Comparison Operators", "Logical Operators", "Array Operations", "Projection"],
        ["Indexing", "Aggregation", "Aggregation Pipeline", "Data Modeling", "Embedded Documents and References"],
        ["MongoDB Schema Design", "Replication", "Sharding", "Transactions", "MongoDB Security"],
    ]),
    ("BIOENG", "Biology for Engineers", [
        ["Introduction to Biology", "Cell Structure", "Cell Organelles", "Biomolecules", "Cellular Functions"],
        ["Genetics", "DNA", "RNA", "Gene Expression", "Genetic Engineering"],
        ["Biotechnology", "Recombinant DNA Technology", "PCR", "Genetic Modification", "Applications of Biotechnology"],
        ["Biomimicry", "Biological Systems and Engineering", "Bio-inspired Design", "Artificial Organs", "Medical Engineering"],
        ["Environmental Biotechnology", "Renewable Biological Resources", "Waste Treatment", "Biofuels", "Sustainable Engineering"],
    ]),
]


def competencies(topic: str) -> list[dict]:
    return [
        {"name": f"Explain {topic}", "description": f"Explain the core concepts, terminology, and purpose of {topic}.", "order_index": 1},
        {"name": f"Apply {topic}", "description": f"Apply {topic} to analyse and solve an appropriate problem.", "order_index": 2},
    ]


def build_seed() -> dict:
    subjects = []
    for subject_index, (code, name, unit_topics) in enumerate(CURRICULUM, start=1):
        units = []
        for unit_index, topics in enumerate(unit_topics, start=1):
            units.append(
                {
                    "title": f"Unit {unit_index}",
                    "description": f"{name} — Unit {unit_index}",
                    "order_index": unit_index,
                    "topics": [
                        {
                            "title": topic,
                            "description": f"Prototype topic: {topic}",
                            "order_index": topic_index,
                            "competencies": competencies(topic),
                        }
                        for topic_index, topic in enumerate(topics, start=1)
                    ],
                }
            )
        subjects.append(
            {
                "code": code,
                "name": name,
                "description": f"Prototype academic domain: {name}. This curriculum is editable in the seed JSON or trainer UI.",
                "order_index": subject_index,
                "is_active": True,
                "units": units,
            }
        )
    return {
        "users": [
            {"name": "Demo Student", "email": "student@demo.local", "role": "student"},
            {"name": "Demo Trainer", "email": "trainer@demo.local", "role": "trainer"},
            {"name": "Demo Student 2", "email": "student2@demo.local", "role": "student"},
        ],
        "subjects": subjects,
    }


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "data" / "seed" / "seed_subjects.json"
    target.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}")
