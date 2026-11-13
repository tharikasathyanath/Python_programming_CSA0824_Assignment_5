
# QUESTION B1.1 – B1.4
# Cleaning, SQLite storage, SQL queries and visualisation

import csv
import sqlite3
import io
import matplotlib.pyplot as plt
from collections import defaultdict
from statistics import mean

# -------------------------------
# PART 1: COMPLETE THE GIVEN CODE
# -------------------------------

RAW = """station,date,pm25
Adyar,2026-10-01,48
Adyar,2026-10-02,NA
Adyar,2026-10-03,
Guindy,2026-10-01,95
Guindy,2026-10-02,-5
Guindy,2026-10-03,121
Adyar,2026-10-04,1200
"""

def load_clean(text):
    """Return valid station, date and PM2.5 readings."""
    rows = []
    reader = csv.DictReader(io.StringIO(text))

    for row in reader:
        value = row["pm25"].strip()

        if value == "" or value.upper() == "NA":
            continue

        try:
            pm25 = float(value)
        except ValueError:
            continue

        if pm25 < 0 or pm25 > 999:
            continue

        rows.append((row["station"], row["date"], pm25))

    return rows


def min_max(values):
    if not values:
        return []

    minimum = min(values)
    maximum = max(values)

    if maximum == minimum:
        return [0.0 for value in values]

    return [round((v - minimum) / (maximum - minimum), 3)
            for v in values]


clean = load_clean(RAW)

print("B1 Complete the Code – Cleaned data:")
print(clean)

print("Min-max normalisation:")
print(min_max([pm for _, _, pm in clean]))

# Expected cleaned data:
# [('Adyar', '2026-10-01', 48.0),
#  ('Guindy', '2026-10-01', 95.0),
#  ('Guindy', '2026-10-03', 121.0)]


# --------------------------------
# PART 2: CREATE A SAMPLE CSV FILE
# --------------------------------

raw_data = [
    ["station", "date", "hour", "pm25", "pm10", "no2", "temperature", "unit"],
    ["Adyar", "2026-10-01", "09:00", "48", "80", "20", "30", "C"],
    ["Adyar", "2026-10-01", "10:00", "55", "90", "25", "31", "C"],
    ["Adyar", "2026-10-02", "09:00", "NA", "85", "22", "32", "C"],
    ["Adyar", "2026-10-02", "10:00", "", "90", "24", "33", "C"],
    ["Guindy", "2026-10-01", "09:00", "95", "150", "45", "86", "F"],
    ["Guindy", "2026-10-01", "10:00", "-5", "140", "40", "87", "F"],
    ["Guindy", "2026-10-02", "09:00", "121", "180", "55", "88", "F"],
    ["Guindy", "2026-10-02", "09:00", "121", "180", "55", "88", "F"],
    ["Velachery", "2026-10-01", "09:00", "1200", "200", "60", "29", "C"]
]

