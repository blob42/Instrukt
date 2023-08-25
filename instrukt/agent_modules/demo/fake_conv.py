##
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz> . All rights reserved.
##
##  SPDX-License-Identifier: AGPL-3.0-or-later
##
##  This file is part of Instrukt.
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU Affero General Public License as
##  published by the Free Software Foundation, either version 3 of the
##  License, or (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU Affero General Public License for more details.
##
##  You should have received a copy of the GNU Affero General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
"""Fake conversation for testing."""
import json

from langchain.schema import messages_from_dict

print(__file__)

# file is at same path as current module
cur_dir = __file__.rpartition("/")[0]
CONV_FILE = f"{cur_dir}/fake_conv.json"



def get_chat_messages():
    """Load memory from fake conversation json"""
    with open(CONV_FILE, "r") as conv_file:
        conv_dict = json.load(conv_file)
        messages = messages_from_dict(conv_dict)
    return messages
