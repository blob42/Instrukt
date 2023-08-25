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
"""Debug commands.

To activate these commands type `%debug` in the console.
"""

import sys

from ..utils.debug import dap_listen
from .command import CallbackOutput, CmdLog
from .root_cmd import ROOT as root


def toggle_langchain_debug():
    """Activate debug mode."""
    import langchain
    langchain.debug = not langchain.debug


toggle_langchain_debug()
"""Extra debug commands"""


@root.command
async def stderr(ctx) -> CallbackOutput:
    """stderr file descriptor"""
    # return sys.stdin.fileno(), sys.stdout.fileno()
    return sys.stderr

@root.command
async def toggle_dbg(ctx) -> CallbackOutput:
    """Deactivate debug mode."""
    from instrukt.config import APP_SETTINGS
    if APP_SETTINGS.debug:
        APP_SETTINGS.debug = False
        return CmdLog("debug mode deactivated")

    APP_SETTINGS.debug = True
    return CmdLog("debug mode activated")


@root.command
async def dap(ctx) -> CallbackOutput:
    """Toggle DAP debugging"""


    if dap_listen():
        return CmdLog("started DAP server")

    return CmdLog("DAP server already started")
