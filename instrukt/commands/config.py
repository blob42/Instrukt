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
"""Config commands"""

from ..context import Context
from .command import CallbackOutput, CmdGroup, CmdLog
from .root_cmd import ROOT as root


@root.group(name="config")
class Config(CmdGroup):
    """Config commands."""

    @staticmethod
    async def cmd_show(ctx: Context) -> CallbackOutput:
        """Show the current config."""
        return ctx.config_manager.config.dict()

    #TODO: async catch errors
    @staticmethod
    async def cmd_save(ctx: Context) -> CallbackOutput:
        """Save the current config."""
        ctx.config_manager.save_config()
        return CmdLog("Config saved.")
