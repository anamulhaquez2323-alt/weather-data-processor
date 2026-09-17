#!/bin/bash
# Weather Data Processor
# Usage: ./run.sh data/weather_march.csv

if [ -z "$1" ]; then
    echo "Usage: ./run.sh data/weather_march.csv"
    exit 1
fi

# Check Python is installed before trying to use it
if ! command -v python3 > /dev/null; then
    echo "Python 3 was not found. Please install it first."
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Cannot find $1"
    exit 1
fi

if ! python3 weather_processor.py "$1"; then
    echo "The program stopped because of an error."
    exit 1
fi

# basename strips the folder and the .csv to get the summary file name
name=$(basename "$1" .csv)
echo
cat "results/${name}_summary.txt"
