import json


class Configs:
    path = "configs/"

    file = open(path + "config.json", 'r', encoding="utf-8")
    main_config = json.load(file)
    file.close()

    file = open(path + "buttons.json", 'r', encoding="utf-8")
    buttons_config = json.load(file)
    file.close()

    file = open(path + "database.json", 'r', encoding="utf-8")
    database_config = json.load(file)
    file.close()

    file = open(path + "messages.json", 'r', encoding="utf-8")
    messages_config = json.load(file)
    file.close()

    file = open(path + 'modals.json', 'r', encoding="utf-8")
    modals_config = json.load(file)
    file.close()

    file = open(path + "selectors.json", 'r', encoding="utf-8")
    selectors_config = json.load(file)
    file.close()

    file = open(path + "translation.json", 'r', encoding="utf-8")
    translation_config = json.load(file)
    file.close()
