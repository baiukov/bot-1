from packages.database.Database import Database
from packages.tickets.Ticket import Ticket


class TicketDB(Database):
    __instance = None
    table_name = "tickets"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = TicketDB()
        return cls.__instance

    @classmethod
    def save_ticket(cls, ticket: Ticket):
        ticket_id = cls.insert({
            "category": ticket.get_category(),
            "author": ticket.get_author().id,
            "payment_type": ticket.get_payment(),
            "text": ticket.get_text(),
        })
        return ticket_id

    @classmethod
    def get_repeating_amount(cls):
        sql = """
            SELECT COUNT(*) AS total_order_count
            FROM (
              SELECT DISTINCT t.author, o.order_id
              FROM orders o
              INNER JOIN tickets t ON o.ticket_id = t.ticket_id
              WHERE t.author IN (
                SELECT DISTINCT t.author
                FROM orders o
                INNER JOIN tickets t ON o.ticket_id = t.ticket_id
                WHERE o.is_payed = 1
              )
            ) AS subquery;
        """
        result = cls.execute(sql, (),)
        return result
