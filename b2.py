
# QUESTION B2.1 – B2.4
# Adversarial data testing and SQL injection

import csv
import sqlite3
import os

# --------------------------------
# PART 1: CREATE DIFFERENT FILES
# --------------------------------

# File with a missing column
with open("missing_column.csv", "w", newline="") as file:
    file.write("station,date\nAdyar,2026-10-01\n")

# File with a wrong delimiter
with open("wrong_delimiter.csv", "w") as file:
    file.write("station;date;pm25\nAdyar;2026-10-01;48\n")

# File with a different encoding
with open("different_encoding.csv", "w", encoding="utf-16") as file:
    file.write("station,date,pm25\nAdyar,2026-10-01,48\n")

# Empty file
open("empty.csv", "w").close()


# --------------------------------
# PART 2: TEST THE FILES
# --------------------------------

def test_file(filename, encoding="utf-8"):
    print("\nTesting:", filename)

    try:
        with open(filename, "r", encoding=encoding) as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                print("Error: File is empty.")
                return

            required = {"station", "date", "pm25"}

            if not required.issubset(set(reader.fieldnames)):
                print("Error: Required column is missing.")
                return

            rows = list(reader)

            if not rows:
                print("No data available.")
            else:
                print("File read successfully:", rows)

    except UnicodeError:
        print("Error: File encoding is different.")

    except Exception as error:
        print("Error:", error)


test_file("missing_column.csv")
test_file("wrong_delimiter.csv")
test_file("different_encoding.csv", "utf-8")
test_file("different_encoding.csv", "utf-16")
test_file("empty.csv")


# --------------------------------
# PART 3: SQL DATABASE
# --------------------------------

readings = [
    ("Adyar", "2026-10-01", 48.0),
    ("Guindy", "2026-10-01", 95.0),
    ("Guindy", "2026-10-03", 121.0),
    ("Adyar", "2026-10-04", 60.0)
]

con = sqlite3.connect(":memory:")
cur = con.cursor()

cur.execute("""
CREATE TABLE aq (
    station TEXT,
    day TEXT,
    pm25 REAL
)
""")

# TODO 1: Insert all readings using one executemany call
cur.executemany(
    "INSERT INTO aq VALUES (?, ?, ?)",
    readings
)

con.commit()


# TODO 2: Parameterised SELECT query
def station_average(name):
    cur.execute(
        "SELECT AVG(pm25) FROM aq WHERE station = ?",
        (name,)
    )

    result = cur.fetchone()
    return result[0]


print("\nStation averages:")
print(station_average("Adyar"), station_average("Guindy"))

# SQL injection attempt
print("Injection attempt:")
print(station_average("Adyar' OR '1'='1"))


# --------------------------------
# PART 4: SHOW UNSAFE SQL
# --------------------------------

unsafe_name = "Adyar' OR '1'='1"

unsafe_query = (
    "SELECT AVG(pm25) FROM aq WHERE station = '"
    + unsafe_name + "'"
)

print("\nUnsafe SQL query:")
print(unsafe_query)

cur.execute(unsafe_query)
print("Unsafe query result:", cur.fetchone()[0])


# --------------------------------
# PART 5: SENTIMENT TESTING
# --------------------------------

POSITIVE = {"good", "clean", "fast", "helpful", "improved"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
NEGATORS = {"not", "never", "no"}


def score(text):
    words = text.lower().replace(".", " ").replace(",", " ").split()
    total = 0

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


test_complaints = [
    "The roads are clean.",
    "The air is bad.",
    "The service is not good.",
    "The pollution is never bad.",
    "The road is not clean but the bus is fast.",
    "The service is good but the road is dirty.",
    "The service is not not good."
]

print("\nSentiment test results:")

for complaint in test_complaints:
    print(label(complaint), "|", complaint)


con.close()
print("\nB2 completed successfully.")
