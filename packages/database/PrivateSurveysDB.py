from packages.database.Database import Database


class PrivateSurveysDB(Database):
    __instance = None
    table_name = "private_surveys"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = PrivateSurveysDB()
        return cls.__instance

    @classmethod
    def create(cls, author_id, name):
        survey_id = cls.insert({
            "author": author_id,
            "survey_name": name,
        })
        return survey_id