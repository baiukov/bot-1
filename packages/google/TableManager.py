import gspread
import gspread.utils
from oauth2client.service_account import ServiceAccountCredentials


class TableManager:
    __instance = None
    __sheet = None

    def __init__(self):
        self.__instance = self

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = TableManager()
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
        try:
            sheet = gclient.open(table_name).sheet1
        except Exception as err:
            sheet = gclient.create(table_name)
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
                "textFormat": {
                    "bold": True
                }
            })
            sheet.update(cell, header[cell])

    @classmethod
    async def add_editor(cls, ctx, email):
        cls.__sheet.share(email, perm_type="user", role="writer")
        await ctx.respond("Email added", ephemeral=True)

    @classmethod
    def find(cls, search_string):
        sheet = cls.__sheet
        values = sheet.get_all_values()
        found_cell = None
        for row in values:
            for cell in row:
                if search_string in str(cell):
                    found_cell = cell
                    break
            if found_cell:
                break

        if found_cell:
            row_index = values.index(row)
            column_index = row.index(found_cell)
            cell_address = gspread.utils.rowcol_to_a1(row_index + 1, column_index + 1)
            return cell_address
        else:
            return None

    @classmethod
    def get_empty(cls, column):
        column_index = column.value
        sheet = cls.__sheet
        values = sheet.col_values(column_index)
        last_value = None
        for value in values:
            last_value = value
        if not last_value:
            cell = sheet.cell(0, column_index)
            return cell
        last_cell = cls.find(last_value)
        row, col = gspread.utils.a1_to_rowcol(last_cell)
        row += 1
        empty_cell = gspread.utils.rowcol_to_a1(row, col)
        return empty_cell

    @classmethod
    def to_column(cls, value, column_index):
        sheet = cls.__sheet
        cell_address = cls.find(value)
        if cell_address:
            sheet.update(cell_address, "")
        cell_address = cls.get_empty(column_index)
        sheet.update(cell_address, value)


