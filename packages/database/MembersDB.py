from packages.database.Database import Database


class MembersDB(Database):
    __instance = None
    table_name = "members"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = MembersDB()
        return cls.__instance

    @classmethod
    def add(cls, member_id):
        cls.insert({
            "member_id": member_id,
        })
