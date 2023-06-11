import gspread
from oauth2client.service_account import ServiceAccountCredentials


class TableManager:
    __instance = None
    __client = None
    __bot = None
    __sheet = None

    def __init__(self, client):
        self.__instance = self
        self.__client = client
        self.__bot = client.get_bot()

    @classmethod
    def get_instance(cls, client=None):
        if not cls.__instance and client:
            cls.__instance = TableManager(client)
        return cls.__instance

    @classmethod
    def create_table_if_not_exists(cls):
        table_name = "Воронка продаж"
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        gclient = gspread.authorize(credentials)
        cls.__gclient = gclient
        print(gclient)
        try:
            sheet = gclient.open(table_name).sheet1
        except Exception as err:
            sheet = gclient.create(table_name)
        print(sheet)
        cls.__sheet = sheet
        header = {
            "A1": "Первичный контакт",
            "B1": "Создан заказ",
            "C1": "Отправлен оффер",
            "D1": "Оплачен",
            "E1": "Завершен",
            "F1": "Отказ"
        }
        for cell in header:
            sheet.format("A1:F1", {
                "backgroundColor": {
                    "red": 1.0,
                    "green": 50.0,
                    "blue": 32.0
                },
                "textformat": {
                    "bold": True
                }
            })
            sheet.update(cell, header[cell])

    @classmethod
    async def add_editor(cls, ctx, email):
        cls.__sheet.share(email, perm_type="user", role="writer")
        await ctx.respond("Email added", ephemeral=True)
