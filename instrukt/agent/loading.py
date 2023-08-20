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
"""Instrukt agent loading."""

import importlib
import inspect
import json
import logging
import os
import pkgutil
import sys
from pathlib import Path
from typing import Generator, Optional, Type

from instrukt.config import APP_SETTINGS

from ..context import Context
from ..errors import AgentError
from ..messages.log import LogMessage
from ..schema import AgentManifest
from .base import InstruktAgent

log = logging.getLogger(__name__)

AGENT_MODULES_PATHS = [Path(__file__).parent.parent / "agent_modules",
                      Path(APP_SETTINGS.custom_agents_path)]
sys.path.extend([str(p) for p in AGENT_MODULES_PATHS])
MODULE_ENTRY_POINT = "main.py"
MODULE_MANIFEST = "manifest.json"
IMPL_CLS = InstruktAgent

MSG_MAIN_NOT_FOUND = """
Agent module <{name}> must define a <{mod_entry}> \
and a class that implements <{impl_cls}>."""

class ModuleManager:

    @staticmethod
    def discover(paths: list[str]) -> Generator[str, None, None]:
        """ Discover available agent modules. Agent modules must be python packages.

        If you started the agent module with a dot(.) or underscore(_) it will not be
        discoverable. Useful during development
        """
        for path in paths:
            for _, name, ispkg in pkgutil.iter_modules([str(path)]):
                if not ispkg:
                    raise ValueError(f"Agent module <{name}> must be a package")

                if name.startswith(".") or name.startswith("_"):
                    continue

                yield name

    @staticmethod
    def list_modules() -> Generator[str, None, None]:
        """List all available agent modules."""
        yield from ModuleManager.discover(AGENT_MODULES_PATHS)

    @staticmethod
    def get_manifest(name: str) -> AgentManifest:
        """Get the manifest of an agent module.

        Returns:
            The manifest as a dictionary.

        Raises:
            ValueError: If the agent module does not have a manifest.
        """
        for path in AGENT_MODULES_PATHS:
            os.path.join(path, name)
            manifest_path = os.path.join(path, name, MODULE_MANIFEST)
            if os.path.isfile(manifest_path):
                with open(manifest_path, "r") as manifest_file:
                    manifest = AgentManifest(**json.load(manifest_file))
                    assert manifest.name == name, f"Agent module <{name}> must have the \
    same name as the agent's python package. Got <{manifest.name}> instead."
                    return manifest
        raise ValueError(f"Agent module <{name}> does not have a manifest")

    @staticmethod
    def verify_module(name: str) -> Type[InstruktAgent]:
        """Verify that an agent module is valid.

        Returns:
            The agent class if the module is valid.

        Raises:
            ValueError: If the module is not valid.
        """
        for path in AGENT_MODULES_PATHS:
            mod_path = os.path.join(path, name)

            # must be a package
            if not os.path.isdir(mod_path):
                continue

            # the package must have a main.py file
            entry_mod = os.path.join(mod_path, MODULE_ENTRY_POINT)
            if not os.path.isfile(entry_mod):
                continue
            
            # the main.py file must have a class the implements InstruktAgent class
            mod = importlib.import_module(f"{name}.{MODULE_ENTRY_POINT[:-3]}")
            for _, agent_cls in inspect.getmembers(mod, inspect.isclass):
                if issubclass(agent_cls, InstruktAgent) and agent_cls is not InstruktAgent:

                    # get the name and description attribute from the subclass
                    agent_name = getattr(agent_cls, "name", None)
                    agent_description = getattr(agent_cls, "description", None)

                    assert agent_name is not None, f"Agent <{name}> must have a \
                                                    name attribute"
                    assert agent_description is not None, f"Agent <{name}> must \
                                                            have a description attribute"

                    # agent name must be the same as agent package
                    pkg_ns_path = f"{path}.{name}"
                    if agent_name != name:
                        raise ValueError(f"Agent <{name}> must have the same name \
                                        as the agent's python package <{pkg_ns_path}>. \
                                        Got <{agent_name}> instead.")

                    return agent_cls

        else:
            raise ValueError(f"Agent <{name}> must contain a class that implements \
                                 implements {IMPL_CLS}.")



class AgentLoader:
    """Handles agent loading"""

    @staticmethod
    def load_agent(name: str, ctx: Context) -> Optional[InstruktAgent]:
        """Load an agent module by name.

        The agent must be a subdirectory of the agent_modules directory and
        MUST implement the InstruktAgent base class.
        """
        # try to load agent commands first
        try:
            importlib.import_module(
                "{}.commands".format(name))
            msg = LogMessage.info("Loaded [b]{}[/] commands.".format(name))
            ctx.notify(msg)
        except ImportError:
            pass
        agent_class = ModuleManager.verify_module(name)
        try:
            agent = agent_class.load(ctx)
        except Exception as e:
            raise AgentError(f"Failed to load agent <{name}>:\n {e}")

        return agent
