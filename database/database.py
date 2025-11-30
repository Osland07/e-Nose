import sqlite3
from sqlite3 import Error

DB_FILE = "enose.db" # Database baru yang lebih general

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
                                        result text NOT NULL,
                                        raw_data TEXT
                                    ); """
        c = conn.cursor()
        c.execute(sql_create_history_table)
    except Error as e:
        print(e)

def add_detection_record(conn, timestamp, result, raw_data_str):
    """
    Add a new detection record into the history table
    :param conn:
    :param timestamp:
    :param result:
    :param raw_data_str: A string joining all raw sensor readings
    :return: project id
    """
    sql = ''' INSERT INTO history(timestamp,result,raw_data)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (timestamp, result, raw_data_str))
    conn.commit()
    return cur.lastrowid

def get_all_records(conn, filter_text=None, search_query=None, sort_column="timestamp", sort_order="DESC"):
    """
    Query all rows in the history table that match the filter and search criteria.
    """
    cur = conn.cursor()
    
    base_query = "SELECT id, timestamp, result, raw_data FROM history"
    conditions = []
    params = []

    if filter_text and filter_text != "All":
        conditions.append("result LIKE ?")
        params.append(f"{filter_text}%")

    if search_query:
        conditions.append("(CAST(id AS TEXT) LIKE ? OR timestamp LIKE ? OR result LIKE ?)")
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
        
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    allowed_sort_columns = ["id", "timestamp", "result"]
    if sort_column not in allowed_sort_columns:
        sort_column = "timestamp"
    
    if sort_order.upper() not in ["ASC", "DESC"]:
        sort_order = "DESC"

    base_query += f" ORDER BY {sort_column} {sort_order}"

    cur.execute(base_query, tuple(params))
    rows = cur.fetchall()
    return rows

def get_all_records_filtered(conn, filter_text=None, search_query=None, sort_column="timestamp", sort_order="DESC"):
    """
    Query ALL rows (no pagination) in the history table that match the filter and search criteria.
    Used for Exporting data.
    """
    cur = conn.cursor()
    
    base_query = "SELECT id, timestamp, result, raw_data FROM history"
    conditions = []
    params = []

    if filter_text and filter_text != "All":
        conditions.append("result LIKE ?")
        params.append(f"{filter_text}%")

    if search_query:
        conditions.append("(CAST(id AS TEXT) LIKE ? OR timestamp LIKE ? OR result LIKE ?)")
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
        
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    allowed_sort_columns = ["id", "timestamp", "result"]
    if sort_column not in allowed_sort_columns:
        sort_column = "timestamp"
    
    if sort_order.upper() not in ["ASC", "DESC"]:
        sort_order = "DESC"

    base_query += f" ORDER BY {sort_column} {sort_order}"

    cur.execute(base_query, tuple(params))
    rows = cur.fetchall()
    return rows

def get_record_by_id(conn, record_id):
    """
    Query a single row in the history table by id
    :param conn: the Connection object
    :param record_id: id of the record to retrieve
    :return: a single row tuple or None
    """
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, result, raw_data FROM history WHERE id = ?", (record_id,))
    row = cur.fetchone()
    return row

def delete_record_by_id(conn, record_id):
    """
    Delete a record from the history table by id
    :param conn: the Connection object
    :param record_id: id of the record to delete
    :return: number of rows affected
    """
    sql = 'DELETE FROM history WHERE id = ?'
    cur = conn.cursor()
    cur.execute(sql, (record_id,))
    conn.commit()
    return cur.rowcount

def get_paginated_records(conn, offset, limit, filter_text=None, search_query=None, sort_column="timestamp", sort_order="DESC"):
    """
    Query records in the history table with pagination, filtering, searching, and sorting.
    """
    cur = conn.cursor()
    
    base_query = "SELECT id, timestamp, result, raw_data FROM history"
    conditions = []
    params = []

    if filter_text and filter_text != "All":
        conditions.append("result LIKE ?")
        params.append(f"{filter_text}%")

    if search_query:
        conditions.append("(CAST(id AS TEXT) LIKE ? OR timestamp LIKE ? OR result LIKE ?)")
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
        
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    allowed_sort_columns = ["id", "timestamp", "result"]
    if sort_column not in allowed_sort_columns:
        sort_column = "timestamp"
    
    if sort_order.upper() not in ["ASC", "DESC"]:
        sort_order = "DESC"

    base_query += f" ORDER BY {sort_column} {sort_order} LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(base_query, tuple(params))
    rows = cur.fetchall()
    return rows

def get_record_count(conn, filter_text=None, search_query=None):
    """
    Get the total number of records in the history table, with optional filtering and searching.
    """
    cur = conn.cursor()

    base_query = "SELECT COUNT(*) FROM history"
    conditions = []
    params = []

    if filter_text and filter_text != "All":
        conditions.append("result LIKE ?")
        params.append(f"{filter_text}%")

    if search_query:
        conditions.append("(CAST(id AS TEXT) LIKE ? OR timestamp LIKE ? OR result LIKE ?)")
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    cur.execute(base_query, tuple(params))
    count = cur.fetchone()[0]
    return count

def get_distinct_result_types(conn):
    """
    Get all unique base result strings from the history table.
    e.g., "Terdeteksi Daging Babi" from "Terdeteksi Daging Babi (99.5%)"
    """
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT result FROM history")
    rows = cur.fetchall()
    
    unique_results = set()
    for row in rows:
        result_str = row[0]
        base_result = result_str.split(' (')[0].strip()
        unique_results.add(base_result)
        
    return sorted(list(unique_results))

def initialize_database():
    """Create and initialize the database, table, and migrate schema if needed."""
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(history)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'raw_data' not in columns:
                print("Migrating database: Adding 'raw_data' column to history table.")
                cursor.execute("ALTER TABLE history ADD COLUMN raw_data TEXT")
                conn.commit()
        except Error as e:
            print(f"Error during database migration: {e}")
        finally:
            conn.close()
    else:
        print("Error! cannot create the database connection.")