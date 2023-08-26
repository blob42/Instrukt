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
import typing as t

from rich.markdown import Markdown

from ...messages.log import LogLevel, LogMessage
from ...tuilib.strings import INTRO_MESSAGE, TIPS
from ...tuilib.widgets.textlog import RichLogUp

if t.TYPE_CHECKING:
    from ...types import AnyMessage


class ConsoleWindow(RichLogUp):
    """Window with bottom-up scrolling view"""

    def on_instrukt_app_ready(self):
        self.write(Markdown(INTRO_MESSAGE + TIPS),
                   width=self.size.width - 2)

    async def on_instrukt_log_message(self, message: 'AnyMessage') -> None:
        if isinstance(message, LogMessage) and message.level == LogLevel.ERROR:
            exception = message.msg.__class__.__name__
            msg = f"[red bold]({exception})[/]:{message.msg}"
            self.write(msg)
        else:
            self.write(message)

        message.stop()

    #NOTE: write the text once on resize
    # async def on_resize(self):
    #FIXME: find the width of current widget
    # and set it as width of content.
    # notify(str(self.container_viewport))
