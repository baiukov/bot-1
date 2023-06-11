from packages.database.Database import Database


class VotedDB(Database):
    __instance = None
    table_name = "voted"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = VotedDB()
        return cls.__instance

    @classmethod
    def add(cls, option_id, user_id):
        cls.insert({
            "option_id": option_id,
            "user": user_id,
        })

    @classmethod
    def has_voted(cls, user_id, survey_id):
        if not user_id or not survey_id:
            return False
        sql = """SELECT * FROM `voted` JOIN survey_options USING (OPTION_ID) 
                    WHERE USER = %s AND SURVEY_ID = %s"""
        result = cls.execute(sql, (user_id, survey_id))
        return bool(result)