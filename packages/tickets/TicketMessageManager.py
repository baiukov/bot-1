from src.Client import Client
from packages.database.DevelopersDB import DevelopersDB
from src.Utils import Utils


class TicketMessageManager:
    __instance = None

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls.__instance = TicketMessageManager()
        return TicketMessageManager

    @classmethod
    async def on_message(cls, message):
        client = Client.get_instance()
        bot = client.get_bot()
        utils = Utils.get_instance(client)
        author = message.author
        if message.author == bot.user:
            return
        channel = message.channel
        channel_name = channel.name
        if not channel_name.startswith("ticket"):
            return
        channel_info = channel.name.split("-")
        if len(channel_info) < 1:
            return
        is_order = len(channel_info) > 2 and channel_info[2].startswith("order")
        is_manager = utils.has_permission(author, "ticket_manager")
        if is_order:
            name = channel_info[0] + "-" + channel_info[1]
            to_channel = await utils.get_channel_by_started(name, is_order=True)
        else:
            name = channel_info[0] + "-" + channel_info[1] + "-order"
            to_channel = await utils.get_channel_by_name(name)
        if not to_channel:
            return
        if not is_order:
            if is_manager:
                await to_channel.send(f"**Manager {author.display_name}** said: {message.content}")
            else:
                await to_channel.send(f"**Client** said: {message.content}")
        else:
            if is_manager:
                await to_channel.send(f"**Manager {author.display_name}** said: {message.content}")
            else:
                developersDB = DevelopersDB()
                developer = developersDB.fetch_one("static_id", author.id)
                if not developer:
                    return
                dev_category = developer[2]
                await to_channel.send(f"**{dev_category} developer** said: {message.content}")
