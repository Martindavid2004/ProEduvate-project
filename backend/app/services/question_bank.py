# question_bank.py
"""Categorized dynamic question bank for assignments/quizzes.

Replaces the old static hardcoded questions ("What is 2+2?", "Capital of
France") that repeated identically on every attempt with:

- A structured bank organized under defined categories
  (Grammar, General Knowledge, Technical, Logical Reasoning).
- Dynamic random selection: every attempt draws a fresh, unique set of
  questions from the pool, so two attempts never see the same paper.

The bank is the deterministic floor for quiz generation: the LLM can expand
it (see chatbot_routes.generate_quiz), but the app must never fall back to
repeating trivial static questions again.
"""

import random

# ---------------------------------------------------------------------------
# Question bank: category -> list of question dicts
# Every question carries a "category" tag used by the frontend badge and by
# the category-filtered selection below.
# ---------------------------------------------------------------------------

QUESTION_BANK = {
    "Grammar": [
        {"question": "Choose the correct sentence.", "options": ["He don't like coffee.", "He doesn't likes coffee.", "He doesn't like coffee.", "He not like coffee."], "correct_answer": "He doesn't like coffee.", "explanation": "Third-person singular subjects take 'doesn't' + base verb form."},
        {"question": "Identify the adverb: 'She sings beautifully.'", "options": ["She", "sings", "beautifully", "None"], "correct_answer": "beautifully", "explanation": "'Beautifully' modifies the verb 'sings', describing how the action is done."},
        {"question": "What is the past tense of 'write'?", "options": ["writed", "wrote", "written", "writing"], "correct_answer": "wrote", "explanation": "'Write' is an irregular verb: write -> wrote -> written."},
        {"question": "Which word is a synonym of 'diligent'?", "options": ["Lazy", "Hardworking", "Careless", "Rude"], "correct_answer": "Hardworking", "explanation": "'Diligent' means showing persistent, careful effort - i.e. hardworking."},
        {"question": "Pick the correct article: '___ honest man'.", "options": ["a", "an", "the", "no article"], "correct_answer": "an", "explanation": "'Honest' starts with a vowel SOUND (the 'h' is silent), so 'an' is used."},
        {"question": "Which sentence uses the correct preposition?", "options": ["She is good in mathematics.", "She is good at mathematics.", "She is good on mathematics.", "She is good for mathematics."], "correct_answer": "She is good at mathematics.", "explanation": "The collocation is 'good at + subject/skill'."},
        {"question": "Identify the subject in: 'The books on the table belong to Riya.'", "options": ["The table", "The books", "Riya", "belong"], "correct_answer": "The books", "explanation": "The verb 'belong' agrees with 'The books' - the doer of the action."},
        {"question": "Choose the correctly punctuated sentence.", "options": ["Its raining outside.", "It's raining outside.", "Its' raining outside.", "It is'nt raining outside."], "correct_answer": "It's raining outside.", "explanation": "\"It's\" is the contraction of 'it is'; 'its' is possessive."},
        {"question": "What is the antonym of 'scarce'?", "options": ["Rare", "Plentiful", "Limited", "Sparse"], "correct_answer": "Plentiful", "explanation": "'Scarce' means in short supply; its opposite is 'plentiful'."},
        {"question": "Which sentence is in the passive voice?", "options": ["The chef cooked the meal.", "The meal was cooked by the chef.", "The chef is cooking.", "Cook the meal now."], "correct_answer": "The meal was cooked by the chef.", "explanation": "Passive voice: subject receives the action ('was cooked') instead of performing it."},
        {"question": "Select the correctly spelled word.", "options": ["Recieve", "Receive", "Receeve", "Receve"], "correct_answer": "Receive", "explanation": "Rule 'i before e except after c': receive."},
        {"question": "Which is a compound sentence?", "options": ["Although it rained, we played.", "It rained, so we stayed inside.", "Raining heavily, we left.", "We left early because of rain."], "correct_answer": "It rained, so we stayed inside.", "explanation": "A compound sentence joins two independent clauses with a coordinating conjunction ('so')."},
        {"question": "Identify the gerund: 'Swimming is my favourite hobby.'", "options": ["is", "my", "Swimming", "favourite"], "correct_answer": "Swimming", "explanation": "A gerund is a verb+ing form used as a noun - here, the subject."},
        {"question": "Choose the correct comparative form.", "options": ["This is more better.", "This is better.", "This is gooder.", "This is most good."], "correct_answer": "This is better.", "explanation": "'Good' has the irregular comparative 'better'; never 'more better'."},
        {"question": "Which word completes the sentence: 'Neither of the answers ___ correct.'", "options": ["are", "is", "were", "have"], "correct_answer": "is", "explanation": "'Neither' is singular, so the verb is singular ('is')."},
    ],
    "General Knowledge": [
        {"question": "Which planet is known as the Red Planet?", "options": ["Venus", "Mars", "Jupiter", "Mercury"], "correct_answer": "Mars", "explanation": "Iron oxide (rust) on its surface gives Mars its reddish appearance."},
        {"question": "Who wrote the play 'Macbeth'?", "options": ["Charles Dickens", "William Shakespeare", "George Orwell", "Jane Austen"], "correct_answer": "William Shakespeare", "explanation": "'Macbeth' is a tragedy written by Shakespeare around 1606."},
        {"question": "What is the largest ocean on Earth?", "options": ["Atlantic Ocean", "Indian Ocean", "Pacific Ocean", "Arctic Ocean"], "correct_answer": "Pacific Ocean", "explanation": "The Pacific covers about one-third of the Earth's surface - the largest ocean."},
        {"question": "Which gas do plants primarily absorb for photosynthesis?", "options": ["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"], "correct_answer": "Carbon dioxide", "explanation": "Plants take in CO2 and release oxygen during photosynthesis."},
        {"question": "The Great Wall is located in which country?", "options": ["Japan", "India", "China", "Mongolia"], "correct_answer": "China", "explanation": "The Great Wall of China was built across China's northern borders."},
        {"question": "Which is the smallest prime number?", "options": ["0", "1", "2", "3"], "correct_answer": "2", "explanation": "1 is not prime by definition; 2 is the smallest (and only even) prime."},
        {"question": "Which element has the chemical symbol 'Au'?", "options": ["Silver", "Gold", "Aluminium", "Argon"], "correct_answer": "Gold", "explanation": "'Au' comes from the Latin word for gold, 'aurum'."},
        {"question": "How many continents are there on Earth?", "options": ["5", "6", "7", "8"], "correct_answer": "7", "explanation": "Africa, Antarctica, Asia, Europe, North America, Australia, South America."},
        {"question": "Which device is used to measure atmospheric pressure?", "options": ["Thermometer", "Barometer", "Hygrometer", "Altimeter"], "correct_answer": "Barometer", "explanation": "A barometer measures air pressure; invented by Torricelli."},
        {"question": "The headquarters of the United Nations is located in:", "options": ["Geneva", "Paris", "New York City", "London"], "correct_answer": "New York City", "explanation": "The UN headquarters has been in New York City since 1952."},
        {"question": "Which data structure works on FIFO (First In First Out)?", "options": ["Stack", "Queue", "Tree", "Graph"], "correct_answer": "Queue", "explanation": "A queue serves elements in the order they arrived (FIFO); stacks are LIFO."},
        {"question": "Which country hosts the Taj Mahal?", "options": ["Pakistan", "India", "Bangladesh", "Nepal"], "correct_answer": "India", "explanation": "The Taj Mahal is in Agra, India, built by Shah Jahan."},
        {"question": "Light travels fastest through which medium?", "options": ["Water", "Glass", "Vacuum", "Diamond"], "correct_answer": "Vacuum", "explanation": "Light moves at its maximum speed (~3x10^8 m/s) in a vacuum."},
        {"question": "Which blood type is known as the universal donor?", "options": ["A", "B", "AB", "O negative"], "correct_answer": "O negative", "explanation": "O negative red cells lack A, B and RhD antigens, so they can be given to almost anyone."},
        {"question": "Who is credited with inventing the World Wide Web?", "options": ["Bill Gates", "Tim Berners-Lee", "Steve Jobs", "Alan Turing"], "correct_answer": "Tim Berners-Lee", "explanation": "Tim Berners-Lee invented the Web at CERN in 1989."},
    ],
    "Technical": [
        {"question": "What does 'HTTP' stand for?", "options": ["HyperText Transfer Protocol", "High Transfer Text Protocol", "HyperText Transport Program", "Host Transfer Text Protocol"], "correct_answer": "HyperText Transfer Protocol", "explanation": "HTTP is the application protocol used to transfer web documents."},
        {"question": "Which SQL command retrieves data from a table?", "options": ["GET", "SELECT", "FETCH", "READ"], "correct_answer": "SELECT", "explanation": "SELECT queries rows from database tables."},
        {"question": "What is the time complexity of binary search on a sorted array?", "options": ["O(n)", "O(n log n)", "O(log n)", "O(1)"], "correct_answer": "O(log n)", "explanation": "Each comparison halves the search space, giving logarithmic complexity."},
        {"question": "Which of these is NOT a programming paradigm?", "options": ["Object-oriented", "Functional", "Procedural", "Alphabetical"], "correct_answer": "Alphabetical", "explanation": "Alphabetical is an ordering scheme, not a paradigm."},
        {"question": "In Python, which data type is immutable?", "options": ["list", "dict", "tuple", "set"], "correct_answer": "tuple", "explanation": "Tuples cannot be modified after creation; lists, dicts and sets can."},
        {"question": "What does 'API' stand for?", "options": ["Application Programming Interface", "Applied Program Integration", "Automated Programming Input", "Application Process Index"], "correct_answer": "Application Programming Interface", "explanation": "An API defines how software components communicate with each other."},
        {"question": "Which normalization form removes partial dependencies on composite keys?", "options": ["1NF", "2NF", "3NF", "BCNF"], "correct_answer": "2NF", "explanation": "2NF eliminates partial dependencies; 3NF goes further and removes transitive dependencies."},
        {"question": "Which HTTP status code means 'Not Found'?", "options": ["200", "301", "404", "500"], "correct_answer": "404", "explanation": "4xx codes are client errors; 404 indicates the resource was not found."},
        {"question": "Which structure uses LIFO (Last In First Out) ordering?", "options": ["Queue", "Stack", "Linked list", "Heap"], "correct_answer": "Stack", "explanation": "Push/pop happen at the same end of a stack, so the last item in is the first out."},
        {"question": "In OOP, wrapping data and methods into a single unit is called:", "options": ["Inheritance", "Polymorphism", "Encapsulation", "Abstraction"], "correct_answer": "Encapsulation", "explanation": "Encapsulation bundles state and behavior and restricts direct access to internals."},
        {"question": "Which of the following is a version control system?", "options": ["Docker", "Git", "Jenkins", "Kubernetes"], "correct_answer": "Git", "explanation": "Git tracks changes to source code; Docker/Jenkins/Kubernetes serve other purposes."},
        {"question": "What will len([1, 2, 3, 4]) return in Python?", "options": ["3", "4", "5", "Error"], "correct_answer": "4", "explanation": "The list has four elements, so len() returns 4."},
        {"question": "Which key is used to link two relational tables?", "options": ["Primary key of the child table", "Foreign key", "Unique key of any table", "Composite hash"], "correct_answer": "Foreign key", "explanation": "A foreign key in one table references the primary key of another, creating the link."},
        {"question": "CSS stands for:", "options": ["Computer Style Sheets", "Cascading Style Sheets", "Creative Style System", "Coded Style Syntax"], "correct_answer": "Cascading Style Sheets", "explanation": "CSS describes the presentation of HTML documents; 'cascading' refers to rule precedence."},
        {"question": "Which sorting algorithm has the best worst-case time complexity?", "options": ["Quick sort", "Bubble sort", "Merge sort", "Insertion sort"], "correct_answer": "Merge sort", "explanation": "Merge sort guarantees O(n log n) even in the worst case; quicksort can degrade to O(n^2)."},
    ],
    "Logical Reasoning": [
        {"question": "Find the next number: 3, 6, 12, 24, ___", "options": ["30", "36", "48", "42"], "correct_answer": "48", "explanation": "Each term doubles the previous one: 24 * 2 = 48."},
        {"question": "If ALL roses are flowers and some flowers fade quickly, which conclusion is valid?", "options": ["All roses fade quickly", "Some roses fade quickly", "No roses fade quickly", "None of these conclusions is certain"], "correct_answer": "None of these conclusions is certain", "explanation": "The 'some flowers' group may not include any roses, so none of the claims follows certainly."},
        {"question": "Odd one out: 2, 3, 5, 7, 9, 11", "options": ["5", "7", "9", "11"], "correct_answer": "9", "explanation": "All others are prime; 9 = 3 x 3 is composite."},
        {"question": "A is older than B. C is younger than B. Who is the oldest?", "options": ["A", "B", "C", "Cannot be determined"], "correct_answer": "A", "explanation": "Ordering gives A > B > C, so A is the oldest."},
        {"question": "Complete the series: A, C, F, J, O, ___", "options": ["T", "U", "S", "V"], "correct_answer": "U", "explanation": "Gaps grow by one letter each step: +2, +3, +4, +5, +6 -> O + 6 = U."},
        {"question": "If CODE is written as DPEF, how is FILE written?", "options": ["GJMF", "GJLE", "GJNF", "HJMF"], "correct_answer": "GJMF", "explanation": "Each letter shifts forward by one: F->G, I->J, L->M, E->F."},
        {"question": "Pointing to a photo, Ravi says, 'He is the son of my grandfather's only son.' Who is in the photo?", "options": ["His father", "His brother", "Himself", "His uncle"], "correct_answer": "Himself", "explanation": "Grandfather's only son = Ravi's father; the father's son is Ravi himself (or a brother, but the standard answer is himself)."},
        {"question": "Find the missing number: 4, 9, 16, 25, ___", "options": ["30", "36", "40", "49"], "correct_answer": "36", "explanation": "The terms are perfect squares: 2^2, 3^2, 4^2, 5^2, next is 6^2 = 36."},
        {"question": "Statement: Every library has books. The school building has a library. Conclusion: The school building has books.", "options": ["Valid", "Invalid", "Partially valid", "Cannot say"], "correct_answer": "Valid", "explanation": "If every library has books and the building contains a library, the building must contain books."},
        {"question": "In a race, you overtake the person in second place. What position are you in now?", "options": ["First", "Second", "Third", "Cannot say"], "correct_answer": "Second", "explanation": "Overtaking the runner in second place puts you in second, not first."},
        {"question": "If in a certain language ROSE is coded 6821 and CHAIR is 73456, what is SEARCH coded as?", "options": ["241736", "214673", "214763", "216473"], "correct_answer": "214763", "explanation": "Map letters to digits from the two codes: S=2, E=1, A=4, R=6, C=7, H=3 -> SEARCH = 214763."},
        {"question": "Which figure completes the analogy? Book : Author :: Painting : ___", "options": ["Museum", "Artist", "Canvas", "Colour"], "correct_answer": "Artist", "explanation": "An author creates a book as an artist creates a painting."},
        {"question": "A clock shows 3:15. What is the angle between the hour and minute hands?", "options": ["0 degrees", "7.5 degrees", "15 degrees", "30 degrees"], "correct_answer": "7.5 degrees", "explanation": "Hour hand at 3:15 is at 97.5 degrees, minute hand at 90 degrees; difference 7.5 degrees."},
        {"question": "If some cats are black and all black things absorb heat, then:", "options": ["All cats absorb heat", "Some cats absorb heat (via their black fur)", "No cats absorb heat", "Cats never absorb heat"], "correct_answer": "Some cats absorb heat (via their black fur)", "explanation": "Only the black cats are guaranteed to be in the heat-absorbing group."},
        {"question": "Find the next term: 2, 5, 10, 17, 26, ___", "options": ["35", "36", "37", "38"], "correct_answer": "37", "explanation": "Each term is n^2 + 1: 1+1, 4+1, 9+1, 16+1, 25+1, next 36+1 = 37."},
    ],
}

