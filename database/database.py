import sqlite3
from sqlite3 import Error

DB_FILE = "enose_pork.db"

def create_connection():
    """ create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    """ create a table from the create_table_sql statement """
    try:
        sql_create_history_table = """ CREATE TABLE IF NOT EXISTS history (
                                        id integer PRIMARY KEY,
                                        timestamp text NOT NULL,
                                        result text NOT NULL
                                    ); """
        c = conn.cursor()
        c.execute(sql_create_history_table)
    except Error as e:
        print(e)

def add_detection_record(conn, timestamp, result):
    """
    Add a new detection record into the history table
    :param conn:
    :param timestamp:
    :param result:
    :return: project id
    """
    sql = ''' INSERT INTO history(timestamp,result)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (timestamp, result))
    conn.commit()
    return cur.lastrowid

def get_all_records(conn):
    """
    Query all rows in the history table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, result FROM history ORDER BY timestamp DESC")
    rows = cur.fetchall()
    return rows

def initialize_database():
    """Create and initialize the database and table."""
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        conn.close()
    else:
        print("Error! cannot create the database connection.")

