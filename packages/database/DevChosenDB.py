from packages.tickets.Ticket import Ticket
from packages.database.Database import Database


class DevChosenDB(Database):
    __instance = None
    table_name = "dev_chosen"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = DevChosenDB()
        return cls.__instance

    @classmethod
    def create_relation(cls, dev_id: str, order_id: int):
        cls.insert({
            "dev_id": dev_id,
            "order_id": order_id
        })

    @classmethod
    def remove_relation(cls, dev_id: str, order_id: int):
        sql = f"DELETE FROM `{cls.table_name}` WHERE DEV_ID = %s AND ORDER_ID = %s"
        cls.execute(sql, (dev_id, order_id))

    @classmethod
    def is_exists(cls, dev_id: str, order_id: str):
        sql = f"SELECT * FROM {cls.table_name} WHERE DEV_ID = %s AND ORDER_ID = %s"
        result = cls.execute(sql, (dev_id, order_id))
        return result
