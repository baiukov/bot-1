from packages.database.Database import Database


class PrivateMessagesDB(Database):
    __instance = None
    table_name = "private_messages"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = PrivateMessagesDB()
        return cls.__instance

    @classmethod
    def add(cls, message_id, survey_id):
        cls.insert({
            "message_id": message_id,
            "survey_id": survey_id,
        })
