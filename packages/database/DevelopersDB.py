from packages.tickets.Ticket import Ticket
from packages.database.Database import Database


class DevelopersDB(Database):
    __instance = None
    table_name = "developers"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = DevelopersDB()
        return cls.__instance

    @classmethod
    def create(cls, static_id: str, name: str, category: str):
        cls.insert({
            "static_id": static_id,
            "nickname": name,
            "category": category
        })

    @classmethod
    def get_by_name(cls, username):
        return cls.fetch_one("nickname", username)

    @classmethod
    def get_by_category(cls, category):
        return cls.fetch_all_by("category", category)

    @classmethod
    def get_additional(cls, ticket_id):
        sql = """
                SELECT * 
                FROM developers 
                WHERE static_id 
                    NOT IN
                    (SELECT dev_chosen.dev_id
                     FROM dev_chosen
                     JOIN orders 
                     ON orders.ORDER_ID = dev_chosen.ORDER_ID 
                        AND orders.TICKET_ID = %s)
              """
        result = cls.execute(sql, (ticket_id,))
        return result

    @classmethod
    def is_chosen_dev(cls, ticket_id, dev_id):
        sql = """
            SELECT * 
            FROM `dev_chosen` 
            JOIN `orders` 
            ON dev_chosen.ORDER_ID = orders.ORDER_ID 
                    AND orders.TICKET_ID = %s
              """
        result = cls.execute(sql, (ticket_id,))
        is_dev = False
        for dev in result:
            if str(dev[0]) == str(dev_id):
                is_dev = True
        return is_dev
