import json

import discord.ui

from src.Configs import Configs


class Selection(discord.ui.Select):
    def __init__(self, custom_id, placeholder, options) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            options=options
        )

    @classmethod
    def from_id(cls, selector_id):
        selector_config = cls.get_selector(selector_id)
        options = cls.get_options(selector_config['options'] if 'options' in selector_config else [])
        return cls(
            custom_id=selector_config['selector_id'],
            placeholder=selector_config['placeholder'],
            options=options
        )

    @classmethod
    def from_raw(cls, custom_id, placeholder, options_raw):
        options = cls.get_options(options_raw)
        return cls(
            custom_id=custom_id,
            placeholder=placeholder,
            options=options
        )

    async def callback(self, interaction):
        interaction.client.dispatch("click", interaction)

    @classmethod
    def get_selector(cls, selector_id):
        selectors_config = Configs.selectors_config
        for selector_config in selectors_config:
            if 'selector_id' in selector_config and selector_config['selector_id'] == selector_id:
                return selector_config
        return selectors_config[0]

    @classmethod
    def get_options(cls, options_config):
        options = []
        for option_config in options_config:
            label = option_config['label'] if 'label' in option_config else ""
            value = option_config['id'] if 'id' in option_config else "0"
            description = option_config['description'] if 'description' in option_config else ""
            emoji = option_config['emoji'] if 'emoji' in option_config else None
            new_option = discord.SelectOption(
                label=label,
                value=value,
                description=description,
                emoji=emoji
            )
            options.append(new_option)
        return options