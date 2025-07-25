import sqlite3

DB_PATH = 'db.sqlite3'
TABLE_NAME = 'main_unitofmeasure'  # adjust 'main_' if your app name is different

def export_unit_of_measure_names():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Fetch only the `code_name`
        query = f"SELECT code_name FROM {TABLE_NAME}"
        cursor.execute(query)

        rows = cursor.fetchall()

        with open("unit_of_measures_output.txt", "w", encoding="utf-8") as f:
            for (code_name,) in rows:
                f.write(f"{code_name}\n")

        print(f"{len(rows)} unit of measure names exported to unit_of_measures_output.txt")

    except sqlite3.Error as e:
        print("SQLite error:", e)

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    export_unit_of_measure_names()