with open("air_quality_raw.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerows(raw_data)

print("\nRaw CSV file created.")


# --------------------------------
# PART 3: CLEAN THE CSV DATA
# --------------------------------

cleaned_rows = []
seen = set()

with open("air_quality_raw.csv", "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        try:
            pm25_text = row["pm25"].strip()
            pm10_text = row["pm10"].strip()
            no2_text = row["no2"].strip()
            temp_text = row["temperature"].strip()

            if pm25_text == "" or pm25_text.upper() == "NA":
                continue

            pm25 = float(pm25_text)
            pm10 = float(pm10_text)
            no2 = float(no2_text)
            temperature = float(temp_text)

            if not (0 <= pm25 <= 999):
                continue

            if not (0 <= pm10 <= 999):
                continue

            if not (0 <= no2 <= 999):
                continue

            # Convert Fahrenheit to Celsius
            if row["unit"].upper() == "F":
                temperature = (temperature - 32) * 5 / 9

            station = row["station"].strip().title()
            date = row["date"].strip()
            hour = row["hour"].strip()

            record = (
                station, date, hour,
                pm25, pm10, no2, round(temperature, 2)
            )

            # Remove duplicate records
            if record not in seen:
                cleaned_rows.append(record)
                seen.add(record)

        except (ValueError, TypeError):
            continue

print("\nCleaned data:")
for row in cleaned_rows:
    print(row)


# --------------------------------
# PART 4: STORE DATA IN SQLITE
# --------------------------------

con = sqlite3.connect("air_quality.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station TEXT,
    day TEXT,
    hour TEXT,
    pm25 REAL,
    pm10 REAL,
    no2 REAL,
    temperature REAL
)
""")

cur.execute("DELETE FROM readings")

cur.executemany("""
INSERT INTO readings
(station, day, hour, pm25, pm10, no2, temperature)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", cleaned_rows)

con.commit()

print("\nData inserted into SQLite successfully.")


# --------------------------------
# PART 5: THREE SQL QUESTIONS
# --------------------------------

# Question 1: Average PM2.5 of Adyar
cur.execute("""
SELECT AVG(pm25)
FROM readings
WHERE station = ?
""", ("Adyar",))

print("\nAverage PM2.5 of Adyar:", cur.fetchone()[0])


# Question 2: Highest PM2.5 reading
cur.execute("""
SELECT MAX(pm25)
FROM readings
""")

print("Highest PM2.5 reading:", cur.fetchone()[0])


# Question 3: Average PM2.5 of each station
cur.execute("""
SELECT station, AVG(pm25)
FROM readings
GROUP BY station
""")

print("\nStation-wise average PM2.5:")
for row in cur.fetchall():
    print(row)


# --------------------------------
# PART 6: DAILY SUMMARY
# --------------------------------

cur.execute("""
SELECT station, day,
MIN(pm25), MAX(pm25), AVG(pm25), COUNT(pm25)
FROM readings
GROUP BY station, day
ORDER BY station, day
""")

summary = cur.fetchall()

print("\nDaily Summary:")
for row in summary:
    print(row)


# --------------------------------
# PART 7: VISUALISATION
# --------------------------------

cur.execute("""
SELECT day, AVG(pm25)
FROM readings
GROUP BY day
ORDER BY day
""")

daily = cur.fetchall()

if daily:
    dates = [row[0] for row in daily]
    averages = [row[1] for row in daily]

    plt.figure()
    plt.plot(dates, averages, marker="o")
    plt.title("Daily PM2.5 Trend")
    plt.xlabel("Date")
    plt.ylabel("Average PM2.5")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


cur.execute("""
SELECT station, AVG(pm25)
FROM readings
GROUP BY station
""")

stations = cur.fetchall()

if stations:
    names = [row[0] for row in stations]
    values = [row[1] for row in stations]

    plt.figure()
    plt.bar(names, values)
    plt.title("Comparison of Stations")
    plt.xlabel("Station")
    plt.ylabel("Average PM2.5")
    plt.tight_layout()
    plt.show()


cur.execute("""
SELECT temperature, pm25
FROM readings
""")

relationship = cur.fetchall()

if relationship:
    temperatures = [row[0] for row in relationship]
    pm_values = [row[1] for row in relationship]

    plt.figure()
    plt.scatter(temperatures, pm_values)
    plt.title("Temperature vs PM2.5")
    plt.xlabel("Temperature (Celsius)")
    plt.ylabel("PM2.5")
    plt.tight_layout()
    plt.show()


cur.execute("""
SELECT hour, AVG(pm25)
FROM readings
GROUP BY hour
ORDER BY hour
""")

hourly = cur.fetchall()

if hourly:
    hours = [row[0] for row in hourly]
    hour_values = [row[1] for row in hourly]

    plt.figure()
    plt.bar(hours, hour_values)
    plt.title("Air Quality by Hour")
    plt.xlabel("Hour")
    plt.ylabel("Average PM2.5")
    plt.tight_layout()
    plt.show()

con.close()

print("\nB1 completed successfully.")
