import discord

from packages.google.TableManager import TableManager
from packages.surveys.PrivateSurveyManager import PrivateSurveyManager
from packages.tickets.TicketManager import TicketManager
from packages.tickets.TicketMessageManager import TicketMessageManager
from packages.statistics.StatisticsChannelManager import StatisticsChannelManager
from packages.statistics.MembersManager import MembersManager
from src.Utils import Utils
from src.Client import Client
from src.Logger import Logger
from src.InteractionController import InteractionController
from packages.management.Manager import Manager
from packages.surveys.SurveyManager import SurveyManager

client = Client.get_instance()
bot = client.get_bot()
logger = Logger.get_logger()


# Events
@bot.event
async def on_ready():
    logger.log("Bot has been started")
    print("Bot has been started")
    await client.on_start()


@bot.event
async def on_click(interaction):
    controller = InteractionController.get_instance()
    try:
        await controller.on_click(interaction)
    except:
        await interaction.response.defer()


@bot.event
async def on_member_join(member):
    statistic_manager = StatisticsChannelManager.get_instance(client)
    members_manager = MembersManager(client)
    members_manager.add_member(member)
    await statistic_manager.update_users()


@bot.event
async def on_member_remove(member):
    members_manager = MembersManager(client)
    statistic_manager = StatisticsChannelManager.get_instance(client)
    members_manager.remove_member(member)
    await statistic_manager.update_users()


@bot.event
async def on_member_update(before, after):
    statistic_manager = StatisticsChannelManager.get_instance(client)
    members_manager = MembersManager(client)
    if before.roles != after.roles:
        members_manager.role_added(before, after)
        await statistic_manager.update_boosters()


@bot.listen()
async def on_message(message):
    ticket_message_manager = TicketMessageManager()
    await ticket_message_manager.on_message(message)


@bot.slash_command()
async def payment(ctx, amount):
    ticket_manager = TicketManager()
    await ticket_manager.set_payment_step1(ctx, amount)


# Commands
@bot.slash_command()
async def postmessage(ctx, message_id):
    utils = Utils.get_instance(client)
    message = await utils.get_message(message_id)
    if not message:
        await ctx.respond("Incorrect message id", ephemeral=True)
        return
    await ctx.send(message['text'], embed=message['embed'], view=message['view'])
    await ctx.delete()


@bot.slash_command()
async def setdeveloper(ctx, developer, category):
    manager = Manager.get_instance()
    await manager.set_developer(ctx, developer, category)
    

@bot.slash_command()
async def devlist(ctx):
    manager = Manager.get_instance()
    await manager.dev_list(ctx)


@bot.slash_command()
async def unsetdev(ctx, username):
    manager = Manager.get_instance()
    await manager.remove_developer(ctx, username)


@bot.slash_command()
async def createorder(ctx):
    ticket_manager = TicketManager()
    await ticket_manager.select_dev(ctx)


@bot.slash_command()
async def devadd(ctx):
    ticket_manager = TicketManager()
    await ticket_manager.select_add_developer(ctx)

@bot.slash_command()
async def devremove(ctx):
    ticket_manager = TicketManager()
    await ticket_manager.select_remove_developer(ctx)


@bot.slash_command()
async def progress(ctx, percentage):
    ticket_manager = TicketManager()
    await ticket_manager.set_progress(ctx, percentage)


@bot.slash_command()
async def orders(ctx):
    manager = Manager.get_instance()
    await manager.send_orders(ctx)


@bot.slash_command()
async def survey(ctx):
    survey_manager = SurveyManager.get_instance()
    await survey_manager.open_modal(ctx)


@bot.slash_command()
async def results(ctx):
    survey_manager = SurveyManager.get_instance()
    await survey_manager.send_results(ctx)


@bot.slash_command()
async def privatesurvey(ctx, excluded_roles=""):
    private_survey_manager = PrivateSurveyManager.get_instance(client)
    await private_survey_manager.open_modal(ctx, excluded_roles)


@bot.slash_command()
async def addtableeditor(ctx, email):
    table_manager = TableManager.get_instance()
    await table_manager.add_editor(ctx, email)
