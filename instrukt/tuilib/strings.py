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
"""Hardcoded strings for the TUI."""
from typing import Tuple

from instrukt.config import APP_SETTINGS


class Icons(dict[str, Tuple[str, str]]):
    """Custom dict subclass for storing icons.

    Accessing the dict by key returns either:
        a. the icon (2nd field) when settings.interface.nerd_fonts is true
        b. the name (1st field) when settings.interface.nerd_fonts is false
    """

    def __getitem__(self, key):
        if APP_SETTINGS.interface.nerd_fonts:
            return super().__getitem__(key)[1]
        else:
            return super().__getitem__(key)[0]

    def __dir__(self):
        return [*self.keys(), *dir(super())]

    def get(self, key, default=None):
        if APP_SETTINGS.interface.nerd_fonts:
            return super().get(key, default)[1]
        else:
            return super().get(key, default)[0]

    def __getattr__(self, attr):
        return self.get(attr, None)


ICONS = Icons({
    "agent_tools": ("tools", ""),
    "agent_settings": ("settings", ""),
    "index": ("indexes", ""),
    "main_menu": ("C", ""),
    "console_action": ("console", ""),
    "dev_console_action": ("shell", ""),
    "keys_action": ("keys", ""),
})

INTRO_MESSAGE = """
Welcome to Instrukt: your integrated AI environment in the terminal !

This is the main prompt and info window where you can find various information about the agents and available commands.

Use the input area below to execute Instrukt commands or send messages to active agents.

To get started, type `/help` or `.help` for a list of available commands.

Type `.help <command>` to show the help for a specific command.

You can load the full documentation by typing `.man` or pressing `h`.
"""

#TODO!: contextual tips 
TIPS = """
## TIPS:
- You can stop a **thinking** agent by pressing `ctrl+s` in the prompt.
"""

AGENT_WINDOW_INTRO = """
This is the agent window. It is used to display the conversation with the agent and the agent's final replies.
"""

REALM_WINDOW_INTRO = """
The realm window displays the virtual environment of the running agent, usually a Docker container.\
It shows the agent's input and the container's output, allowing for seamless interaction with the environment. Additionally, it offers the ability to attach to the running container directly and interact with the environment as a user.
"""

IPYTHON_SHELL_INTRO = """
[b u]Instrukt Ipython Shell[/]

[b blue]Commands[/]:
    [b yellow]intro[/]: Print this message

[b blue]Global variables[/]:
    [b yellow]app[/]: Instrukt `Textual` app instance
    [b yellow]agent[/]: Current agent
    [b yellow]agent.base_agent[/]: Langchain agent instance
    [b yellow]memory[/]: Current agent's memory
    [b yellow]im[/]: Index Manager
"""

LIBMAGIC_INSTALL = """For debian based systems, you can install libmagic with:\
 `sudo apt install libmagic1`"""

