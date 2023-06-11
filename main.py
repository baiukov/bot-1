from src.Client import Client
from src.Logger import Logger

import src.event_handler


def main():
    Client.get_instance().start()
    Logger()


if __name__ == '__main__':
    main()
