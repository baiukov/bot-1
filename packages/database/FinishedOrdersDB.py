from packages.database.Database import Database
from datetime import date


class FinishedOrdersDB(Database):
    __instance = None
    table_name = "finished_orders"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = FinishedOrdersDB()
        return cls.__instance

    @classmethod
    def save(cls, order_id: int, rating: int, suggestions: str, feedback: str):
        today = date.today()
        cls.insert({
            "date_accepted": today,
            "order_id": order_id,
            "rating": rating,
            "suggestions": suggestions,
            "feedback": feedback
        })

    @classmethod
    def get_avg_rating(cls):
        sql = f"SELECT AVG(RATING) FROM {cls.table_name}"
        result = cls.execute(sql, ())
        return result

    @classmethod
    def is_finished_by_tid(cls, ticket_id):
        sql = f"SELECT * FROM {cls.table_name} LEFT JOIN `orders` USING (ORDER_ID) WHERE `ticket_id` = %s";
        result = cls.execute(sql, (ticket_id,))
        return bool(result)