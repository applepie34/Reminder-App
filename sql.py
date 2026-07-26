import sqlite3

dbname = "reminder.db"

def get_connection():
    return sqlite3.connect(dbname)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS reminders
        ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            recurrence TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
        ''')
        conn.commit()
def add_reminder(title, description,recurrence, date, time):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(''' 
        insert into reminders (title,description,recurrence,date,time)
        values (?,?,?,?,?))''',
        (title, description, recurrence, date, time))
        conn.commit()
def get_reminders():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(''' 
        select * from reminders
        ''')
        return cursor.fetchall()

if __name__ == "__main__":
    init_db()

