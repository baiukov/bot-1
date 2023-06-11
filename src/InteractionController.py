import discord

from packages.surveys.PrivateSurveyManager import PrivateSurveyManager
from packages.surveys.SurveyManager import SurveyManager
from packages.tickets.TicketManager import TicketManager
from src.Modal import Modal
from src.Utils import Utils
from src.Client import Client


class InteractionController:
    __instance = None

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = InteractionController()
        return cls.__instance

    @classmethod
    async def on_click(cls, interaction):
        print(interaction.data)
        button_id = interaction.data['custom_id']
        print(button_id)
        ticket_manager = TicketManager.get_manager()
        survey_manager = SurveyManager.get_instance()
        private_survey_manager = PrivateSurveyManager.get_instance()
        utils = Utils.get_instance(Client.get_instance())
        match button_id:
            case "new_ticket_button1":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.new_ticket_step0(interaction,
                                                      await utils.get_message("new_ticket_category_message"))
            case "ticket_category":
                await ticket_manager.new_ticket_step1(interaction, modal=Modal.get_modal("new_ticket_modal"))
            case "new_ticket_modal":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.new_ticket_step2(interaction)
                await utils.remove_ephemeral(interaction)
                await ticket_manager.new_ticket_step3(interaction)
            case "remove_ticket_button":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.remove_ticket(interaction)
            case "cancelling_reason":
                await ticket_manager.removed_ticket(interaction)
            case "developer_choise":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.create_order(interaction)
            case "developer_choise_add":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.add_developer(interaction)
            case "finished_need_changes":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.accept_message(interaction)
            case "finished_accept":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.accept_message(interaction)
            case "order_accept":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.accept_order(interaction)
            case "order_payed":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.order_payed(interaction)
            case "feedback_modal":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.accept_order(interaction)
            case "payment_types":
                await utils.remove_ephemeral(interaction)
                await ticket_manager.set_payment_step2(interaction)
            case "surveys_modal":
                await utils.remove_ephemeral(interaction)
                await survey_manager.create_survey(interaction)
            case "dm_surveys_modal":
                await utils.remove_ephemeral(interaction)
                await private_survey_manager.send_survey(interaction)

        if button_id.startswith("survey_"):
            await utils.remove_ephemeral(interaction)
            await survey_manager.add_vote(interaction)
        if button_id.startswith("private_"):
            await utils.remove_ephemeral(interaction)
            await private_survey_manager.add_vote(interaction)
        if button_id.startswith("accept_captcha_"):
            await utils.remove_ephemeral(interaction)
            await ticket_manager.force_finish(interaction)

