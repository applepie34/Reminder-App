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
            id INTEGER PRIMARY KEY ,
            title TEXT NOT NULL,
            description TEXT DEFAULT 'reminder' ,
            recurrence TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
        ''')
        conn.commit()
def add_reminder(title, description,recurrence, date, time):
    next_id = get_next_available_id()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(''' 
        insert into reminders (id,title,description,recurrence,date,time)
        values (?,?,?,?,?,?)''',
        (next_id,title, description, recurrence, date, time))
        conn.commit()
def get_reminders():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(''' 
        select * from reminders
        ''')
        return cursor.fetchall()


def delete_reminder(task_id: int):
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (task_id,))
        conn.commit()

def get_next_available_id() -> int:
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reminders ORDER BY id ASC")
        rows = cursor.fetchall()
        
        existing_ids = {row[0] for row in rows}
        
        # Find the smallest positive integer missing from existing_ids
        next_id = 1
        while next_id in existing_ids:
            next_id += 1
            
        return next_id



    

