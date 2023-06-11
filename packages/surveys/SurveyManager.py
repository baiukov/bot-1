import discord

from packages.database.SurveyOptionsDB import SurveyOptionsDB
from packages.database.SurveysDB import SurveysDB
from packages.database.VotedDB import VotedDB
from src.ButtonsView import ButtonsView
from src.Configs import Configs
from src.Modal import Modal
from src.Utils import Utils
from src.Utils import ephemeral_messages


class SurveyManager:
    __instance = None

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = SurveyManager()
        return cls.__instance

    @classmethod
    async def open_modal(cls, ctx):
        modal = Modal.get_modal("surveys_modal")
        await ctx.interaction.response.send_modal(modal)

    @classmethod
    async def create_survey(cls, interaction):
        utils = Utils.get_instance()
        author = interaction.user
        msgs = Configs.translation_config
        err = msgs['error']
        survey_message = await utils.get_survey_message(interaction, is_dm=False)
        cfg = Configs.main_config
        channels = cfg['text_channels'] if 'text_channels' in cfg else None
        if not channels:
            await interaction.response.send_message(err + msgs['undefined_error'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        channel_cfg = channels['surveys'] if 'surveys' in channels else None
        if not channel_cfg:
            await interaction.response.send_message(err + msgs['undefined_error'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        channel_name = channel_cfg['name'] if 'name' in channel_cfg else None
        if not channel_cfg:
            await interaction.response.send_message(err + msgs['undefined_error'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        channel = await utils.get_channel_by_name(channel_name)
        if not channel:
            message = utils.get_line(msgs['channel_doesnt_exist'], {
                "channel_name": channel_name
            })
            await interaction.response.send_message(err + message, ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        message = await channel.send(survey_message['text'], embed=survey_message['embed'],
                                        view=survey_message['view'])
        surveysDB = SurveysDB.get_instance()
        surveysDB.update({"message_id": str(message.id)}, "survey_id", survey_message['survey_id'])
        await interaction.response.send_message(msgs['survey_created'], ephemeral=True)
        ephemeral_messages[author] = await interaction.original_response()

    @classmethod
    async def add_vote(cls, interaction):
        id = interaction.data['custom_id']
        data = id.split("_")
        user = interaction.user
        survey_id = data[1]
        option_id = data[2]
        voted_DB = VotedDB.get_instance()
        surveys_DB = SurveysDB.get_instance()
        survey = surveys_DB.fetch_one("survey_id", survey_id)
        is_active = survey[3]
        if not is_active:
            await interaction.response.defer()
            return
        has_voted = voted_DB.has_voted(user.id, survey_id)
        if not has_voted:
            voted_DB.add(option_id, user.id)
        await interaction.response.defer()

    @classmethod
    async def get_views(cls):
        surveyDB = SurveysDB.get_instance()
        optionsDB = SurveyOptionsDB.get_instance()
        surveys = surveyDB.fetch_all()
        utils = Utils.get_instance()
        views = []
        for survey in surveys:
            survey_id = survey[0]
            is_active = survey[3]
            message_id = survey[4]
            options = optionsDB.fetch_all_by("survey_id", survey_id)
            configs = []
            for option in options:
                option_id = option[0]
                option_name = option[2]
                config = {
                    "custom_id": f"survey_{survey_id}_{option_id}",
                    "label": option_name,
                    "style": "SECONDARY",
                    "disabled": not is_active
                }
                configs.append(config)
            view = ButtonsView.get(configs)
            survey_message = await utils.get_survey_msg_by_id(message_id)
            if not is_active and survey_message:
                await cls.change_message(message_id)
            views.append(view)
        return views

    @classmethod
    async def send_results(cls, ctx):
        surveysDB = SurveysDB.get_instance()
        results = surveysDB.get_results()
        message = "**Surveys:**\n"
        length = len(results)
        if not length:
            message += "--There is no surveys yet--"
        for i in range(len(results)):
            result = results[i]
            survey_id = result[0]
            survey_name = result[1]
            option_name = result[3]
            count = result[4]
            if i == 0:
                message += f"0. {survey_name}\n"
            if i > 0 and survey_id != results[i-1][0]:
                message += f"{i}. {survey_name}\n"
            message += f"{option_name} - {count} votes\n"
        await ctx.respond(message, ephemeral=True)

    @classmethod
    async def change_message(cls, message_id):
        cfg = Configs.main_config
        channels = cfg['text_channels'] if 'text_channels' in cfg else None
        utils = Utils.get_instance()
        if not channels:
            return
        channel_cfg = channels['surveys'] if 'surveys' in channels else None
        if not channel_cfg:
            return
        channel_name = channel_cfg['name'] if 'name' in channel_cfg else None
        if not channel_cfg:
            return
        channel = await utils.get_channel_by_name(channel_name)
        if not channel:
            return
        msgs = Configs.translation_config
        message = await channel.fetch_message(message_id)
        await message.edit(content=msgs['survey_ended'], view=None)