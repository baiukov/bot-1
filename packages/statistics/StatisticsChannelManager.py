import discord

from packages.database.FinishedOrdersDB import FinishedOrdersDB
from packages.database.OrdersDB import OrdersDB
from packages.database.TicketDB import TicketDB
from src.Configs import Configs
from src.Utils import Utils


class StatisticsChannelManager:
    __instance = None
    __client = None
    __bot: discord.Client = None
    __guild: discord.Guild = None
    __utils: Utils = None

    __voice_categories = {}

    @classmethod
    def __init__(cls, client):
        cls.__client = client
        cls.__bot = client.get_bot()
        cls.__guild = cls.__bot.get_guild(Configs.main_config['server_id'])
        cls.__utils = Utils.get_instance(client)


    @classmethod
    def get_instance(cls, client=None):
        if not cls.__instance:
            cls.__instance = StatisticsChannelManager(client)
        return cls.__instance

    @classmethod
    async def manage(cls):
        config = Configs.main_config
        expected = []
        for category in config['categories']:
            if 'id' in category and category['id'] == "stats":
                expected.append({
                    "id": category['id'] if 'id' in category else "",
                    "name": category['name'] if 'name' in category else None,
                    "position": category['position'] if 'position' in category else None
                })
        await cls.manage_categories(expected)
        voice_channels = Configs.main_config['voice_channels']
        text_channels = Configs.main_config['text_channels']
        await cls.manage_channels("voice", voice_channels),
        await cls.manage_channels("text", text_channels)

    @classmethod
    async def manage_categories(cls, expected_categories):
        bot = cls.__bot
        server_id = Configs.main_config['server_id']
        guild = bot.get_guild(server_id)
        obtained_categories = []
        for category in guild.categories:
            obtained_categories.append(category)
        missing_categories = expected_categories.copy()
        for expected in expected_categories:
            for obtained in obtained_categories:
                if obtained.name == expected['name']:
                    missing_categories.remove(expected)
                    cls.__voice_categories[expected['id']] = obtained
        for category in missing_categories:
            new_category = await guild.create_category(
                name=category['name'],
                position=category['position']
            )
            cls.__voice_categories[category['id']] = new_category

    @classmethod
    async def manage_channels(cls, channelType, expected_channels):
        bot = cls.__bot
        server_id = Configs.main_config['server_id']
        guild = bot.get_guild(server_id)
        obtained_channels = []
        is_voice = True if channelType == "voice" else False
        all_channels = guild.voice_channels if is_voice else guild.text_channels
        for channel in all_channels:
            obtained_channels.append(channel)
        expected_channels_data = []
        for channel_config in expected_channels:
            channel = expected_channels[channel_config]
            name = channel['name'] if 'name' in channel else ""
            amount = channel['amount'] if 'amount' in channel else 0
            category = channel['category'] if 'category' in channel else None
            expected_channels_data.append({
                "name": name,
                "amount": amount,
                "category": category
            })
        missing_channels = expected_channels_data.copy()
        for obtained_channel in obtained_channels:
            for expected_channel in expected_channels_data:
                if obtained_channel.name.startswith(expected_channel['name']):
                    missing_channels.remove(expected_channel)
        if is_voice:
            for channel_data in missing_channels:
                name = f"{channel_data['name']}: {channel_data['amount']}"
                overwrites = {}
                for role in guild.roles:
                    overwrites[role] = discord.PermissionOverwrite(connect=False)
                categories = cls.__voice_categories
                category = categories['stats'] if 'stats' in categories else None
                if not category:
                    return
                await guild.create_voice_channel(
                    name=name,
                    overwrites=overwrites,
                    category=category
                )
        else:
            for channel_data in missing_channels:
                name = channel_data['name'].replace("#", "")
                category_name = channel_data['category']
                category = None
                for current_category in guild.categories:
                    if current_category.name == category_name:
                        category = current_category
                if not category:
                    category = await cls.create_category(category_name)
                await guild.create_text_channel(
                    name=name,
                    category=category
                )

    @classmethod
    async def create_category(cls, category_name):
        bot = cls.__bot
        server_id = Configs.main_config['server_id']
        guild = bot.get_guild(server_id)
        for category in guild.categories:
            if category.name == category_name:
                return
        category = await guild.create_category(category_name, position=1)
        return category

    @classmethod
    def get_voice(cls, voice_id):
        guild = cls.__guild
        voices = Configs.main_config['voice_channels']
        voice = None
        for channel in voices:
            if channel == voice_id:
                voice = voices[channel]
        if not voice:
            return None
        name = voice['name'] if 'name' in voice else None
        amount = voice['amount'] if 'amount' in voice else 0
        if not name:
            return None
        for channel in guild.voice_channels:
            if channel.name.startswith(name):
                return {
                    "channel": channel,
                    "amount": amount
                }

    @classmethod
    async def update_all(cls):
        await cls.update_repeating()
        await cls.update_boosters()
        await cls.update_feedbacks()
        await cls.update_rating()
        await cls.update_orders_in_progress()
        await cls.update_finished_orders()
        await cls.update_users()

    @classmethod
    async def update_users(cls):
        guild = cls.__guild
        voice_map = cls.get_voice("members")
        new_value = voice_map['amount'] if voice_map['amount'] else len(guild.members)
        voice = cls.get_voice("members")['channel']
        if not voice:
            return
        data = voice.name.split(":")
        new_name = str(data[0] + ": " + str(new_value))
        await voice.edit(name=new_name)

    @classmethod
    async def update_finished_orders(cls):
        db = FinishedOrdersDB.get_instance()
        voice_map = cls.get_voice("orders_done")
        new_value = voice_map['amount'] if voice_map['amount'] else len(db.fetch_all())
        voice = voice_map['channel']
        if not voice:
            return
        data = voice.name.split(":")
        new_name = str(data[0] + ": " + str(new_value))
        await voice.edit(name=new_name)

    @classmethod
    async def update_orders_in_progress(cls):
        new_value = 0
        guild = cls.__guild
        for channel in guild.text_channels:
            if channel.name.startswith("ticket-") and \
                    (channel.category and not channel.category.name.startswith("Archive")):
                new_value += 1
        voice_map = cls.get_voice("orders_in_progress")
        new_value = voice_map['amount'] if voice_map['amount'] else new_value
        voice = voice_map['channel']
        if not voice:
            return
        data = voice.name.split(":")
        new_name = str(data[0] + ": " + str(new_value))
        await voice.edit(name=new_name)

    @classmethod
    async def update_rating(cls):
        db = FinishedOrdersDB.get_instance()
        avg = db.get_avg_rating()[0][0]
        if not avg:
            avg = 0
        voice_map = cls.get_voice("rating")
        new_value = voice_map['amount'] if voice_map['amount'] else "{:.2f}".format(float(avg))
        voice = voice_map['channel']
        if not voice:
            return
        data = voice.name.split(":")
        new_name = str(data[0] + ": " + str(new_value))
        await voice.edit(name=new_name)

    @classmethod
    async def update_feedbacks(cls):
        cfg = Configs.main_config['text_channels']
        channel_cfg = cfg['feedback']
        feed_channel_name = channel_cfg['name']
        feed_channel = await cls.__utils.get_channel_by_name(feed_channel_name)
        real = 0
        async for _ in feed_channel.history(limit=10000):
            real += 1
        voice_map = cls.get_voice("feedback_amount")
        amount = voice_map['amount'] if voice_map['amount'] else real
        voice = voice_map['channel']
        if not voice:
            return
        data = voice.name.split(":")
        new_name = str(data[0] + ": " + str(amount))
        await voice.edit(name=new_name)

    @classmethod
    async def update_repeating(cls):
        ticketDB = TicketDB.get_instance()
        ordersDB = OrdersDB.get_instance()
        amount = ticketDB.get_repeating_amount()[0][0]
        all_amount = len(ordersDB.fetch_all())
        percentage = (amount / all_amount) * 100 if all_amount != 0 else 0.0
        real = f"{percentage:.2f}%"
        voice_map = cls.get_voice("repeating")
        amount = voice_map['amount'] if voice_map['amount'] else real
        voice = voice_map['channel']
        if not voice:
            return
        data = voice.name.split(":")
        new_name = str(data[0] + ": " + str(amount))
        await voice.edit(name=new_name)


    @classmethod
    async def update_boosters(cls):
        cfg = Configs.main_config
        booster_role_names = cfg['permissions']['server_booster']
        guild = cls.__guild
        counter = 0
        for member in guild.members:
            for role in member.roles:
                for role_name in booster_role_names:
                    if role.name == role_name:
                        counter += 1
        voice_map = cls.get_voice("boosters")
        new_value = voice_map['amount'] if voice_map['amount'] else counter
        voice = voice_map['channel']
        if not voice:
            return
        data = voice.name.split(":")
        new_name = str(data[0] + ": " + str(new_value))
        await voice.edit(name=new_name)


        