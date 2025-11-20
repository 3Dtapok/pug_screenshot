from configparser import ConfigParser
import os
from pydantic import BaseModel


class SettingModel(BaseModel):
    draw_color: str = "f00"
    line_size: int = 3
    background_opacity: int = 150


class Settings:
    def __init__(self):
        self._config_ini = ConfigParser()
        self.read_settings('settings.ini')

        self._config_dict = dict(self._config_ini['Settings'])
        self.config = SettingModel(
            draw_color=self._config_dict['draw_color'],
            line_size=self._config_dict['line_size'],
            background_opacity=self._config_dict['background_opacity'],
        )

    def read_settings(self, config_path):
        if not os.path.exists(config_path):
            self.create_default_settings(config_path)

        self._config_ini.read(config_path)

    def save_settings(self, config_path):
        with open(config_path, 'w') as configfile:
            self._config_ini.write(configfile)

    def create_default_settings(self, config_path):
        config = ConfigParser()

        config['Settings'] = {}
        settings_model = SettingModel()
        settings_dict = settings_model.model_dump()

        for key, value in settings_dict.items():
            config['Settings'][key] = str(value)

        with open(config_path, 'w') as configfile:
            config.write(configfile)

        self._config_ini = config

    def get_config(self):
        return self.config
