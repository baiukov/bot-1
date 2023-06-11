import asyncio
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from packages.database.FinishedOrdersDB import FinishedOrdersDB
from packages.database.OrdersDB import OrdersDB
from packages.database.PrivateSurveysDB import PrivateSurveysDB
from packages.database.SurveysDB import SurveysDB
from packages.google.TableManager import TableManager
from packages.statistics.MembersManager import MembersManager
from packages.statistics.StatisticsChannelManager import StatisticsChannelManager
from packages.surveys.SurveyManager import SurveyManager
from src.ButtonsView import ButtonsView
from packages.tickets.TicketChannelManager import TicketChannelManager
from src.Configs import Configs
from src.Utils import Utils
from src.dictionaries import Columns


class Client:
    __instance = None
    __intents = discord.Intents.default()
    __intents.message_content = True
    __intents.members = True

    __config = Configs.main_config
    __messages = Configs.messages_config

    __bot = commands.Bot(intents=__intents, command_prefix=__config['command_prefix'])
    __token = __config['token']

    # Getters
    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = Client()
        return cls.__instance

    @classmethod
    def get_bot(cls):
        return cls.__bot

    @classmethod
    def get_config(cls):
        return cls.__config

    @classmethod
    def get_messages(cls):
        return cls.__messages

    # Methods
    @classmethod
    def start(cls):
        cls.__bot.run(cls.__token)

    @classmethod
    async def on_start(cls):
        bot = cls.__bot
        views_configs = Configs.buttons_config
        survey_manager = SurveyManager.get_instance()
        for view_config in views_configs:
            bot.add_view(ButtonsView.get_view_by_id(view_config['view_id']))
        views = await survey_manager.get_views()
        for view in views:
            bot.add_view(view)
        channel_manager = TicketChannelManager(cls.__instance)
        await channel_manager.manage_ticket_channel()
        Utils.get_instance(cls.__instance)
        statistic_manager = StatisticsChannelManager.get_instance(cls.__instance)
        members_manger = MembersManager.get_instance(client=cls.__instance)
        await members_manger.update_member_roles()
        table_manager = TableManager.get_instance()
        table_manager.create_table_if_not_exists()
        await statistic_manager.manage()
        await statistic_manager.update_all()
        await cls.start_cycle()

    @classmethod
    async def start_cycle(cls):
        await cls.survey_cycle()
        await cls.order_cycle()
        day = 24 * 60 * 60 * 1000
        await asyncio.sleep(day)

    @classmethod
    async def survey_cycle(cls):
        today = datetime.today()
        surveysDB = SurveysDB.get_instance()
        private_surveysDB = PrivateSurveysDB.get_instance()
        surveys = surveysDB.fetch_all() + private_surveysDB.fetch_all()
        for survey in surveys:
            survey_id = survey[0]
            date_started = survey[2]
            is_active = survey[3]
            if not is_active:
                continue
            delta = today - date_started
            if delta.days >= 5:
                surveysDB.update({"is_active": False}, "survey_id", survey_id)
                message_id = survey[4]
                survey_manager = SurveyManager.get_instance()
                survey_manager.change_message(message_id)

    @classmethod
    async def order_cycle(cls):
        ordersDB = OrdersDB.get_instance()
        finished_ordersDB = FinishedOrdersDB.get_instance()
        orders = ordersDB.fetch_all()
        today = datetime.today()
        for order in orders:
            date_created = order[2]
            delta = today - date_created
            if delta.days < 30:
                continue
            order_id = order[0]
            is_finished = finished_ordersDB.fetch_one("order_id", order_id)
            if not is_finished:
                ticket_id = order[1]
                table_manager = TableManager.get_instance()
                table_manager.to_column(f"ticket-{ticket_id}", Columns.CANCELLED)