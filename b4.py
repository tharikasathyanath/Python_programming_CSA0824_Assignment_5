
# QUESTION B4.1 – B4.3
# Sentiment analysis, summarisation and database indexing

import sqlite3
import time
import re
from collections import Counter


# --------------------------------
# PART 1: SENTIMENT SCORER
# --------------------------------

POSITIVE = {"good", "clean", "fast", "helpful", "improved"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
NEGATORS = {"not", "never", "no"}


def score(text):
    words = text.lower().replace(".", " ").replace(",", " ").split()
    total = 0

    # TODO 1: Find each word's value and flip it after a negator
    for i, word in enumerate(words):
        value = 0

        if word in POSITIVE:
            value = 1
        elif word in NEGATIVE:
            value = -1

        if i > 0 and words[i - 1] in NEGATORS:
            value = -value

        total += value

    return total


def label(text):
    result = score(text)

    if result > 0:
        return "positive"
    elif result < 0:
        return "negative"
    else:
        return "neutral"


# --------------------------------
# PART 2: 50 CITIZEN COMPLAINTS
# --------------------------------

base_complaints = [
    ("The roads are clean and the air is good.", "positive"),
    ("Smoke is bad and the air is dirty.", "negative"),
    ("The bus service is fast and helpful.", "positive"),
    ("The factory smoke is bad and harmful.", "negative"),
    ("The road is not clean.", "negative"),
    ("The air quality has improved.", "positive"),
    ("The public service is slow and rude.", "negative"),
    ("The transport service is good.", "positive"),
    ("The pollution is bad and the road is dirty.", "negative"),
    ("The staff are helpful and the service is good.", "positive")
]

complaints = []
manual_labels = []

# Create 50 complaint records from the 10 sample complaints
for repeat in range(5):
    for complaint, correct_label in base_complaints:
        complaints.append(
            complaint + f" Report number {repeat + 1}."
        )
        manual_labels.append(correct_label)


# --------------------------------
# PART 3: COMPARE SENTIMENT LABELS
# --------------------------------

agree_count = 0

print("SENTIMENT RESULTS")
print("-----------------")

for i, complaint in enumerate(complaints):
    predicted = label(complaint)
    actual = manual_labels[i]

    if predicted == actual:
        agree_count += 1

    print(
        i + 1,
        "| Predicted:", predicted,
        "| Manual:", actual,
        "|", complaint
    )

accuracy = (agree_count / len(complaints)) * 100

print("\nTotal complaints:", len(complaints))
print("Correct labels:", agree_count)
print("Agreement percentage:", round(accuracy, 2), "%")


# --------------------------------
# PART 4: EXTRACTIVE SUMMARISER
# --------------------------------

STOP_WORDS = {
    "the", "is", "are", "and", "a", "an", "of", "to",
    "in", "was", "were", "for", "on", "with", "report",
    "number"
}


def summarise(text, number_of_sentences=2):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    words = re.findall(r"\b[a-z]+\b", text.lower())

    important_words = [
        word for word in words
        if word not in STOP_WORDS
    ]

    frequency = Counter(important_words)

    sentence_scores = []

    for index, sentence in enumerate(sentences):
        sentence_words = re.findall(r"\b[a-z]+\b", sentence.lower())

        sentence_score = sum(
            frequency[word]
            for word in sentence_words
            if word not in STOP_WORDS
        )

        sentence_scores.append((sentence_score, index, sentence))

    selected = sorted(
        sentence_scores,
        key=lambda item: item[0],
        reverse=True
    )[:number_of_sentences]

    selected.sort(key=lambda item: item[1])

    return " ".join(item[2] for item in selected)


all_complaints_text = " ".join(complaints)

print("\nEXTRACTIVE SUMMARY")
print("------------------")
print(summarise(all_complaints_text, 5))


# --------------------------------
# PART 5: DATABASE AND INDEX TEST
# --------------------------------

con = sqlite3.connect("air_quality_b4.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station TEXT,
    day TEXT,
    pm25 REAL
)
""")

cur.execute("DELETE FROM readings")

# Insert sample readings for testing
data = []

for station_number in range(1, 121):
    for day_number in range(1, 31):
        station = f"Station_{station_number}"
        day = f"2026-10-{day_number:02d}"

        for hour in range(15):
            pm25 = 30 + ((station_number + day_number + hour) % 100)
            data.append((station, day, pm25))

cur.executemany(
    "INSERT INTO readings (station, day, pm25) VALUES (?, ?, ?)",
    data
)

con.commit()

print("\nTotal database readings:", len(data))


# Query before creating the index
query = """
SELECT AVG(pm25)
FROM readings
WHERE station = ? AND day = ?
"""

start = time.perf_counter()

for i in range(100):
    cur.execute(query, ("Station_50", "2026-10-15"))
    cur.fetchone()

time_without_index = time.perf_counter() - start

print(
    "Time without index:",
    round(time_without_index, 6),
    "seconds"
)


# Create index on station and day
cur.execute("""
CREATE INDEX IF NOT EXISTS idx_station_day
ON readings(station, day)
""")

con.commit()


# Query after creating the index
start = time.perf_counter()

for i in range(100):
    cur.execute(query, ("Station_50", "2026-10-15"))
    cur.fetchone()

time_with_index = time.perf_counter() - start

print(
    "Time with index:",
    round(time_with_index, 6),
    "seconds"
)

if time_with_index > 0:
    improvement = (
        time_without_index / time_with_index
    )

    print("Approximate speed improvement:", round(improvement, 2), "times")


# --------------------------------
# PART 6: FINAL ENGINEERING DECISION
# --------------------------------

print("\nFINAL ENGINEERING DECISION")
print("--------------------------")

print("""
1. Store all air-quality readings in an SQLite database.
2. Use CSV files for receiving station data.
3. Clean missing, negative and impossible readings before storage.
4. Convert all temperatures into Celsius.
5. Use SQL GROUP BY for daily and monthly reports.
6. Create an index on station and day for faster searching.
7. Use charts to understand pollution trends.
8. Use sentiment scoring and summarisation for citizen complaints.
9. For a large number of complaints, a trained machine-learning
   model may provide better accuracy than a simple word list.
10. Regularly test, measure and improve the system.
""")

con.close()

print("B4 completed successfully.")