# Canonical category order used by pickers in the UI.
CATEGORIES = list(QUESTION_BANK.keys())


def get_categories():
    """Return the available question-bank categories."""
    return CATEGORIES


def bank_size():
    """Total number of questions available across all categories."""
    return sum(len(qs) for qs in QUESTION_BANK.values())


def _normalize_question(q, category=None):
    """Copy a bank question into the wire format used by quizzes/assignments."""
    out = {
        "question": q.get("question"),
        "options": list(q.get("options") or []),
        "correct_answer": q.get("correct_answer"),
        "explanation": q.get("explanation", ""),
        "category": q.get("category") or category,
    }
    return out


def pick_questions(num_questions=10, categories=None, rng=None):
    """Dynamically select a random, unique set of questions.

    - Every call returns a different selection and order (true randomization,
      no static repetition between attempts).
    - `categories` optionally restricts the pool to specific categories
      (e.g. ["Technical", "Grammar"]).
    - Questions are de-duplicated by normalized question text.
    - Returns at most num_questions items; fewer only if the pool itself is
      smaller than the request.
    """
    try:
        num_questions = max(1, int(num_questions or 10))
    except (TypeError, ValueError):
        num_questions = 10

    rng = rng or random.Random()

    if categories:
        wanted = {str(c).strip().lower() for c in categories}
        pool_pairs = [(cat, qs) for cat, qs in QUESTION_BANK.items() if cat.lower() in wanted]
    else:
        pool_pairs = list(QUESTION_BANK.items())

    # Flatten with the owning category tagged, then shuffle so selection is
    # random per attempt (never the same head of the list twice).
    pool = []
    for cat, qs in pool_pairs:
        for q in qs:
            pool.append(_normalize_question(q, category=cat))

    rng.shuffle(pool)

    seen = set()
    selected = []
    for q in pool:
        text = (q.get("question") or "").strip().lower()
        if not text or text in seen:
            continue
        seen.add(text)
        selected.append(q)
        if len(selected) >= num_questions:
            break

    return selected


def pick_mixed_questions(num_questions=10, rng=None):
    """Pick questions spread across ALL categories (balanced mix).

    Round-robins over shuffled per-category decks so a mixed paper always
    contains a spread of categories instead of a random clump.
    """
    try:
        num_questions = max(1, int(num_questions or 10))
    except (TypeError, ValueError):
        num_questions = 10

    rng = rng or random.Random()

    decks = []
    for cat, qs in QUESTION_BANK.items():
        deck = [_normalize_question(q, category=cat) for q in qs]
        rng.shuffle(deck)
        decks.append(deck)

    selected = []
    seen = set()
    i = 0
    while len(selected) < num_questions and decks:
        deck = decks[i % len(decks)]
        if not deck:
            decks.pop(i % len(decks))
            if not decks:
                break
            i = i % max(1, len(decks))
            continue
        q = deck.pop()
        text = (q.get("question") or "").strip().lower()
        if text not in seen:
            seen.add(text)
            selected.append(q)
        i += 1

    return selected[:num_questions]
