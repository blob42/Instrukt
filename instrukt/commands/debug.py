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

import logging

from .._logging import LogCaptureHandler
from ..context import global_context
from ..utils.debug import dap_listen
from .command import CallbackOutput, CmdLog
from .root_cmd import ROOT as root


def toggle_langchain_debug():
    """Activate debug mode."""
    import langchain
    langchain.debug = not langchain.debug

def enable_log_debug():
    # set current log handler to debug
    log = logging.getLogger()
    for handler in log.handlers:
        if isinstance(handler, LogCaptureHandler):
            handler.setLevel(logging.DEBUG)

def toggle_app_debug() -> bool:
    """Toggle debug mode."""
    with global_context() as ctx:
        cfg = ctx.config_manager.config
        if cfg.debug:
            cfg.debug = False
            return False

        cfg.debug = True
        return True

toggle_app_debug()
toggle_langchain_debug()
enable_log_debug()


#WIP:
@root.command
async def toggle_dbg(ctx) -> CallbackOutput:
    """Toggle debug mode."""
    if toggle_app_debug():
        return CmdLog("debug mode activated")
    return CmdLog("debug mode deactivated")


@root.command
async def dap(ctx) -> CallbackOutput:
    """Toggle DAP debugging"""

    if dap_listen():
        return CmdLog("started DAP server")

    return CmdLog("DAP server already started")
