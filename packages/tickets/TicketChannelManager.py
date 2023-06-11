import discord

from src.Configs import Configs
from src.Utils import Utils


class TicketChannelManager:
    __utils = None
    __instance = None
    __server_id = None
    __config = None
    __bot = None
    __channel_by_category = None

    @classmethod
    def __init__(cls, client):
        cls.__bot = client.get_bot()
        cls.__config = client.get_config()
        cls.__server_id = cls.__config['server_id']
        cls.__utils = Utils.get_instance(client)

    @classmethod
    def get_instance(cls, client):
        if not cls.__instance:
            cls.__instance = TicketChannelManager(client)
        return cls.__instance

    @classmethod
    async def manage_ticket_channel(cls):
        selectors_config = Configs.selectors_config
        options = []
        for selector_config in selectors_config:
            if 'options' in selector_config and 'selector_id' in selector_config:
                if selector_config['selector_id'] == "ticket_category":
                    options = selector_config['options']
        expected_channels = []
        for option in options:
            expected_channels.append(option['label'])
        expected_channels.append("Archive")
        bot = cls.__bot
        guild = bot.get_guild(cls.__server_id)
        categories = guild.by_category()
        obtained_channels = []
        missing_channels = expected_channels.copy()
        for category_tuple in categories:
            category = category_tuple[0]
            if not category:
                continue
            if category in obtained_channels:
                continue
            for channel in expected_channels:
                if category.name.startswith(channel):
                    obtained_channels.append(category)
                    if channel in missing_channels:
                        missing_channels.remove(channel)
        for channel in missing_channels:
            permission_overwrite = discord.PermissionOverwrite(view_channel=False)
            utils = Utils.get_instance()
            archive = utils.get_archive()
            new_position = archive.position - 1 if archive else None
            await guild.create_category(
                channel + "-1",
                overwrites={guild.default_role: permission_overwrite},
                position=new_position
            )
        cls.__channel_by_category = guild.by_category()
        await cls.remove_unused_categories(expected_channels)

    @classmethod
    async def remove_unused_categories(cls, control_category_names):
        guild = cls.__bot.get_guild(cls.__server_id)
        for category in guild.categories:
            for category_name in control_category_names:
                if category.name.startswith(category_name):
                    number = int(category.name.split("-")[1])
                    if number > 1 and len(category.channels) == 0:
                        await category.delete()

    @classmethod
    def count_channels(cls, category_name):
        amount = 0
        categories = cls.__channel_by_category
        for category in categories:
            channels = category[1]
            if category[0].name == category_name:
                amount = len(channels)
        return amount

    @classmethod
    def get_last_category(cls, name_starting):
        categories = cls.__channel_by_category
        last_category = None
        for category in categories:
            category = category[0]
            if not category:
                continue
            if category.name.startswith(name_starting):
                if not last_category:
                    last_category = category
                elif int(category.name[:1]) > int(last_category.name[:1]):
                    last_category = category
        return last_category

    @classmethod
    async def create_category(cls, category_name, permissions=None):
        guild = cls.__bot.get_guild(cls.__server_id)
        categories = guild.by_category()
        category_number = 0
        last_category = None
        for category_tuple in categories:
            current_category = category_tuple[0]
            if not current_category:
                last_category = current_category
                continue
            current_category_name = current_category.name
            if current_category_name.startswith(category_name):
                category_number = int(current_category_name.split("-")[1])
                last_category = current_category
        last_default_category = guild.categories[0]
        config = None
        for conf in Configs.selectors_config:
            if conf['selector_id'] == 'ticket_category':
                config = conf
        first_category = config['options'][0]['label']
        if not last_category:
            for category in guild.categories:
                if not category.name.startswith(first_category):
                    last_default_category = category
        new_name_id = category_number + 1
        new_name = category_name + "-" + str(new_name_id)
        new_position = last_category.position if last_category else last_default_category.position
        default_overwrite = {guild.default_role: discord.PermissionOverwrite()}
        new_category: discord.CategoryChannel = await guild.create_category(
            name=new_name,
            overwrites=permissions if permissions else default_overwrite,
            position=new_position
        )
        return new_category

    @classmethod
    async def create_channel(cls, category_name, channel_name, perm_id, is_order=False, is_open=False):
        bot = cls.__bot
        server_id = Configs.main_config['server_id']
        guild = bot.get_guild(server_id)
        channel = None
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
        perms = overwrites if not is_open else None
        for guild_category in guild.categories:
            if channel:
                continue
            if guild_category.name.startswith(category_name):
                if is_order:
                    ticket_id = channel_name.split("-")[1]
                    for ticket_channel in guild_category.channels:
                        if channel:
                            continue
                        if ticket_channel.name.split("-")[1] == ticket_id:
                            channel = await guild_category.create_text_channel(channel_name)
                            await channel.move(after=ticket_channel)
                    continue
                if len(guild_category.channels) < 47:
                    channel = await guild_category.create_text_channel(channel_name)
                else:
                    new_category = await cls.create_category(
                        category_name,
                        perms
                    )
                    channel = await new_category.create_text_channel(channel_name)
        if not channel:
            new_category = await cls.create_category(
                category_name,
                perms
            )
            channel = await new_category.create_text_channel(channel_name)
        manager_roles = cls.__utils.get_perm_roles(perm_id)
        for manager_role in manager_roles:
            role = discord.utils.get(guild.roles, name=manager_role)
            if role:
                await channel.set_permissions(
                    role,
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True
                )
        return channel

    @classmethod
    async def archive(cls, channel):
        bot = cls.__bot
        config = cls.__config
        server_id = config['server_id']
        guild = bot.get_guild(server_id)
        archive = None
        for category in guild.categories:
            if category.name.startswith("Archive"):
                archive = category
        managers_roles = cls.__utils.get_perm_roles("ticket_manager")
        perms = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
        for role_name in managers_roles:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                perms[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                    view_channel=True
                )
        if not archive:
            archive = await cls.create_category("Archive", perms)
        if len(archive.channels) > 47:
            archive = await cls.create_category("Archive", perms)
        await channel.move(end=True, category=archive)
