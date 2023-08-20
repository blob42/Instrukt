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
"""Root command route for the app."""
from importlib import import_module

from ..commands import CMD_MODULES
from .command import CmdGroup

ROOT: CmdGroup = CmdGroup("root", "root command")
SKIP_COMMAND_TESTS: bool = False


__all__= ['ROOT']

def load_commands():
    for module in CMD_MODULES:
        import_module(f"instrukt.commands.{module}")

# disable loading of commands when running pytest
if not SKIP_COMMAND_TESTS:
    load_commands()
