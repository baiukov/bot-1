from packages.database.Database import Database


class ClosedTicketDB(Database):
    __instance = None
    table_name = "closed_tickets"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = ClosedTicketDB()
        return cls.__instance

    @classmethod
    def save_closed(cls, ticket_id: int, reason: str):
        cls.insert({
            "ticket_id": ticket_id,
            "reason": reason
        })
