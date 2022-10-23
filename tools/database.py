import sqlite3
import os
import datetime as dt

database = "database.db"


class DoesNotExist(Exception):
    pass


def connect():
    existed = False  # file created on .connect This is much prettier way to do this.
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    if not existed:
        sql1 = """\
CREATE TABLE IF NOT EXISTS uni_module(
    module_id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_name TEXT,
    module_code TEXT
    )
"""
        sql2 = """\
CREATE TABLE IF NOT EXISTS attendance_codes(
    code_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    uni_module INTEGER NOT NULL,
    date INTEGER NOT NULL,
    FOREIGN KEY (uni_module) REFERENCES courses(module_id) )       
        """
        cursor.execute(sql1)
        cursor.execute(sql2)
        connection.commit()
    return connection, cursor


def get_attendance_codes(cursor: sqlite3.Cursor):
    """
    Get last 24hours codes
    :param cursor:
    :return:
    """
    sql = """\
SELECT module_code, code FROM attendance_codes
INNER JOIN uni_module ON uni_module.module_id = attendance_codes.uni_module
WHERE date < ? and date > ?;
"""
    cursor.execute(sql, (dt.datetime.utcnow().timestamp(), dt.datetime.utcnow().timestamp() - 86400))
    return cursor.fetchall()


def add_course(cursor: sqlite3.Cursor, course_name: str, course_code: str):
    course_code = course_code.upper()
    sql = """\
INSERT INTO uni_module (module_name, module_code) VALUES (?, ?);
"""
    cursor.execute(sql, (course_name, course_code))
    return True


def list_modules(cursor: sqlite3.Cursor):
    sql = """\
SELECT module_name, module_code FROM uni_module;
"""
    cursor.execute(sql)
    return cursor.fetchall()


def remove_module(cursor: sqlite3.Cursor, course_code: str):
    sql = """\
DELETE FROM uni_module WHERE module_code = ?;
"""
    cursor.execute(sql, (course_code,))
    return True


def add_attendance_code(cursor: sqlite3.Cursor, course_code: str, code: str):
    course_code = course_code.upper()
    module_id = get_module_id(cursor, course_code)
    if not module_id:
        raise DoesNotExist(f"Module {course_code} does not exist")
    sql = """\
INSERT INTO attendance_codes (code, uni_module, date) VALUES (?, ?, ?);
"""
    cursor.execute(sql, (code, module_id, dt.datetime.utcnow().timestamp()))
    return True


def remove_attendance_code(cursor: sqlite3.Cursor, code: str):
    sql = """\
DELETE FROM attendance_codes WHERE code = ?;
"""
    cursor.execute(sql, (code,))
    return True


def get_module_id(cursor: sqlite3.Cursor, course_code: str):
    sql = """\
SELECT module_id FROM uni_module WHERE module_code == ?;"""
    cursor.execute(sql, (course_code,))
    data = cursor.fetchone()
    if data is not None:
        return data[0]
    return None
