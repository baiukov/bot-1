from packages.database.Database import Database


class SurveysDB(Database):
    __instance = None
    table_name = "surveys"

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = SurveysDB()
        return cls.__instance

    @classmethod
    def create(cls, author_id, name):
        survey_id = cls.insert({
            "author": author_id,
            "survey_name": name
        })
        return survey_id

    @classmethod
    def get_results(cls):
        sql = """
            SELECT
              S.SURVEY_ID,
              S.SURVEY_NAME,
              SO.OPTION_ID,
              SO.OPTION_NAME,
              COUNT(V.OPTION_ID)
            FROM
              SURVEYS S
              INNER JOIN SURVEY_OPTIONS SO 
                ON S.SURVEY_ID = SO.SURVEY_ID 
                    AND S.IS_ACTIVE = 0
              LEFT JOIN VOTED V 
                ON SO.OPTION_ID = V.OPTION_ID
            GROUP BY
              S.SURVEY_ID,
              S.AUTHOR,
              SO.OPTION_ID,
              SO.OPTION_NAME;
        """
        result = cls.execute(sql, (),)
        return result