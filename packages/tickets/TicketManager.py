import asyncio
import random
import re

import discord

from packages.database.DevChosenDB import DevChosenDB
from packages.database.DevelopersDB import DevelopersDB
from packages.database.OrdersDB import OrdersDB
from packages.google.TableManager import TableManager
from packages.tickets.Ticket import Ticket
from packages.database.TicketDB import TicketDB
from packages.database.ClosedTicketsDB import ClosedTicketDB
from packages.database.FinishedOrdersDB import FinishedOrdersDB
from packages.tickets.TicketChannelManager import TicketChannelManager
from packages.statistics.StatisticsChannelManager import StatisticsChannelManager
from src.ButtonsView import ButtonsView
from src.Client import Client
from src.Configs import Configs
from src.Modal import Modal
from src.Utils import ephemeral_messages
from src.Utils import Utils
from datetime import date

from src.dictionaries import Columns


class TicketManager:
    __manger = None
    __tickets = []
    __creating_tickets: {discord.User: Ticket} = {}
    __payments: {discord.channel: int} = {}
    __ticket_db = None
    __utils = None

    @classmethod
    def __init__(cls):
        cls.__ticket_db = TicketDB.get_instance()
        cls.__utils = Utils.get_instance(Client.get_instance())

    @classmethod
    def get_manager(cls):
        if not cls.__manger:
            cls.__manger = TicketManager()
        return cls.__manger

    @classmethod
    def get_ticket_by_id(cls, ticket_id):
        for ticket in cls.__tickets:
            if ticket.get_id() == ticket_id:
                return ticket
        return None

    @classmethod
    def get_ticket_by_user(cls, user):
        for ticket in cls.__tickets:
            if ticket.get_author() == user:
                return ticket
        return None

    @classmethod
    async def new_ticket_step0(cls, interaction, message=None):
        user = interaction.user
        if user in cls.__creating_tickets:
            cls.__creating_tickets.pop(user)
        await interaction.response.send_message(message['text'], embed=message['embed'], view=message['view'],
                                                ephemeral=True)
        ephemeral_messages[user] = await interaction.original_response()

    @classmethod
    async def new_ticket_step1(cls, interaction: discord.Interaction, modal=None):
        category_id = interaction.data['values'][0]
        selector_id = interaction.data['custom_id']
        selector_config = Configs.selectors_config
        category = None
        for selector in selector_config:
            if selector_id == selector['selector_id']:
                for option in selector['options']:
                    if option['id'] == category_id:
                        category = option['label']
        ticket = Ticket(
            category=category,
            author=interaction.user
        )
        cls.__creating_tickets[interaction.user] = ticket
        await interaction.response.send_modal(modal)

    @classmethod
    async def new_ticket_step2(cls, interaction: discord.Interaction):
        author = interaction.user
        ticket: Ticket | None = None
        for current_author in cls.__creating_tickets:
            if current_author == author:
                ticket = cls.__creating_tickets[current_author]
        if not ticket:
            return False
        answers = []
        for component in interaction.data['components']:
            answers.append(component['components'][0])
        text = answers[0]['value']
        payment = answers[1]['value']
        ticket.set_text(text)
        ticket.set_payment(payment)
        ticket_id = cls.__ticket_db.save_ticket(ticket)
        ticket.set_id(ticket_id)

    @classmethod
    async def new_ticket_step3(cls, interaction: discord.Interaction):
        user = interaction.user
        ticket: Ticket = cls.__creating_tickets[user] if user in cls.__creating_tickets else None
        if not ticket:
            return
        cls.__creating_tickets.pop(user)
        channel_name = "ticket-" + str(ticket.get_id())
        category_name = ticket.get_category()
        channel_manager = TicketChannelManager.get_instance(Client.get_instance())
        channel = await channel_manager.create_channel(category_name, channel_name, "ticket_manager")
        await channel.set_permissions(
            user,
            read_messages=True,
            send_messages=True,
            manage_messages=True
        )
        msgs = Configs.translation_config
        msg = msgs['go_to_channel']
        line = cls.__utils.get_line(msg, {
            "user": user.mention,
            "channel": f"<#{channel.id}>"
        })
        await interaction.response.send_message(line, ephemeral=True)
        ephemeral_messages[user] = await interaction.original_response()
        utils = Utils.get_instance()
        welcome_msg = await utils.get_message('ticket_welcome_message')
        default_args = {
            "username": f"{user.name}#{user.discriminator}",
            "ticket_text": ticket.get_text(),
            "payment": ticket.get_payment()
        }
        welcome_msg['text'] = utils.get_line(welcome_msg['text'], default_args)
        title = welcome_msg['embed'].title
        welcome_msg['embed'].title = utils.get_line(title, default_args)
        for field in welcome_msg['embed'].fields:
            new_value = utils.get_line(field.value, default_args)
            field.value = new_value
        await channel.send(welcome_msg['text'], embed=welcome_msg['embed'], view=welcome_msg['view'])
        message = await channel.send(msgs['cancel_ticket'], view=ButtonsView.get_view_by_id("remove_ticket"))
        await message.pin()
        table_manager = TableManager.get_instance()
        table_manager.to_column(f"ticket-{ticket.get_id()}", Columns.TICKET)
        await StatisticsChannelManager.update_orders_in_progress()

    @classmethod
    async def remove_ticket(cls, interaction: discord.Interaction):
        user: discord.Member = interaction.user
        is_manager = cls.__utils.has_permission(user, "ticket_manager")
        msgs = Configs.translation_config
        utils = Utils.get_instance()
        if not is_manager:
            await interaction.response.send_message(msgs['only_managers'], ephemeral=True)
        else:
            message = await utils.get_message("ticket_cancelling_message")
            await interaction.response.send_message(
                message['text'],
                embed=message['embed'],
                view=message['view'],
                ephemeral=True
            )
        ephemeral_messages[user] = await interaction.original_response()

    @classmethod
    async def removed_ticket(cls, interaction: discord.Interaction):
        channel = interaction.channel
        ticket_id = int(channel.name.split("-")[1])
        selectors_config = Configs.selectors_config
        config = None
        for selector_config in selectors_config:
            if selector_config['selector_id'] == 'cancelling_reason':
                config = selector_config
        options = config['options']
        reason = ""
        for option in options:
            if 'id' in option and option['id'] == interaction.data['values'][0]:
                reason = option['label'] if 'label' in option else ""
        if not reason:
            return
        closed_tickets_db = ClosedTicketDB.get_instance()
        closed_tickets_db.save_closed(ticket_id, reason)
        client = Client.get_instance()
        channel_manager = TicketChannelManager(client)
        client = client.get_instance()
        bot = client.get_bot()
        config = client.get_config()
        guild = bot.get_guild(config['server_id'])
        await channel_manager.archive(channel)
        overwrites = channel.overwrites
        for key in overwrites:
            await channel.set_permissions(target=key, view_channel=False)
        order_channel = None
        channel_infos = channel.name.split("-")
        for guild_channel in guild.channels:
            if order_channel:
                continue
            if guild_channel.name == channel_infos[0] + "-" + channel_infos[1] + "-order":
                order_channel = guild_channel
        if order_channel:
            overwrites = order_channel.overwrites
            await channel_manager.archive(order_channel)
            for key in overwrites:
                await order_channel.set_permissions(target=key, view_channel=False)
        await interaction.response.defer()
        await asyncio.sleep(3000)
        await interaction.message.delete()
        ephemeral_messages[interaction.user] = await interaction.original_response()

    @classmethod
    async def select_dev(cls, ctx):
        msgs = Configs.translation_config
        if not cls.__utils.has_permission(ctx.author, "ticket_manager"):
            interaction = await ctx.respond(msgs['error'] + msgs['not_enough_perm'], ephemeral=True)
            ephemeral_messages[ctx.author] = await interaction.original_response()
            return
        developerDB = DevelopersDB()
        developers = developerDB.fetch_all(limit=25)
        if not developers:
            interaction = await ctx.respond(msgs['error'] + msgs['no_devs'], ephemeral=True)
            ephemeral_messages[ctx.author] = await interaction.original_response()
            return
        utils = Utils.get_instance(Client.get_instance())
        view = utils.get_dev_selector(developers)
        interaction = await ctx.respond(view=view, ephemeral=True)
        ephemeral_messages[ctx.author] = await interaction.original_response()

    @classmethod
    async def create_order(cls, interaction: discord.Interaction):
        channel = interaction.channel
        channel_name = channel.name
        msgs = Configs.translation_config
        err = msgs['error']
        user = interaction.user
        if not channel_name.startswith("ticket"):
            await interaction.response.send_message(err + msgs['not_ticket'], ephemeral=True)
            ephemeral_messages[user] = interaction.original_response()
            return
        ticket_id = interaction.channel.name.split("-")[1]
        ticketsDB = TicketDB.get_instance()
        ticket = ticketsDB.fetch_one("ticket_id", ticket_id)
        if not ticket:
            await interaction.response.send_message(err + msgs['ticket_not_exist'], ephemeral=True)
            ephemeral_messages[user] = interaction.original_response()
            return
        developer_static = interaction.data['values'][0].split("_")[1]
        utils = Utils.get_instance(Client.get_instance())
        member = await utils.check_developer(interaction)
        orders_db = OrdersDB.get_instance()
        if orders_db.fetch_one("ticket_id", ticket_id):
            await interaction.response.send_message(err + msgs['order_exist'], ephemeral=True)
            ephemeral_messages[user] = interaction.original_response()
            return
        order_id = orders_db.create(ticket_id)
        dev_chosen_db = DevChosenDB.get_instance()
        dev_chosen_db.create_relation(developer_static, order_id)
        await interaction.response.send_message(msgs['order_success'])
        channel_manager = TicketChannelManager(Client.get_instance())
        order_channel = await channel_manager.create_channel(
            channel.category.name,
            f"ticket-{ticket_id}-order",
            "ticket_manager",
            True
        )
        welcome_msg = await utils.get_message('info_for_developers')
        default_args = {
            "username": f"{member.mention}",
            "order_number": str(order_id),
            "type": ticket[2],
            "text": ticket[4],
            "payment": ticket[3]
        }
        welcome_msg['text'] = utils.get_line(welcome_msg['text'], default_args)
        title = welcome_msg['embed'].title
        description = welcome_msg['embed'].description
        welcome_msg['embed'].description = utils.get_line(description, default_args)
        welcome_msg['embed'].title = utils.get_line(title, default_args)
        for field in welcome_msg['embed'].fields:
            new_value = utils.get_line(field.value, default_args)
            field.value = new_value
        await order_channel.send(welcome_msg['text'], embed=welcome_msg['embed'], view=welcome_msg['view'])
        await order_channel.set_permissions(member, view_channel=True, send_messages=True)
        ephemeral_messages[user] = await interaction.original_response()
        table_manager = TableManager.get_instance()
        table_manager.to_column(f"ticket-{ticket_id}", Columns.ORDER)
        await channel.edit(name=channel.name + "-0" + "﹪")
        await StatisticsChannelManager.update_repeating()

    @classmethod
    async def select_add_developer(cls, ctx):
        developersDB = DevelopersDB.get_instance()
        channel = ctx.channel
        msgs = Configs.translation_config
        err = msgs['error']
        user = ctx.author
        utils = Utils.get_instance(Client.get_instance())
        if not utils.has_permission(user, "ticket_manager"):
            interaction = ctx.respond(err + msgs['not_enough_perm'], ephemeral=True)
            ephemeral_messages[ctx.author] = await interaction.original_response()
            return
        if not channel.name.startswith("ticket"):
            interaction = ctx.respond(err + msgs['not_ticket'], ephemeral=True)
            ephemeral_messages[ctx.author] = await interaction.original_response()
            return
        ticket_id = channel.name.split("-")[1]
        suitable_developers = developersDB.get_additional(ticket_id)
        if len(suitable_developers) == 0:
            interaction = ctx.respond(err + msgs['no_devs'])
            ephemeral_messages[ctx.author] = await interaction.original_response()
            return
        view = utils.get_dev_selector(suitable_developers, is_addition=True)
        interaction = await ctx.respond(view=view, ephemeral=True)
        ephemeral_messages[ctx.author] = await interaction.original_response()

    @classmethod
    async def select_remove_developer(cls, ctx):
        developersDB = DevelopersDB.get_instance()
        channel = ctx.channel
        msgs = Configs.translation_config
        err = msgs['error']
        user = ctx.author
        utils = Utils.get_instance(Client.get_instance())
        if not utils.has_permission(user, "ticket_manager"):
            interaction = ctx.respond(err + msgs['not_enough_perm'], ephemeral=True)
            ephemeral_messages[ctx.author] = await interaction.original_response()
            return
        if not channel.name.startswith("ticket"):
            interaction = ctx.respond(err + msgs['not_ticket'], ephemeral=True)
            ephemeral_messages[ctx.author] = await interaction.original_response()
            return
        ticket_id = channel.name.split("-")[1]
        suitable_developers = developersDB.get_related(ticket_id)
        if len(suitable_developers) == 0:
            interaction = ctx.respond(err + msgs['no_devs'])
            ephemeral_messages[ctx.author] = await interaction.original_response()
            return
        view = utils.get_dev_selector(suitable_developers, is_removing=True)
        interaction = await ctx.respond(view=view, ephemeral=True)
        ephemeral_messages[ctx.author] = await interaction.original_response()

    @classmethod
    async def add_developer(cls, interaction):
        developer_static = interaction.data['values'][0].split("_")[1]
        utils = Utils.get_instance(Client.get_instance())
        member = await utils.check_developer(interaction)
        if not member:
            return
        dev_chosen_db = DevChosenDB.get_instance()
        channel = interaction.channel
        channel_infos = channel.name.split("-")
        ticket_id = channel_infos[1]
        ordersDB = OrdersDB.get_instance()
        ticketsDB = TicketDB.get_instance()
        order = ordersDB.fetch_one("ticket_id", ticket_id)
        if not order:
            return
        ticket = ticketsDB.fetch_one("ticket_id", ticket_id)
        order_id = order[0]
        is_order_channel = channel_infos[2].startswith("order") if len(channel_infos) > 2 else False
        order_channel_name = channel.name if is_order_channel else \
            channel_infos[0] + "-" + channel_infos[1] + "-order"
        order_channel = channel if is_order_channel else await utils.get_channel_by_name(order_channel_name)
        welcome_msg = await utils.get_message('info_for_developers')
        default_args = {
            "username": f"{member.mention}",
            "order_number": str(order[0]),
            "type": ticket[2],
            "text": ticket[4],
            "payment": ticket[3]
        }
        welcome_msg['text'] = utils.get_line(welcome_msg['text'], default_args)
        title = welcome_msg['embed'].title
        welcome_msg['embed'].title = utils.get_line(title, default_args)
        description = welcome_msg['embed'].description
        welcome_msg['embed'].description = utils.get_line(description, default_args)
        for field in welcome_msg['embed'].fields:
            new_value = utils.get_line(field.value, default_args)
            field.value = new_value
        await order_channel.send(welcome_msg['text'], embed=welcome_msg['embed'], view=welcome_msg['view'])
        await order_channel.set_permissions(member, view_channel=True, send_messages=True)
        if not dev_chosen_db.is_exists(developer_static, order_id):
            dev_chosen_db.create_relation(developer_static, order_id)


    @classmethod
    async def remove_developer(cls, interaction):
        developer_static = interaction.data['values'][0].split("_")[1]
        utils = Utils.get_instance(Client.get_instance())
        member = await utils.check_developer(interaction)
        if not member:
            return
        dev_chosen_db = DevChosenDB.get_instance()
        channel = interaction.channel
        channel_infos = channel.name.split("-")
        ticket_id = channel_infos[1]
        ordersDB = OrdersDB.get_instance()
        order = ordersDB.fetch_one("ticket_id", ticket_id)
        if not order:
            return
        order_id = order[0]
        is_order_channel = channel_infos[2].startswith("order") if len(channel_infos) > 2 else False
        order_channel_name = channel.name if is_order_channel else \
            channel_infos[0] + "-" + channel_infos[1] + "-order"
        order_channel = channel if is_order_channel else await utils.get_channel_by_name(order_channel_name)
        await order_channel.set_permissions(member, view_channel=False, send_messages=False)
        msgs = Configs.translation_config
        message = utils.get_line(msgs['removing_success'], {
            "developer": f"{member.name}#{member.discriminator}"
        })
        await interaction.response.send_message(message, ephemeral=True)
        ephemeral_messages[interaction.user] = await interaction.original_response()
        if dev_chosen_db.is_exists(developer_static, order_id):
            dev_chosen_db.remove_relation(developer_static, order_id)

    @classmethod
    async def set_progress(cls, ctx, percentage_str, is_auto=False):
        percentage_str = percentage_str if "%" not in percentage_str else percentage_str.replace("%", "")
        utils = Utils.get_instance(Client.get_instance())
        msgs = Configs.translation_config
        err = msgs['error']
        percentage = None
        author = ctx.author
        try:
            percentage = int(percentage_str)
        except:
            interaction = await ctx.respond(err + msgs['not_num'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
        if not percentage:
            return
        if percentage < 0 or percentage > 100:
            interaction = await ctx.respond(err + msgs['0-100'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        channel = ctx.channel
        channel_name = channel.name
        channel_data = channel_name.split("-")
        if not channel_name.startswith("ticket"):
            interaction = await ctx.respond(err + msgs['not_ticket'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        if len(channel_data) < 3 and channel[2] != "order":
            interaction = await ctx.respond(err + msgs['not_order'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        ticket_id = channel_data[1]
        developersDB = DevelopersDB.get_instance()
        is_dev = developersDB.is_chosen_dev(ticket_id, author.id)
        if not is_dev:
            interaction = await ctx.respond(err + msgs['not_dev'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        ordersDB = OrdersDB.get_instance()
        order = ordersDB.fetch_one("ticket_id", ticket_id)
        current_progress = order[4]
        if percentage <= current_progress and not is_auto:
            interaction = await ctx.respond(err + msgs['same_or_lower_progress'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        ordersDB.update({"progress": percentage}, "ticket_id", ticket_id)
        interaction = await ctx.respond(f"{msgs['set_progress']} **``{str(percentage)}``**%",
                                        ephemeral=True)
        to_channel: discord.TextChannel = utils.get_ticket_channel_by_id(ticket_id)
        to_channel_name = to_channel.name
        to_channel_infos = to_channel_name.split("-")
        new_name = to_channel_infos[0] + "-" + to_channel_infos[1] + "-" + str(percentage) + "﹪"
        if percentage == 100:
            new_name = to_channel_infos[0] + "-" + to_channel_infos[1] + "-finished"
        if percentage == 100:
            await ctx.respond(msgs['order_finish'], ephemeral=True)
            message = await utils.get_message("order_finished")
            await to_channel.send(message['text'], embed=message['embed'], view=message['view'])
            now = date.today()
            ordersDB.update({"date_finished": now}, "ticket_id", ticket_id)
            return
        message = utils.get_line(msgs['update_progress'], {
            "progress": f" **``{percentage_str}``**%"
        })
        await to_channel.send(message)
        ephemeral_messages[author] = await interaction.original_response()
        await to_channel.edit(name=new_name)

    @classmethod
    async def accept_message(cls, interaction):
        button = interaction.data
        button_id = button['custom_id']
        channel = interaction.channel
        channel_name = channel.name
        info = channel_name.split("-")
        utils = Utils.get_instance(Client.get_instance())
        to_channel_name = info[0] + "-" + info[1] + "-order"
        to_channel = await utils.get_channel_by_name(to_channel_name)
        msgs = Configs.translation_config
        author = interaction.user
        err = msgs['error']
        if button_id == "finished_need_changes":
            if utils.has_permission(author, "ticket_manager"):
                await interaction.response.send_message(err + msgs['only_client'], ephemeral=True)
                ephemeral_messages[author] = await interaction.original_response()
                return
            ordersDB = OrdersDB.get_instance()
            finishedOrders = FinishedOrdersDB.get_instance()
            ticket_id = info[1]
            if finishedOrders.is_finished_by_tid(ticket_id):
                await interaction.response.send_message(err + msgs['cannot_back_finished'], ephemeral=True)
                ephemeral_messages[author] = await interaction.original_response()
                return
            ordersDB.update({"progress": 80}, "ticket_id", ticket_id)
            new_name = channel_name.replace("finished", "80﹪")
            await to_channel.send(msgs['need_changes'])
            await channel.send(msgs['need_changes'])
            await interaction.message.delete()
            await channel.edit(name=new_name)
            return
        if button_id == "finished_accept":
            if utils.has_permission(author, "ticket_manager"):
                await cls.accept_captcha(interaction)
                return
            modal = Modal.get_modal("feedback_modal")
            await interaction.response.send_modal(modal)

    @classmethod
    async def accept_captcha(cls, interaction):
        x = str(random.randint(0, 9))
        y = str(random.randint(0, 9))
        operation = random.choice(["+", "-", "*"])
        utils = cls.__utils
        modal = Modal.get_modal("accept_captcha_{x}_{operation}_{y}")
        args = {
            "x": x,
            "y": y,
            "operation": operation
        }
        id = modal.custom_id
        modal.custom_id = utils.get_line(modal.custom_id, args)
        modal.title = utils.get_line(modal.title, args)
        await interaction.response.send_modal(modal)

    @classmethod
    async def force_finish(cls, interaction):
        data = interaction.data['custom_id'].split("_")
        components = interaction.data['components']
        x = int(data[2])
        y = int(data[4])
        operation = data[3]
        user_answer_str = components[0]['components'][0]['value']
        is_incorrect = False
        answer = 0
        utils = cls.__utils
        author = interaction.user
        match operation:
            case "+":
                answer = x + y
            case "-":
                answer = x - y
            case "*":
                answer = x * y
        user_answer = 0
        try:
            user_answer = int(user_answer_str)
        except Exception as err:
            is_incorrect = True
        is_incorrect = is_incorrect or answer != user_answer
        msgs = Configs.translation_config
        err = msgs['error']
        if is_incorrect:
            await interaction.response.send_message(err + msgs['incorrect_answer'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        finished_orders_db = FinishedOrdersDB.get_instance()
        ordersDB = OrdersDB.get_instance()
        infos = interaction.channel.name.split("-")
        ticket_id = infos[1]
        order = ordersDB.fetch_one("ticket_id", ticket_id)
        if not order:
            await interaction.response.send_message(err + msgs['order_not_found'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        progress = order[4]
        if progress != 100:
            await interaction.response.send_message(err + msgs['progress_not_100'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        is_exist = finished_orders_db.fetch_one("order_id", order[0])
        if is_exist:
            await interaction.response.send_message(err + msgs['already_accepted'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        finished_orders_db.save(order[0], 5, "", "")
        await interaction.channel.send(msgs['force_finished'])
        await interaction.response.defer()
        table_manager = TableManager.get_instance()
        table_manager.to_column(f"ticket-{ticket_id}", Columns.FINISHED)
        await StatisticsChannelManager.update_rating()
        await StatisticsChannelManager.update_finished_orders()
        await StatisticsChannelManager.update_feedbacks()

    @classmethod
    async def accept_order(cls, interaction):
        data = interaction.data
        components = data['components']
        author = interaction.user
        msgs = Configs.translation_config
        err = msgs['error']
        rating = components[0]['components'][0]['value']
        try:
            rating = int(rating)
        except:
            await interaction.response.send_message(err + msgs['not_int'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        if rating < 1 or rating > 5:
            await interaction.response.send_message(err + msgs['not_in_1-5'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        suggestions = components[1]['components'][0]['value']
        feedback = components[2]['components'][0]['value']
        utils = Utils.get_instance()
        channel = await utils.get_channel_by_name("feedback")
        if not channel:
            return
        bot = Client.get_bot()
        user = bot.get_user(author.id)
        rate_str = ""
        for i in range(rating):
            rate_str += "⭐"
        message = await utils.get_dynamic_message("feedback_message", {
            "username": f"{user.name}#{user.discriminator}",
            "rating": rate_str,
            "suggestions": suggestions,
            "comment": feedback
        })
        embed: discord.Embed = message['embed']
        embed.set_thumbnail(url=user.display_avatar)
        finished_orders_db = FinishedOrdersDB.get_instance()
        ordersDB = OrdersDB.get_instance()
        infos = interaction.channel.name.split("-")
        ticket_id = infos[1]
        order = ordersDB.fetch_one("ticket_id", ticket_id)
        if not order:
            await interaction.response.send_message(err + msgs['order_not_found'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        progress = order[4]
        if progress != 100:
            await interaction.response.send_message(err + msgs['progress_not_100'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        is_exist = finished_orders_db.fetch_one("order_id", order[0])
        if is_exist:
            await interaction.response.send_message(err + msgs['already_accepted'], ephemeral=True)
            ephemeral_messages[author] = await interaction.original_response()
            return
        to_channel_name = infos[0] + "-" + infos[1] + "-order"
        to_channel = await utils.get_channel_by_name(to_channel_name)
        finished_orders_db.save(order[0], rating, suggestions, feedback)
        message2 = utils.get_line(msgs['order_accepted'], {"rating": rate_str})
        table_manager = TableManager.get_instance()
        table_manager.to_column(f"ticket-{ticket_id}", Columns.FINISHED)
        await to_channel.send(message2)
        await channel.send(message['text'], embed=embed)
        await interaction.response.defer()
        await StatisticsChannelManager.update_rating()
        await StatisticsChannelManager.update_finished_orders()
        await StatisticsChannelManager.update_feedbacks()

    @classmethod
    async def set_payment_step1(cls, ctx, amount_str):
        utils = Utils.get_instance()
        channel = ctx.channel
        selector = await utils.get_message("payment_types")
        ordersDB = OrdersDB.get_instance()
        channel_data = channel.name.split("-")
        ticket_id = channel_data[1]
        order = ordersDB.fetch_one("ticket_id", ticket_id)
        is_payed = order[5]
        msgs = Configs.translation_config
        err = msgs['error']
        author = ctx.author
        if is_payed:
            interaction = await ctx.respond(err + msgs['already_payed'], ephemeral=True)
            ephemeral_messages[author] = interaction.original_response()
            return
        nums = [str(i) for i in range(10)]
        if amount_str[-1] not in nums:
            amount_str = amount_str[:-1]
        amount = int(amount_str)
        if amount < 0:
            interaction = await ctx.respond(err + msgs['amount_below_0'], ephemeral=True)
            ephemeral_messages[author] = interaction.original_response()
            return
        if not utils.has_permission(author, "ticket_manager"):
            interaction = await ctx.respond(err + msgs['not_enough_perm'], ephemeral=True)
            ephemeral_messages[author] = interaction.original_response()
            return
        cls.__payments[channel] = amount
        await ctx.respond(selector['text'], view=selector['view'], ephemeral=True)

    @classmethod
    async def set_payment_step2(cls, interaction):
        amount = None
        channel = interaction.channel
        author = interaction.user
        msgs = Configs.translation_config
        err = msgs['error']
        utils = cls.__utils
        ptype = interaction.data['values'][0]
        pname = None
        pemail = ""
        selectors = Configs.selectors_config
        payment_selector = None
        for selector in selectors:
            id = selector['selector_id'] if 'selector_id' in selector else ""
            if id == 'payment_types':
                payment_selector = selector
        if payment_selector:
            options = payment_selector['options'] if 'options' in payment_selector else None
            if options:
                for option in options:
                    id = option['id'] if 'id' in option else ""
                    label = option['label'] if 'label' in option else ""
                    description = option['description'] if 'description' in option else ""
                    if id == ptype:
                        pname = label
                        pemail = description
        ptype = pname if pname else ptype
        for current_payment_channel in cls.__payments:
            if current_payment_channel == channel:
                amount = cls.__payments[channel]
        if not amount:
            interaction = await interaction.response.send_message(err + msgs['undefined_error'],
                                                                  ephemeral=True)
            ephemeral_messages[author] = interaction.original_response()
            return
        channel_name = channel.name
        channel_data = channel_name.split("-")
        ticket_id = channel_data[1]
        ticketDB = TicketDB.get_instance()
        ticket = ticketDB.fetch_one("ticket_id", ticket_id)
        if not ticket:
            interaction = await interaction.response.send_message(err + msgs['ticket_not_exist'],
                                                                  ephemeral=True)
            ephemeral_messages[author] = interaction.original_response()
            return
        ordersDB = OrdersDB.get_instance()
        ordersDB.update({"sum": amount}, "ticket_id", ticket_id)
        message = await utils.get_message("payment_message")
        embed: discord.Embed = message['embed']
        embed.description = utils.get_line(embed.description, {"email": pemail})
        embed.add_field(name="Order: ", value=ticket[4])
        embed.add_field(name="Payment type: ", value=ptype, inline=False)
        embed.add_field(name="Amount: ", value=amount, inline=False)
        await interaction.response.send_message(message['text'], view=message['view'], embed=embed)
        table_manager = TableManager.get_instance()
        table_manager.to_column(f"ticket-{ticket_id}", Columns.OFFER)

    @classmethod
    async def order_payed(cls, interaction):
        user = interaction.user
        utils = Utils.get_instance(Client.get_instance())
        msgs = Configs.translation_config
        err = msgs['error']
        if not utils.has_permission(user, "ticket_manager"):
            interaction = await interaction.response.send_message(err + msgs['not_enough_perm'], ephemeral=True)
            ephemeral_messages[user] = interaction.original_response()
            return
        ticket_id = interaction.channel.name.split("-")[1]
        ordersDB = OrdersDB.get_instance()
        ordersDB.update({"is_payed": True}, "ticket_id", ticket_id)
        await interaction.response.send_message(msgs["set_payed"])
        table_manager = TableManager.get_instance()
        table_manager.to_column(f"ticket-{ticket_id}", Columns.PAYED)

