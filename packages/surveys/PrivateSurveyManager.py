import discord

from packages.database.PrivateMessagesDB import PrivateMessagesDB
from packages.database.PrivateSurveysDB import PrivateSurveysDB
from src.Client import Client
from src.Configs import Configs
from src.Modal import Modal
from src.Utils import ephemeral_messages, Utils


class PrivateSurveyManager:
    __instance = None
    __client: Client = None
    __surveys: {discord.User: [discord.Role]} = {}

    @classmethod
    def __init__(cls, client):
        cls.__client = client

    @classmethod
    def get_instance(cls, client=None):
        if not cls.__instance:
            cls.__instance = PrivateSurveyManager(client)
        return cls.__instance

    @classmethod
    async def open_modal(cls, ctx, roles):
        modal = Modal.get_modal("surveys_modal")
        modal.custom_id = "dm_surveys_modal"
        cls.exclude_roles(ctx.author, roles)
        await ctx.interaction.response.send_modal(modal)

    @classmethod
    def exclude_roles(cls, user, role_names_str):
        bot = cls.__client.get_bot()
        cfg = Configs.main_config
        server_id = cfg['server_id']
        guild = bot.get_guild(server_id)
        role_names = role_names_str.split(";")
        excluded_roles = []
        for role in guild.roles:
            current_name = role.name
            for name in role_names:
                if current_name == name:
                    excluded_roles.append(role)
        cls.__surveys[user] = excluded_roles

    @classmethod
    async def send_survey(cls, interaction):
        bot = Client.get_bot()
        cfg = Configs.main_config
        server_id = cfg['server_id']
        guild: discord.Guild = bot.get_guild(server_id)
        members = guild.members
        user = interaction.user
        excluded_roles = cls.__surveys[user] if user in cls.__surveys else []
        utils = Utils.get_instance()
        survey_message = await utils.get_survey_message(interaction, is_dm=True)
        survey_id = survey_message['survey_id']
        for member in members:
            is_excluded = False
            for member_role in member.roles:
                if is_excluded:
                    continue
                if member_role in excluded_roles:
                    is_excluded = True
            if is_excluded:
                continue
            try:
                dm = member.dm_channel
                if not dm:
                    dm = await member.create_dm()
                message = await dm.send(survey_message['text'], embed=survey_message['embed'],
                              view=survey_message['view'])
                dm_msgs_db = PrivateMessagesDB.get_instance()
                dm_msgs_db.add(message.id, survey_id)
            except:
                continue
        await interaction.response.send_message("survey created", ephemeral=True)

    @classmethod
    async def add_vote(cls, interaction):
        id = interaction.data['custom_id']
        data = id.split("_")
        user = interaction.user
        survey_id = data[1]
        answer = data[2]
        messagesDB = PrivateMessagesDB.get_instance()
        surveys_DB = PrivateSurveysDB.get_instance()
        survey = surveys_DB.fetch_one("survey_id", survey_id)
        is_active = survey[3]
        if not is_active:
            await interaction.response.defer()
            return
        message = interaction.message
        vote = messagesDB.fetch_one("message_id", message.id)
        if not vote[2]:
            messagesDB.update({"answer": answer}, "message_id", message.id)
        msgs = Configs.translation_config
        await message.edit(content=msgs['thanks_for_participation'], view=None, embed=None)
        await interaction.response.defer()

