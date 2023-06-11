import json

import discord.ui

from src.dictionaries import input_styles
from src.Configs import Configs


class Modal(discord.ui.Modal):
    __config_file = Configs.modals_config

    @classmethod
    async def callback(cls, interaction: discord.Interaction) -> None:
        interaction.client.dispatch("click", interaction)

    @classmethod
    def get_modal(cls, modal_id):
        modal = discord.ui.Modal(title="")
        config = None
        for modal_config in cls.__config_file:
            if 'modal_id' in modal_config and modal_config['modal_id'] == modal_id:
                config = modal_config
        if not config:
            print("-")
            return discord.ui.Modal(title="")
        modal.title = config['title'] if 'title' in config else ""
        modal.callback = cls.callback
        modal.custom_id = config['modal_id']
        answers = config['answers'] if 'answers' in config else []
        for answer_config in answers:
            label = answer_config['label'] if 'label' in answer_config else ""
            style = input_styles[answer_config['style']] if 'style' in answer_config else discord.InputTextStyle.short
            placeholder = answer_config['placeholder'] if 'placeholder' in answer_config else ""
            value = answer_config['value'] if 'value' in answer_config else ""
            required = answer_config['required'] if 'required' in answer_config else False
            custom_id = answer_config['custom_id'] if 'custom_id' in answer_config else None

            answer = discord.ui.InputText(
                label=label,
                style=style,
                placeholder=placeholder,
                value=value,
                required=required,
                custom_id=custom_id
            )
            modal.add_item(answer)
        return modal

