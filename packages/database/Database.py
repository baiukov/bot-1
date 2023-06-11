import json
from array import array

import pymysql
from src.Configs import Configs


class Database:
    database_config = Configs.database_config

    table_name = None

    __cursor = pymysql.connect(
        user=database_config['user'],
        password=database_config['password'],
        host=database_config['host'],
        database=database_config['database']
    ).cursor()

    def get_table_name(self):
        return self.table_name

    @classmethod
    def fetch_one(cls, field, value):
        cursor = cls.__cursor
        sql = f"SELECT * FROM {cls.table_name} WHERE `{field}` = %s"
        cursor.execute(sql, value)
        result = cursor.fetchone()
        return result

    @classmethod
    def fetch_all(cls, limit=None):
        cursor = cls.__cursor
        limit_line = f" LIMIT {limit}" if limit else ""
        sql = f"SELECT * FROM {cls.table_name} {limit_line}"
        cursor.execute(sql)
        result = cursor.fetchall()
        return result

    @classmethod
    def fetch_all_by(cls, field, value, limit=None):
        cursor = cls.__cursor
        limit_line = f" LIMIT {limit}" if limit else ""
        sql = f"SELECT * FROM {cls.table_name} WHERE `{field}` = %s {limit_line}"
        cursor.execute(sql, value)
        result = cursor.fetchall()
        return result

    @classmethod
    def insert(cls, args: {}):
        field_string = ""
        value_string = ""
        delimiter = ""
        for arg in args:
            field_string += delimiter + "`" + arg + "`"
            value_string += delimiter + "%s"
            delimiter = ", "

        sql = f"INSERT INTO {cls.table_name}({field_string}) VALUES ({value_string})"
        cursor = cls.__cursor
        tuple = cls.get_tuple(args)
        cursor.execute(sql, tuple)
        return cursor.lastrowid

    @classmethod
    def update(cls, args: {}, field, value):
        set = ""
        delimiter = ""
        for arg in args:
            set += delimiter + "`" + arg + "` = %s"
            delimiter = ","
        sql = f"UPDATE {cls.table_name} SET {set} WHERE `{field}` = %s"
        tuple = cls.get_tuple(args) + (value,)
        cursor = cls.__cursor
        cursor.execute(sql, tuple)

    @classmethod
    def execute(cls, sql, args):
        c = cls.__cursor
        c.execute(sql, args)
        result = c.fetchall()
        return result

    @classmethod
    def delete(cls, field, value):
        sql = f"DELETE FROM `{cls.table_name}` WHERE {field} = %s"
        cls.__cursor.execute(sql, value)

    @classmethod
    def get_tuple(cls, args):
        values = args.values()
        tuple = ()
        for value in values:
            tuple = tuple + (value,)
        return tuple