#!/usr/bin/env python3

import csv
import os
import sys
from datetime import datetime

COLUMNS = ["date", "min_temp", "max_temp", "rainfall_mm", "wind_kmh"]
WET_DAY_RAIN = 1.0


def wind_type(speed):
    if speed < 20:
        return "Calm"
    elif speed < 40:
        return "Breezy"
    else:
        return "Windy"


def check_row(row, seen_dates):
    problems = []

    # DictReader puts any extra values under the key None
    if None in row:
        return ["too many values"], None

    for column in COLUMNS:
        if row[column] is None or row[column].strip() == "":
            problems.append(column + " is missing")

    if problems:
        return problems, None

    date = row["date"].strip()

    # strptime also rejects dates that look real but do not exist
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        problems.append("date " + date + " is not a real YYYY-MM-DD date")

    if date in seen_dates:
        problems.append("date " + date + " is repeated")

    numbers = {}
    for column in COLUMNS[1:]:
        try:
            numbers[column] = float(row[column])
        except ValueError:
            value = row[column].strip()
            problems.append(column + " '" + value + "' is not a number")

    # Only worth comparing the values once they are all numbers
    if len(numbers) == 4:
        if numbers["min_temp"] > numbers["max_temp"]:
            problems.append("min_temp is higher than max_temp")
        if numbers["min_temp"] < -50 or numbers["max_temp"] > 60:
            problems.append("temperature is outside -50 to 60")
        if numbers["rainfall_mm"] < 0:
            problems.append("rainfall_mm is negative")
        if numbers["wind_kmh"] < 0:
            problems.append("wind_kmh is negative")

    if problems:
        return problems, None

    numbers["date"] = date
    return problems, numbers


def load_readings(file_name):
    readings = []
    errors = []
    seen_dates = []

    with open(file_name, "r", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            print("Error: the file is empty")
            sys.exit(1)

        # The columns have to match the ones the program expects
        headings = [name.strip().lower() for name in reader.fieldnames]
        if headings != COLUMNS:
            print("Error: the columns must be " + ", ".join(COLUMNS))
            sys.exit(1)

        reader.fieldnames = headings

        for row in reader:
            problems, reading = check_row(row, seen_dates)

            if reading is None:
                line = "line " + str(reader.line_num)
                errors.append(line + ": " + "; ".join(problems))
            else:
                readings.append(reading)
                seen_dates.append(reading["date"])

    return readings, errors


def work_out_day(reading):
    reading["avg_temp"] = round((reading["min_temp"] + reading["max_temp"]) / 2, 1)
    reading["temp_range"] = round(reading["max_temp"] - reading["min_temp"], 1)

    if reading["rainfall_mm"] >= WET_DAY_RAIN:
        reading["day_type"] = "Wet"
    else:
        reading["day_type"] = "Dry"

    reading["wind"] = wind_type(reading["wind_kmh"])


def summarise(readings):
    total_temp = 0
    total_rain = 0
    total_wind = 0
    wet_days = 0
    wind_counts = {"Calm": 0, "Breezy": 0, "Windy": 0}

    hottest = readings[0]
    coldest = readings[0]
    wettest = readings[0]
    windiest = readings[0]

    for day in readings:
        total_temp += day["avg_temp"]
        total_rain += day["rainfall_mm"]
        total_wind += day["wind_kmh"]
        wind_counts[day["wind"]] += 1

        if day["day_type"] == "Wet":
            wet_days += 1

        # Replace each extreme day whenever a later day beats it
        if day["max_temp"] > hottest["max_temp"]:
            hottest = day
        if day["min_temp"] < coldest["min_temp"]:
            coldest = day
        if day["rainfall_mm"] > wettest["rainfall_mm"]:
            wettest = day
        if day["wind_kmh"] > windiest["wind_kmh"]:
            windiest = day

    days = len(readings)

    return {
        "days": days,
        "average_temp": round(total_temp / days, 1),
        "total_rain": round(total_rain, 1),
        "wet_days": wet_days,
        "average_wind": round(total_wind / days, 1),
        "hottest": hottest,
        "coldest": coldest,
        "wettest": wettest,
        "windiest": windiest,
        "wind_counts": wind_counts,
    }


def save_daily_results(file_name, readings):
    fields = COLUMNS + ["avg_temp", "temp_range", "day_type", "wind"]

    with open(file_name, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(readings)


def save_summary(file_name, input_file, summary, errors):
    lines = [
        "WEATHER SUMMARY",
        "===============",
        "Data file: " + input_file,
        "Days processed: " + str(summary["days"]),
        "Rows skipped: " + str(len(errors)),
        "",
        "Average temperature: " + str(summary["average_temp"]) + " C",
        "Hottest day: " + summary["hottest"]["date"]
        + " (" + str(summary["hottest"]["max_temp"]) + " C)",
        "Coldest day: " + summary["coldest"]["date"]
        + " (" + str(summary["coldest"]["min_temp"]) + " C)",
        "",
        "Total rainfall: " + str(summary["total_rain"]) + " mm",
        "Wet days: " + str(summary["wet_days"]),
        "Wettest day: " + summary["wettest"]["date"]
        + " (" + str(summary["wettest"]["rainfall_mm"]) + " mm)",
        "",
        "Average wind speed: " + str(summary["average_wind"]) + " km/h",
        "Windiest day: " + summary["windiest"]["date"]
        + " (" + str(summary["windiest"]["wind_kmh"]) + " km/h)",
        "Calm days: " + str(summary["wind_counts"]["Calm"]),
        "Breezy days: " + str(summary["wind_counts"]["Breezy"]),
        "Windy days: " + str(summary["wind_counts"]["Windy"]),
    ]

    if errors:
        lines.append("")
        lines.append("Skipped rows:")
        for error in errors:
            lines.append("  " + error)

    with open(file_name, "w") as file:
        file.write("\n".join(lines) + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python weather_processor.py data/weather_march.csv")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.isfile(input_file):
        print("Error: cannot find " + input_file)
        sys.exit(1)

    readings, errors = load_readings(input_file)

    print("Valid days: " + str(len(readings)))
    print("Rows skipped: " + str(len(errors)))
    for error in errors:
        print("  Skipped " + error)

    if len(readings) == 0:
        print("Error: there were no valid rows to process")
        sys.exit(1)

    for reading in readings:
        work_out_day(reading)

    summary = summarise(readings)

    # Name the results after the input file, so nothing gets overwritten
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    os.makedirs("results", exist_ok=True)
    daily_file = os.path.join("results", base_name + "_daily.csv")
    summary_file = os.path.join("results", base_name + "_summary.txt")

    try:
        save_daily_results(daily_file, readings)
        save_summary(summary_file, input_file, summary, errors)
    except OSError:
        print("Error: the results could not be saved")
        sys.exit(1)

    print("Daily results saved to " + daily_file)
    print("Summary saved to " + summary_file)


if __name__ == "__main__":
    main()
