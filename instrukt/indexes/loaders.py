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
"""Data loaders."""
#TODO: website loader for url paths
#TODO: git loader for git repo paths

import mimetypes
from pathlib import Path
import typing as t

import logging

logger = logging.getLogger(__name__)


from ..types import AnyDict
from ..errors import LoaderError

if t.TYPE_CHECKING:
    from langchain.document_loaders.base import BaseLoader

from langchain.document_loaders import (
        TextLoader,
        PDFMinerLoader,
        DirectoryLoader,
        # CSVLoader,
        # DirectoryLoader,
        # EverNoteLoader,
        # GitLoader,
        # NotebookLoader,
        # OnlinePDFLoader,
        # PythonLoader,
        # UnstructuredEPubLoader,
        # UnstructuredFileLoader,
        # UnstructuredHTMLLoader,
        # UnstructuredMarkdownLoader,
        # UnstructuredODTLoader,
        # UnstructuredPowerPointLoader,
        # UnstructuredWordDocumentLoader,
        # WebLoader,
)

TLoaderType = t.Tuple[
        t.Type["BaseLoader"],
        t.Optional[AnyDict]
        ]

DIRECTORY_LOADER = ( DirectoryLoader, {
        "loader_cls": TextLoader,
        "loader_kwargs": {
            "autodetect_encoding": True
            },
        "use_multithreading": True,
        "max_concurrency": 8, #nb of parallel threads
        "recursive": True,
        "load_hidden": False,
        "silent_errors": False,
        "glob": "**/[!.]*"
    })

"""Document loader tuples in the form (loader_cls, loader_kwargs)"""
LOADER_MAPPINGS: dict[str, TLoaderType] = {
    ".txt": (TextLoader, {"autodetect_encoding": True}),
    ".pdf": (PDFMinerLoader, {}),
    "._dir": DIRECTORY_LOADER
}

def get_loader(path: str) -> t.Optional["BaseLoader"]:
    """Return the loader class for the given path with its default parameters.

    Returns:
        A tuple in the form (loader_cls, loader_kwargs)
    """

    _path = Path(path)

    if _path.is_dir():
        loader_cls, dir_loader_kwargs = DIRECTORY_LOADER
        assert dir_loader_kwargs is not None

        return loader_cls(path, **dir_loader_kwargs)   # type: ignore 

    elif _path.is_file():
        file_ext: t.Optional[str] = _path.suffix.lower()

        if file_ext == '':
            _, file_ext = detect_file_type(path)
            #TODO!: handle mimetype not found

        if file_ext is None:
            raise LoaderError(f"Could not find filetype of {path}")

        file_loader_cls, loader_kwargs = LOADER_MAPPINGS.get(
            file_ext,
            LOADER_MAPPINGS['.txt'] # default is text loader
        )
        logger.debug("file_loader_cls: %s", file_loader_cls)
        return file_loader_cls(path, **loader_kwargs)   # type: ignore 

    return None


def detect_file_type(path: str) -> t.Tuple[str, t.Optional[str]]:
    """Detects the file type and returns the mimetype and file extension.

    Returns:
        A tuple in the form (mimetype, file_ext)
    """
    try:
        import magic
    except ImportError:
        raise LoaderError("magic library is required to detect file type")
    mime = magic.from_file(path, mime=True)
    ext = mimetypes.guess_extension(mime)
    return mime, ext
