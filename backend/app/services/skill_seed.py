"""
Seed the Skill Card System with the nine initial training topics.

This seeds CONTENT (topics/lessons/problems/assessments) ONLY - never any
student progress. It is idempotent: running with existing data is a no-op.
Admins can edit or archive all of it through the admin API.
"""

from ..database import (
    skill_topics_collection,
    skill_lessons_collection,
    skill_problems_collection,
    skill_assessments_collection,
)

TOPIC_DEFS = [
    {"name": "Python", "icon": "code", "description": "Python fundamentals, functions, OOP and standard library for placements."},
    {"name": "SQL", "icon": "database", "description": "Queries, joins, aggregation and database design questions."},
    {"name": "Java", "icon": "file-code", "description": "Core Java, OOP concepts, collections and exception handling."},
    {"name": "C Programming", "icon": "terminal", "description": "Pointers, memory, arrays, strings and control flow."},
    {"name": "DSA", "icon": "network", "description": "Data structures and algorithms: arrays, trees, graphs, complexity."},
    {"name": "Aptitude", "icon": "target", "description": "Numbers, percentages, time-work, probability and shortcuts."},
    {"name": "Logical Reasoning", "icon": "brain", "description": "Series, puzzles, syllogisms, blood relations and patterns."},
    {"name": "Verbal Ability", "icon": "message-square", "description": "Grammar, vocabulary, comprehension and sentence correction."},
    {"name": "Web Development", "icon": "globe", "description": "HTML, CSS, JavaScript, React and REST basics."},
]

LESSON_TEMPLATES = {
    "Python": ["Python Basics and Syntax", "Functions, Lists and Dicts", "OOP and Error Handling"],
    "SQL": ["SELECT, WHERE and ORDER BY", "Joins and Group By", "Normalization and Indexes"],
    "Java": ["Classes, Objects and Constructors", "Collections Framework", "Inheritance and Interfaces"],
    "C Programming": ["Variables, Loops and Arrays", "Pointers and Memory", "Functions and Recursion"],
    "DSA": ["Complexity and Arrays", "Stacks, Queues and Linked Lists", "Trees, Graphs and Searching"],
    "Aptitude": ["Percentages and Ratios", "Time, Speed and Work", "Profit, Loss and Interest"],
    "Logical Reasoning": ["Series and Patterns", "Syllogisms and Relations", "Coding-Decoding and Puzzles"],
    "Verbal Ability": ["Grammar Essentials", "Vocabulary Building", "Reading Comprehension"],
    "Web Development": ["HTML and CSS Layout", "JavaScript Fundamentals", "React and REST APIs"],
}

PROBLEM_TEMPLATES = {
    "Python": [
        {"title": "Sum of Two Numbers", "difficulty": "easy", "description": "Read two integers and print their sum.", "starter": "a = int(input())\nb = int(input())\n# print the sum\n", "cases": [("3\n4", "7"), ("10\n-5", "5")]},
        {"title": "FizzBuzz", "difficulty": "medium", "description": "Print 1..n replacing multiples of 3 with Fizz, of 5 with Buzz, both with FizzBuzz (one per line).", "starter": "n = int(input())\n", "cases": [("5", "1\n2\nFizz\n4\nBuzz"), ("15", "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz")]},
    ],
    "SQL": [
        {"title": "Grade Calculator", "difficulty": "easy", "description": "Print PASS if the marks input is 40 or above, else FAIL (high-level SQL logic practice via simulation).", "starter": "marks = int(input())\n", "cases": [("75", "PASS"), ("39", "FAIL")]},
    ],
    "Java": [
        {"title": "Reverse a Number", "difficulty": "medium", "description": "Read an integer and print its digits reversed (modeled in Python executor practice form).", "starter": "n = input()\n", "cases": [("1234", "4321"), ("100", "1")]},
    ],
    "C Programming": [
        {"title": "Largest of Three", "difficulty": "easy", "description": "Read three integers and print the largest.", "starter": "a = int(input())\nb = int(input())\nc = int(input())\n", "cases": [("1 5 3", "5"), ("9 2 7", "9")]},
    ],
    "DSA": [
        {"title": "Binary Search", "difficulty": "medium", "description": "Given a sorted list (first line, space separated) and a target (second line), print the index or -1.", "starter": "nums = list(map(int, input().split()))\ntarget = int(input())\n", "cases": [("1 3 5 7 9\n7", "3"), ("1 3 5\n4", "-1")]},
    ],
    "Aptitude": [
        {"title": "Percentage Solver", "difficulty": "easy", "description": "Given total and percent, print the amount.", "starter": "total = int(input())\npct = int(input())\n", "cases": [("200\n50", "100")]},
    ],
    "Logical Reasoning": [
        {"title": "Series Next Term", "difficulty": "medium", "description": "Space-separated series in first line; print the next term (arithmetic).", "starter": "nums = list(map(int, input().split()))\n", "cases": [("2 4 6 8", "10")]},
    ],
    "Verbal Ability": [
        {"title": "Word Count", "difficulty": "easy", "description": "Print the number of words in the sentence.", "starter": "s = input()\n", "cases": [("the quick brown fox", "4")]},
    ],
    "Web Development": [
        {"title": "Format Heading", "difficulty": "easy", "description": "Print the input word wrapped as <h1>...</h1>.", "starter": "w = input()\n", "cases": [("Title", "<h1>Title</h1>")]},
    ],
}

