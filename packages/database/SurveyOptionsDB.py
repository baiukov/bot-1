from packages.database.Database import Database


class SurveyOptionsDB(Database):
    __instance = None
    table_name = "survey_options"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = SurveyOptionsDB()
        return cls.__instance

    @classmethod
    def create(cls, survey_id, option_name):
        option_id = cls.insert({
            "survey_id": survey_id,
            "option_name": option_name,
        })
        return option_id