from packages.database.OrdersDB import OrdersDB
from src.Configs import Configs
from src.Client import Client
from packages.database.DevelopersDB import DevelopersDB
from packages.tickets.TicketManager import ephemeral_messages
from src.Utils import Utils


class Manager:
    __instance = None
    __utils = None

    @classmethod
    def __init__(cls):
        cls.__utils = Utils.get_instance(Client.get_instance())

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = Manager()
        return cls.__instance

    @classmethod
    async def set_developer(cls, ctx, developer_name, category):
        msgs = Configs.translation_config
        err = msgs['error']
        if not cls.__utils.has_permission(ctx.author, "ticket_manager"):
            await ctx.response.send_message(err + msgs['not_enough_perm'], ephemeral=True)
            return
        bot = Client.get_instance().get_bot()
        developer_name = developer_name.replace(">", "")[2:]
        developer = await bot.fetch_user(developer_name)
        if not developer:
            await ctx.response.send_message(err + msgs['user_undefined'], ephemeral=True)
            return
        selectors = Configs.selectors_config
        options = None
        for selector in selectors:
            if selector['selector_id'] == 'ticket_category':
                options = selector['options']
        if not options:
            await ctx.response.send_message(err + msgs['categories_undefined'], ephemeral=True)
            return
        categories = []
        for option in options:
            categories.append(option['label'])
        if category not in categories:
            await ctx.response.send_message(err + msgs['incorrect_category'] + f"{str(categories)}",
                                            ephemeral=True)
            return
        username = developer.name + "#" + developer.discriminator
        developersDB = DevelopersDB.get_instance()
        is_exist = developersDB.get_by_name(username)
        if is_exist:
            await ctx.response.send_message(err + msgs['dev_exists'])
            return
        developersDB.create(developer.id, username, category)
        await ctx.response.send_message(msgs['new_developer'] + f"{username} - {category}", ephemeral=True)

    @classmethod
    async def dev_list(cls, ctx):
        user = ctx.author
        msgs = Configs.translation_config
        err = msgs['error']
        if not cls.__utils.has_permission(user, "ticket_manager"):
            await ctx.response.send_message(err + msgs['not_enough_perm'], ephemeral=True)
            return
        developersDB = DevelopersDB()
        message = msgs['dev_list']
        categories = cls.__utils.get_options()
        for category in categories:
            developers = developersDB.get_by_category(category)
            message += "\n" + category + f" ({len(developers)}): "
            for developer in developers:
                message += "\n" + f"{developer[1]} ({developer[0]})"
            message += "\n"
        await ctx.response.send_message(message, ephemeral=True)

    @classmethod
    async def remove_developer(cls, ctx, username):
        msgs = Configs.translation_config
        err = msgs['error']
        if not cls.__utils.has_permission(ctx.author, "ticket_manager"):
            await ctx.response.send_message(err + msgs['not_enough_perm'], ephemeral=True)
            return
        developersDB = DevelopersDB()
        developer = developersDB.get_by_name(username)
        if not developer:
            await ctx.response.send_message(err + msgs['dev_no_exist'], ephemeral=True)
            return
        developersDB.delete("nickname", username)
        await ctx.response.send_message(msgs['dev_deleted'] + f"{username} ({developer[0]}) - {developer[2]}")

    @classmethod
    async def send_orders(cls, ctx):
        author = ctx.author
        utils = cls.__utils
        msgs = Configs.translation_config
        err = msgs['error']
        if not utils.has_permission(author, "ticket_manager"):
            interaction = await ctx.respond(err + msgs['not_enough_perm'], ephemeral=True)
            ephemeral_messages[author] = interaction.original_response()
            return
        developersDB = DevelopersDB.get_instance()
        ordersDB = OrdersDB.get_instance()
        all_devs = developersDB.fetch_all()
        message = ""
        for dev in all_devs:
            nickname = dev[1]
            static_id = dev[0]
            category = dev[2]
            message += f"\n**{nickname}** ({static_id}) - {category} "
            orders = ordersDB.get_orders_by_dev(static_id)
            if not len(orders):
                message += f"\n{msgs['no_orders']}"
            for i in range(len(orders)):
                order = orders[i]
                progress = order[0]
                order_category = order[1]
                date_finished = order[2]
                is_finished = True if progress >= 100 else False
                status = "In process"
                if is_finished and date_finished:
                    date = f"{date_finished.day}.{date_finished.month}.{date_finished.year}"
                    status = f"Finished ({date})"
                message += f"\n{i + 1}. Order: {order_category}. Progress: {progress}%. Status: {status}"
            message += "\n"
        interaction = await ctx.respond(message, ephemeral=True)
        ephemeral_messages[author] = interaction.original_response()
