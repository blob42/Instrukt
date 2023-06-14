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

from .root_cmd import ROOT as root
from .command import CallbackOutput
import sys

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
