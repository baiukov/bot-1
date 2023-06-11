import json

import discord
import numpy as np

from packages.database.DevelopersDB import DevelopersDB
from packages.database.PrivateSurveysDB import PrivateSurveysDB
from packages.database.SurveyOptionsDB import SurveyOptionsDB
from packages.database.SurveysDB import SurveysDB
from src.ButtonsView import ButtonsView
from src.dictionaries import colors
from src.Selection import Selection
from src.Configs import Configs

ephemeral_messages = {}


class Utils:
    __instance = None
    __client = None
    __bot = None

    @classmethod
    def __init__(cls, client):
        cls.__client = client
        cls.__bot = client.get_bot()

    @classmethod
    def get_instance(cls, client=None):
        if not cls.__instance:
            cls.__instance = Utils(client)
        return cls.__instance

    @classmethod
    def get_role_by_name(cls, name):
        client = cls.__client
        server = client.get_bot().get_guild(cls.__client['server_id'])
        role = discord.utils.get(server.roles, name=name)
        return role

    @classmethod
    async def get_channel_by_name(cls, channel_name, is_order=False):
        client = cls.__bot
        guilds = client.guilds
        channel_id = 0
        for guild in guilds:
            channel_sets = guild.channels
            for current_channel in channel_sets:
                if channel_id != 0:
                    continue
                if channel_name == current_channel.name:
                    channel_id = current_channel.id
                if is_order and 'order' in channel_name:
                    channel_id = 0
        channel = client.get_channel(channel_id)
        return channel

    @classmethod
    async def get_channel_by_started(cls, channel_starter, is_order=False):
        client = cls.__bot
        guilds = client.guilds
        channel_id = 0
        for guild in guilds:
            channel_sets = guild.channels
            for current_channel in channel_sets:
                print(channel_id)
                if channel_id != 0:
                    continue
                if is_order and 'order' in current_channel.name:
                    continue
                if current_channel.name.startswith(channel_starter):
                    channel_id = current_channel.id
        channel = client.get_channel(channel_id)
        return channel

    @classmethod
    def get_embed(cls, embed_config):
        title = embed_config['title'] if 'title' in embed_config else ""
        description = embed_config['description'] if 'description' in embed_config else ""
        color = embed_config['color'] if 'color' in embed_config else 0xffffff
        fields = embed_config['fields'] if 'fields' in embed_config else []
        if type(color) != 'int':
            color = colors[color] if color in colors else 0xffffff
        new_embed = discord.Embed(title=title, description=description, color=color)
        for field in fields:
            title = field['field'] if 'field' in field else ""
            value = field['value'] if 'value' in field else ""
            inline = field['inline'] if 'inline' in field else ""
            inline = False if inline in ['False', 'false', "0", 0] else True
            new_embed.add_field(name=title, value=value, inline=inline)
        return new_embed

    @classmethod
    async def get_message(cls, message_id):
        message = {
            "channel": None,
            "text": None,
            "embed": None,
            "view": None
        }
        messages_config = Configs.messages_config
        is_in_cfg = False
        for message_config in messages_config:
            if 'message_id' in message_config and message_config['message_id'] == message_id:
                is_in_cfg = True
                if 'channel' in message_config:
                    message['channel'] = await cls.get_channel_by_name(message_config['channel'])
                if 'text' in message_config:
                    message['text'] = message_config['text']
                if 'embed' in message_config:
                    message['embed'] = cls.get_embed(message_config['embed'])
                if 'view_id' in message_config:
                    message['view'] = ButtonsView.get_view_by_id(message_config['view_id'])
                if 'selector_id' in message_config:
                    view = discord.ui.View()
                    view.add_item(Selection.from_id(message_config['selector_id']))
                    message['view'] = view
        return message if is_in_cfg else None

    @classmethod
    def validate_user(cls, command_name, user):
        config = cls.__client.get_config()
        permitted_roles = config["permissions"]
        for role in permitted_roles:
            role_names = []
            for user_role in user.roles:
                role_names = user_role.name.lower()
            if role == role_names:
                for command in permitted_roles[role]:
                    if command_name == command:
                        return True
        return False

    @classmethod
    def get_options(cls):
        selectors = Configs.selectors_config
        result = []
        for selector in selectors:
            if 'selector_id' in selector and selector['selector_id'] == "ticket_category":
                options = selector['options'] if 'options' in selector else []
                for option in options:
                    result.append(option['label'])
        return result

    @classmethod
    def has_permission(cls, user: discord.Member, perm_id):
        roles = user.roles
        perms = Configs.main_config['permissions']
        perm_roles = perms[perm_id] if perm_id in perms else []
        for perm_role in perm_roles:
            for role in roles:
                if role.name == perm_role:
                    return True
        return False

    @classmethod
    def get_perm_roles(cls, perm_id):
        config = Configs.main_config
        server_id = config['server_id']
        guild: discord.Guild = cls.__bot.get_guild(server_id)
        perms = config['permissions']
        names = []
        for perm in perms:
            if names:
                continue
            if perm == perm_id:
                names = perms[perm]
        roles = []
        for role in guild.roles:
            for name in names:
                if role.name == name:
                    roles.append(role)
        return roles

    @classmethod
    def get_line(cls, msg, args: {} = None):
        line = msg
        if not line:
            return msg
        for arg in args:
            arg_str = "{" + arg + "}"
            if arg_str in line:
                line = line.replace(arg_str, args[arg])

        return line

    @classmethod
    def get_dev_selector(cls, all_developers, is_addition=False):
        msgs = Configs.translation_config
        options_raw = []
        for developer in all_developers:
            option = {
                "id": f"d_{developer[0]}",
                "label": f"{developer[1]}",
                "description": f"{developer[2]}",
                "emoji": "👨‍💻"
            }
            options_raw.append(option)
        selector = Selection.from_raw(
            custom_id=f"developer_choise{'_add' if is_addition else ''}",
            placeholder=msgs['choose_dev'],
            options_raw=options_raw
        )
        view = discord.ui.View()
        view.add_item(selector)
        return view

    @classmethod
    async def check_developer(cls, interaction):
        msgs = Configs.translation_config
        err = msgs['error']
        developer_static = interaction.data['values'][0].split("_")[1]
        developersDB = DevelopersDB.get_instance()
        if not developersDB.fetch_one("static_id", developer_static):
            await interaction.response.send_message(err + msgs['dev_no_exist'], ephemeral=True)
            return
        bot = cls.__client.get_bot()
        developer = None
        try:
            developer = await bot.fetch_user(developer_static)
        except:
            pass
        if not developer:
            await interaction.response.send_message(err + msgs['dev_no_exist'], ephemeral=True)
            return
        server_id = Configs.main_config['server_id']
        guild = bot.get_guild(server_id)
        member: discord.Member | None = None
        try:
            member = await guild.fetch_member(developer_static)
        except:
            pass
        if not member:
            await interaction.response.send_message(err + msgs['not_member'], ephemeral=True)
            return
        return member

    @classmethod
    def get_channel_named(cls, channel_name):
        bot = cls.__bot
        server_id = Configs.main_config['server_id']
        guild = bot.get_guild(server_id)
        result = None
        for channel in guild.channels:
            if channel.name == channel_name:
                result = channel
        return result

    @classmethod
    def get_ticket_channel_by_id(cls, ticket_id):
        bot = cls.__bot
        server_id = Configs.main_config['server_id']
        guild = bot.get_guild(server_id)
        for channel in guild.channels:
            channel_name = channel.name
            if channel_name.startswith("ticket-" + str(ticket_id)) and "order" not in channel_name:
                return channel

    @classmethod
    async def remove_ephemeral(cls, interaction: discord.Interaction):
        user = interaction.user
        if user in ephemeral_messages:
            try:
                await ephemeral_messages[user].delete()
            except:
                pass
            ephemeral_messages.pop(user)

    @classmethod
    def get_archive(cls):
        bot = cls.__bot
        server_id = Configs.main_config['server_id']
        guild = bot.get_guild(server_id)
        archive = None
        for channel in guild.channels:
            if archive:
                continue
            if channel.name.startswith("Archive"):
                archive = channel
        return archive

    @classmethod
    async def get_dynamic_message(cls, message_id: str, args: {}):
        message = await cls.get_message(message_id)
        text = message['text']
        embed: discord.Embed = message['embed']
        title = embed.title
        description = embed.description
        message['text'] = cls.get_line(text, args)
        embed.title = cls.get_line(title, args)
        embed.description = cls.get_line(description, args)
        for field in embed.fields:
            field.name = cls.get_line(field.name, args)
            field.value = cls.get_line(field.value, args)
        return message

    @classmethod
    async def get_survey_msg_by_id(cls, id):
        if not id:
            return None
        cfg = Configs.main_config
        channels = cfg['text_channels'] if 'text_channels' in cfg else None
        if not channels:
            return None
        survey_channel = channels['surveys'] if 'surveys' in channels else None
        if not survey_channel:
            return None
        name = survey_channel['name'] if 'name' in survey_channel else None
        if not name:
            return None
        channel = await cls.get_channel_by_name(name)
        if not channel:
            return None
        return await channel.fetch_message(id)

    @classmethod
    async def get_survey_message(cls, interaction, is_dm):
        data = interaction.data
        components = data['components']
        name = components[0]['components'][0]['value']
        description = components[1]['components'][0]['value']
        options_str = components[2]['components'][0]['value']
        utils = Utils.get_instance()
        author = interaction.user
        options = options_str.replace(" ", "").replace("\n", "").split(";")
        db = PrivateSurveysDB.get_instance() if is_dm else SurveysDB.get_instance()
        survey_id = db.create(author.id, name)
        survey_option_db = SurveyOptionsDB.get_instance()
        configs = []
        for option in options:
            option_id = survey_option_db.create(survey_id, option) if not is_dm else None
            custom = "private" if is_dm else "survey"
            if not option_id:
                option_id = option
            config = {
                "custom_id": f"{custom}_{survey_id}_{option_id}",
                "label": option,
                "style": "SECONDARY",
            }
            configs.append(config)
        view = ButtonsView.get(configs)
        message = await utils.get_dynamic_message("new_survey", {
            "survey_name": name,
            "survey_description": description
        })
        return {
            "survey_id": survey_id,
            "text": message['text'],
            "embed": message['embed'],
            "view": view
        }
