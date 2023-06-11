class Ticket:
    __id = None
    __author = None
    __text = None
    __payment = None
    __category = None

    def __init__(self, category, author=None, text=None, payment=None, id=None):
        self.__id = id
        self.__author = author
        self.__text = text
        self.__payment = payment
        self.__category = category

    # Getters
    def get_id(self): return self.__id

    def get_author(self): return self.__author

    def get_text(self): return self.__text

    def get_payment(self): return self.__payment

    def get_category(self): return self.__category

    # Setters
    def set_text(self, text): self.__text = text
    def set_payment(self, payment): self.__payment = payment
    def set_id(self, id): self.__id = id
