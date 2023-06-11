import json

import discord

from src.Configs import Configs
from src.dictionaries import styles


class ButtonsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    __buttons_config = Configs.buttons_config

    @classmethod
    def get_view_by_id(cls, view_id):
        configs = None
        for view_config in cls.__buttons_config:
            if 'view_id' in view_config and view_config['view_id'] == view_id:
                configs = view_config['buttons']
        return cls.get(configs) if configs else None

    @classmethod
    def get(cls, configs):
        view = ButtonsView()
        for button_config in configs:
            label = button_config['label']
            style = styles[button_config['style']]
            emoji = button_config['emoji'] if 'emoji' in button_config else None
            custom_id = button_config['custom_id']
            is_disabled = button_config['disabled'] if 'disabled' in button_config else False
            button = discord.ui.Button(
                label=label,
                style=style,
                emoji=emoji if emoji else None,
                custom_id=custom_id,
                disabled=is_disabled
            )

            async def button_callback(interaction):
                interaction.client.dispatch("click", interaction)

            button.callback = button_callback
            view.add_item(button)
        return view