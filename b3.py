
# QUESTION B3.1 – B3.4
# Python loops vs pandas groupby vs SQL GROUP BY

import csv
import sqlite3
import pandas as pd
import time
import cProfile
import pstats
import os
from datetime import datetime, timedelta
from collections import defaultdict


# --------------------------------
# PART 1: GENERATE SAMPLE DATA
# --------------------------------

def generate_data(station_count):
    filename = f"air_data_{station_count}_stations.csv"

    start_date = datetime(2026, 1, 1)

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(["station", "day", "hour", "pm25"])

        for station_number in range(1, station_count + 1):
            station = f"Station_{station_number}"

            for reading_number in range(8760):
                current_time = start_date + timedelta(hours=reading_number)

                # Generate repeatable sample readings
                pm25 = 30 + (reading_number % 70) + (station_number % 10)

                writer.writerow([
                    station,
                    current_time.strftime("%Y-%m-%d"),
                    current_time.strftime("%H:%M"),
                    pm25
                ])

    return filename


# --------------------------------
# PART 2: PYTHON LOOP METHOD
# --------------------------------

def python_loop_method(filename):
    totals = defaultdict(float)
    counts = defaultdict(int)

    with open(filename, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            key = (row["station"], row["day"])
            value = float(row["pm25"])

            totals[key] += value
            counts[key] += 1

    result = {}

    for key in totals:
        result[key] = totals[key] / counts[key]

    return result


# --------------------------------
# PART 3: PANDAS GROUPBY METHOD
# --------------------------------

def pandas_method(filename):
    df = pd.read_csv(filename)

    result = df.groupby(["station", "day"])["pm25"].mean()

    return result.to_dict()


# --------------------------------
# PART 4: SQL GROUP BY METHOD
# --------------------------------

def sql_method(filename):
    con = sqlite3.connect(":memory:")
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE readings (
            station TEXT,
            day TEXT,
            pm25 REAL
        )
    """)

    batch = []

    with open(filename, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            batch.append((
                row["station"],
                row["day"],
                float(row["pm25"])
            ))

            if len(batch) >= 10000:
                cur.executemany(
                    "INSERT INTO readings VALUES (?, ?, ?)",
                    batch
                )
                batch.clear()

        if batch:
            cur.executemany(
                "INSERT INTO readings VALUES (?, ?, ?)",
                batch
            )

    con.commit()

    cur.execute("""
        SELECT station, day, AVG(pm25)
        FROM readings
        GROUP BY station, day
    """)

    result = {
        (row[0], row[1]): row[2]
        for row in cur.fetchall()
    }

    con.close()
    return result


# --------------------------------
# PART 5: PROFILE PYTHON METHOD
# --------------------------------

def profile_python_method(filename):
    profiler = cProfile.Profile()

    profiler.enable()
    python_loop_method(filename)
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(10)


# --------------------------------
# PART 6: TEST THREE DATA SIZES
# --------------------------------

for station_count in [1, 12, 120]:

    print("\n================================")
    print("NUMBER OF STATIONS:", station_count)
    print("================================")

    filename = generate_data(station_count)

    # Measure Python loop time
    start = time.perf_counter()
    python_result = python_loop_method(filename)
    python_time = time.perf_counter() - start

    # Measure pandas time
    start = time.perf_counter()
    pandas_result = pandas_method(filename)
    pandas_time = time.perf_counter() - start

    # Measure SQL time
    start = time.perf_counter()
    sql_result = sql_method(filename)
    sql_time = time.perf_counter() - start

    print("Python loop time:", round(python_time, 4), "seconds")
    print("Pandas time:", round(pandas_time, 4), "seconds")
    print("SQL time:", round(sql_time, 4), "seconds")

    # Check whether all three methods agree
    keys = set(python_result.keys())

    correct = (
        keys == set(pandas_result.keys())
        and keys == set(sql_result.keys())
    )

    if correct:
        for key in keys:
            if not (
                abs(python_result[key] - pandas_result[key]) < 0.000001
                and abs(python_result[key] - sql_result[key]) < 0.000001
            ):
                correct = False
                break

    print("All three methods agree:", correct)

    # Profile the Python method for the first dataset
    if station_count == 1:
        print("\nPython cProfile report:")
        profile_python_method(filename)

print("\nB3 completed successfully.")
