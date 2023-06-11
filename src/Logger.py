import datetime


class Logger:
    __instance = None
    __log_file = open('./logs/log.txt', 'a')

    @classmethod
    def get_logger(cls):
        if not cls.__instance:
            cls.__instance = Logger()
        return cls.__instance

    @classmethod
    def log(cls, log_info):
        time = datetime.datetime.now()
        time_string = time.strftime("[%d.%m.%Y %H:%M:%S]: ")
        log_string = time_string + log_info + "\n"
        cls.__log_file.write(log_string)
