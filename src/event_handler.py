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
utils = Utils.get_instance(client)
manager = Manager()
controller = InteractionController.get_instance()
ticket_message_manager = TicketMessageManager()
ticket_manager = TicketManager()
statistic_manager = StatisticsChannelManager(client)
survey_manager = SurveyManager()
private_survey_manager = PrivateSurveyManager(client)
table_manager = TableManager.get_instance()
members_manager = MembersManager(client)


# Events
@bot.event
async def on_ready():
    logger.log("Bot has been started")
    print("Bot has been started")
    await client.on_start()


@bot.event
async def on_click(interaction):
    try:
        await controller.on_click(interaction)
    except:
        await interaction.response.defer()


@bot.event
async def on_member_join(member):
    members_manager.add_member(member)
    await statistic_manager.update_users()


@bot.event
async def on_member_remove(member):
    members_manager.remove_member(member)
    await statistic_manager.update_users()


@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        members_manager.role_added(before, after)
        await statistic_manager.update_boosters()


@bot.listen()
async def on_message(message):
    await ticket_message_manager.on_message(message)


@bot.slash_command()
async def payment(ctx, amount):
    await ticket_manager.set_payment_step1(ctx, amount)


# Commands
@bot.slash_command()
async def test(ctx):
    for channel in bot.get_guild(727496645767462932).channels:
        try:
            await channel.delete()
        except:
            pass


@bot.slash_command()
async def postmessage(ctx, message_id):
    message = await utils.get_message(message_id)
    if not message:
        await ctx.respond("Incorrect message id", ephemeral=True)
        return
    await ctx.send(message['text'], embed=message['embed'], view=message['view'])
    await ctx.delete()


@bot.slash_command()
async def setdeveloper(ctx, developer, category):
    await manager.set_developer(ctx, developer, category)


@bot.slash_command()
async def devlist(ctx):
    await manager.dev_list(ctx)


@bot.slash_command()
async def removedev(ctx, username):
    await manager.remove_developer(ctx, username)


@bot.slash_command()
async def createorder(ctx):
    await ticket_manager.select_dev(ctx)


@bot.slash_command()
async def developeradd(ctx):
    await ticket_manager.select_add_developer(ctx)


@bot.slash_command()
async def progress(ctx, percentage):
    await ticket_manager.set_progress(ctx, percentage)


@bot.slash_command()
async def orders(ctx):
    await manager.send_orders(ctx)


@bot.slash_command()
async def survey(ctx):
    await survey_manager.open_modal(ctx)


@bot.slash_command()
async def results(ctx):
    await survey_manager.send_results(ctx)


@bot.slash_command()
async def privatesurvey(ctx, excluded_roles=""):
    await private_survey_manager.open_modal(ctx, excluded_roles)


@bot.slash_command()
async def addtableeditor(ctx, email):
    await table_manager.add_editor(ctx, email)
