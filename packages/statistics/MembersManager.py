import discord

from packages.database.MembersDB import MembersDB
from src.Configs import Configs
from src.Utils import Utils


class MembersManager:
    __instance = None
    __client = None
    __bot: discord.Client = None
    __guild: discord.Guild = None
    __utils: Utils = None
    __source_roles = {}

    __voice_categories = {}

    @classmethod
    def __init__(cls, client):
        cls.__client = client
        cls.__bot = client.get_bot()
        cls.__guild = cls.__bot.get_guild(Configs.main_config['server_id'])
        cls.__utils = Utils.get_instance(client)


    @classmethod
    def get_instance(cls, client=None):
        if not cls.__instance:
            cls.__instance = MembersManager(client)
        return cls.__instance

    @classmethod
    async def update_member_roles(cls):
        cfg = Configs.main_config
        sources = cfg['sources'] if 'sources' in cfg else None
        if not sources:
            return
        guild = cls.__guild
        missing_roles = []
        for source in sources:
            role_name = source['role'] if 'role' in source else None
            if not role_name:
                continue
            source_name = source['name'] if 'name' in source else None
            role_cfg = {
                "name": source,
                "role": role_name
            }
            missing_roles.append(role_cfg)
            for role in guild.roles:
                if role.name == role_name:
                    cls.__source_roles[role] = source_name
                    missing_roles.remove(role_cfg)
        for role in missing_roles:
            new_role = await guild.create_role(name=role['role'])
            cls.__source_roles[new_role] = role['name']

    @classmethod
    def add_member(cls, member):
        members_db = MembersDB.get_instance()
        members_db.add(member.id)

    @classmethod
    def remove_member(cls, member):
        members_db = MembersDB.get_instance()
        members_db.delete("member_id", member.id)

    @classmethod
    def role_added(cls, before, after):
        if len(before.roles) > len(after.roles):
            return
        new_role = None
        for role in after.roles:
            if new_role:
                continue
            if role not in before.roles:
                new_role = role
        if not new_role:
            return
        if not new_role in cls.__source_roles:
            return
        source = cls.__source_roles[new_role]
        members_db = MembersDB.get_instance()
        members_db.update({"source": source}, "member_id", after.id)
