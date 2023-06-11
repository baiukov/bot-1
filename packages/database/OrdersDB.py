from packages.database.Database import Database
from packages.tickets.Ticket import Ticket


class OrdersDB(Database):
    __instance = None
    table_name = "orders"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = OrdersDB()
        return cls.__instance

    @classmethod
    def create(cls, ticket_id):
        order_id = cls.insert({
            "ticket_id": ticket_id,
            "progress": 0,
            "is_payed": False,
        })
        return order_id

    @classmethod
    def get_orders_by_dev(cls, dev_id):
        sql = """
            SELECT orders.PROGRESS, tickets.CATEGORY, orders.DATE_FINISHED 
            FROM developers 
                LEFT JOIN dev_chosen 
                ON developers.STATIC_ID = dev_chosen.DEV_ID 
                    LEFT JOIN orders 
                    USING (ORDER_ID) 
                        JOIN tickets 
                        ON orders.TICKET_ID = tickets.TICKET_ID 
            WHERE dev_chosen.DEV_ID = %s
        """
        result = cls.execute(sql, (dev_id),)
        return result