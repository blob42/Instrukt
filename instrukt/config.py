##
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz>. All rights reserved.
##
##  SPDX-License-Identifier: AGPL-3.0-or-later
##
##  This file is part of Instrukt.
##
##  This program is free software: you can redistribute it and/or modify it under
##  the terms of the GNU Affero General Public License as published by the Free
##  Software Foundation, either version 3 of the License, or (at your option) any
##  later version.
##
##  This program is distributed in the hope that it will be useful, but WITHOUT
##  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
##  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
##  details.
##
##  You should have received a copy of the GNU Affero General Public License along
##  with this program.  If not, see <http://www.gnu.org/licenses/>.
##
"""Config manager for instrukt"""

import os
from pathlib import Path
from typing import Any, ClassVar, Optional, Tuple, Union

from pydantic import (
    BaseSettings,
    Field,
    SecretStr,
    root_validator,
    validator,
)
from pydantic_yaml import YamlModelMixin
from xdg import BaseDirectory  # type: ignore

from .errors import ConfigError

try:
    import chromadb
    CHROMA_INSTALLED = True
except ModuleNotFoundError:
    CHROMA_INSTALLED = False

CONFIG_PATH = BaseDirectory.save_config_path("instrukt")

if CHROMA_INSTALLED:

    class ChromaSettings(chromadb.config.Settings):

        class Config:
            env_prefix = "INSTRUKT_CHROMA_"

        persist_directory: str = "chroma_persist"
        anonymized_telemetry: bool = False
        is_persistent: bool = True
else:

    class ChromaSettings(BaseSettings):  # type: ignore
        pass


class TUISettings(BaseSettings):
    """Settings model for Instrukt."""

    class Config:
        """Pydantic config for Instrukt settings."""
        env_prefix = "INSTRUKT_TUI"

    nerd_fonts: bool = True
    code_block_theme: str = "dracula"


class OpenAISettings(BaseSettings):
    """Settings for OpenAI model."""

    class Config:
        """Pydantic config for Instrukt settings."""
        env_prefix = "INSTRUKT_OPENAI"

    model_name: str = Field(default="gpt-3.5-turbo")
    """Model name to use."""
    temperature: float = 0.7
    """Sampling temperature to use."""
    max_retries: int = 6
    """Maximum number of retries when generating."""
    max_tokens: Optional[int] = None
    """Maximum number of generated tokens."""
    request_timeout: Optional[Union[float, Tuple[float, float]]] = None
    """Timeout for requests to OpenAI completion API."""


class Settings(YamlModelMixin, BaseSettings):  # type: ignore
    """Settings model for Instrukt."""

    _openai_api_key_warning: ClassVar[bool] = False

    class Config:
        """Pydantic config for Instrukt settings."""
        env_prefix = "INSTRUKT_"
        validate_assignment = True

        @classmethod
        def customise_sources(cls, init_settings, env_settings,
                              file_secret_settings):
            """Customise the sources for settings."""
            return (
                env_settings,
                init_settings,
                file_secret_settings,
            )

    #TODO: move to openai settings class
    openai_api_key: Optional[SecretStr] = Field(
        "", env=["INSTRUKT_OPENAI_API_KEY", "OPENAI_API_KEY"])

    openai: OpenAISettings = Field(default_factory=OpenAISettings)

    debug: bool = False

    # CHROMA VECTORSTORE
    chroma: ChromaSettings = Field(default_factory=ChromaSettings)

    #COMMAND HISTORY
    history_file: str = os.path.join(CONFIG_PATH, "history.yaml")

    use_llm_cache: bool = False

    sqlite_cache_path: str = os.path.join(
        BaseDirectory.save_cache_path("instrukt"), "cache.sqlite")

    llm_errors_logdir: str = os.path.join(
        BaseDirectory.save_cache_path("instrukt", "llm_errors"))

    custom_agents_path: str = BaseDirectory.save_data_path("instrukt/agents")

    # TUI SETTINGS
    interface: TUISettings = Field(default_factory=TUISettings)

    @root_validator(skip_on_failure=True)
    def validate_config(cls, values):
        if CHROMA_INSTALLED:
            chroma_persist_directory = Path(
                values["chroma"]["persist_directory"])
            if not chroma_persist_directory.is_absolute():
                _chroma_persist_directory = \
                    os.path.join(BaseDirectory.save_data_path("instrukt"),
                                 str(chroma_persist_directory))

                values["chroma"] = ChromaSettings(
                    **values["chroma"].dict(exclude={"persist_directory"}),
                    persist_directory=_chroma_persist_directory,
                )

        return values

    @property
    def has_openai(self) -> bool:
        """Check if an OpenAI API key is set."""
        return bool(self.openai_api_key)

    @validator("openai_api_key")
    def validate_api_key(cls, v, field):
        """Warning for missing API key."""
        from instrukt.messages.log import LogMessage
        if not v and not cls._openai_api_key_warning:
            from .context import context_var
            warning = LogMessage.warning(
                f"[yellow]`{field.name}`[/] is not set. Some features may not work."
            )

            ctx = context_var.get()

            if ctx is not None and ctx.app is not None:
                ctx.app.post_message(warning)
            else:
                print(
                    "[WARNING] `openai_api_key` is not set. Some features may not work."
                )

            cls._openai_api_key_warning = True  # type: ignore
        return v


class ConfigManager():

    def __init__(self, config_file: str = "instrukt.yml"):

        self.config = Settings()  # type: ignore

        if bool(self.config.openai_api_key):
            Settings._openai_api_key_warning = True

        self.config_path = os.path.join(
            BaseDirectory.save_config_path("instrukt"), config_file)
        if os.path.exists(self.config_path):
            self.load_config()
        else:
            self.save_config()

        # add custom agent path to sys.path
        import sys
        sys.path.append(self.config.custom_agents_path)

    @property
    def C(self) -> Settings:
        """Shortcut to self.config."""
        return self.config

    def load_config(self) -> None:
        if os.path.getsize(self.config_path) == 0:
            raise ConfigError("Config file is empty.")

        parsed = self.config.parse_file(self.config_path)
        if len(parsed.openai_api_key) == 0:
            parsed = Settings(**parsed.dict())
        self.config = parsed

    def save_config(self) -> None:
        with open(self.config_path, "w") as f:
            f.write(self.config.yaml(exclude={'openai_api_key'}))

    def set(self, key: Any, value: Any):
        setattr(self.config, key, value)

    def get(self, key, default=None):
        return getattr(self.config, key, default)


CONF_MANAGER = ConfigManager()
APP_SETTINGS = CONF_MANAGER.config

if APP_SETTINGS.use_llm_cache:
    import langchain
    from langchain.cache import SQLiteCache
    langchain.llm_cache = SQLiteCache(
        database_path=APP_SETTINGS.sqlite_cache_path)
