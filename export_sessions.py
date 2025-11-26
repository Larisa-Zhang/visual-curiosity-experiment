import csv
import os

# input files
RECORD_FILE = "record.csv"
MEMORY_FILE = "memory_test_results.csv"

# output folder
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

def export_records():
    with open(RECORD_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print("⚠️ No data in record.csv")
        return

    header = rows[0]
    for row in rows[1:]:
        if not row: 
            continue
        session_id = row[0]
        out_path = os.path.join(EXPORT_DIR, f"record_{session_id}.csv")

        # if file doesn't exist yet, create with header
        write_header = not os.path.exists(out_path)
        with open(out_path, "a", newline='', encoding='utf-8') as out_f:
            writer = csv.writer(out_f)
            if write_header:
                writer.writerow(header)
            writer.writerow(row)

    print("✅ Records exported by session into /exports/")

def export_memory():
    if not os.path.exists(MEMORY_FILE):
        print("⚠️ No memory_test_results.csv found")
        return

    with open(MEMORY_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print("⚠️ No data in memory_test_results.csv")
        return

    header = rows[0]
    for row in rows[1:]:
        if not row: 
            continue
        session_id = row[0]  # here I assume first column = timestamp/session marker
        out_path = os.path.join(EXPORT_DIR, f"memory_{session_id}.csv")

        write_header = not os.path.exists(out_path)
        with open(out_path, "a", newline='', encoding='utf-8') as out_f:
            writer = csv.writer(out_f)
            if write_header:
                writer.writerow(header)
            writer.writerow(row)

    print("✅ Memory test results exported by session into /exports/")

if __name__ == "__main__":
    export_records()
    export_memory()
