import sqlite3
import sys

def check_db():
    try:
        # Connect to database
        conn = sqlite3.connect('papers.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table['name']}")

        # Check sections table
        print("\nChecking sections table:")
        cursor.execute("SELECT * FROM sections;")
        sections = cursor.fetchall()
        print(f"Found {len(sections)} sections:")
        for section in sections:
            print(f"\nSection: {section['name']}")
            print(f"Content length: {len(section['content'])}")
            print(f"Updated at: {section['updated_at']}")
            print("-" * 50)

    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_db()