ASSESSMENT_TEMPLATES = {
    "Python": [
        {"title": "Python Fundamentals Test", "max_marks": 20, "pass_pct": 40,
         "questions": [
             {"question": "Which keyword defines a function in Python?", "options": ["func", "def", "define", "lambda"], "answer": 1, "marks": 5},
             {"question": "What is the output of 7 // 2 in Python 3?", "options": ["3.5", "3", "4", "2"], "answer": 1, "marks": 5},
             {"question": "Which is a mutable collection?", "options": ["tuple", "str", "list", "int"], "answer": 2, "marks": 5},
             {"question": "Where is a Python KeyError raised?", "options": ["Missing list index", "Missing dict key", "Type mismatch", "Import failure"], "answer": 1, "marks": 5}]},
    ],
    "SQL": [
        {"title": "SQL Core Test", "max_marks": 20, "pass_pct": 40,
         "questions": [
             {"question": "Which clause filters rows BEFORE grouping?", "options": ["HAVING", "WHERE", "ORDER BY", "LIMIT"], "answer": 1, "marks": 5},
             {"question": "JOIN returns matching rows of both tables. Which is this?", "options": ["LEFT JOIN", "FULL JOIN", "INNER JOIN", "CROSS JOIN"], "answer": 2, "marks": 5},
             {"question": "Which removes duplicate values in a SELECT?", "options": ["UNIQUE", "DISTINCT", "FILTER", "GROUP"], "answer": 1, "marks": 5},
             {"question": "COUNT(*) counts...?", "options": ["Distinct rows", "All rows", "Non-null first column", "Columns"], "answer": 1, "marks": 5}]},
    ],
}


def ensure_default_content():
    """Create the 9 topics (with lessons/problems/assessments) if absent."""
    created = 0
    existing = {t["name"] for t in skill_topics_collection.find({}, {"name": 1})}
    for order, topic in enumerate(TOPIC_DEFS):
        if topic["name"] in existing:
            continue
        topic_id = skill_topics_collection.insert_one({
            "name": topic["name"],
            "icon": topic["icon"],
            "description": topic["description"],
            "order": order,
            "archived": False,
            "source": "seed",
            "createdAt": __import__("datetime").datetime.utcnow(),
        }).inserted_id
        created += 1

        for position, lesson_title in enumerate(LESSON_TEMPLATES[topic["name"]]):
            skill_lessons_collection.insert_one({
                "topic_id": topic_id,
                "title": lesson_title,
                "content": (f"{lesson_title} - study notes and worked examples for "
                            f"{topic['name']}. Complete the reading to mark this lesson done."),
                "required": True, "order": position, "source": "seed",
            })

        for problem in PROBLEM_TEMPLATES.get(topic["name"], []):
            skill_problems_collection.insert_one({
                "topic_id": topic_id,
                "title": problem["title"],
                "difficulty": problem["difficulty"],
                "description": problem["description"],
                "starter_code": problem["starter"],
                "required": True,
                "test_cases": [{"input": i, "expectedOutput": o} for i, o in problem["cases"]],
                "source": "seed",
            })

        for assessment in ASSESSMENT_TEMPLATES.get(topic["name"], []):
            skill_assessments_collection.insert_one({
                "topic_id": topic_id,
                "title": assessment["title"],
                "max_marks": assessment["max_marks"],
                "pass_pct": assessment["pass_pct"],
                "required": True,
                "retakes_allowed": 2,
                "questions": assessment["questions"],
                "source": "seed",
            })
    return created
