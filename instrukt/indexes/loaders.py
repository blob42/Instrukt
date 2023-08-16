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

import concurrent
import fnmatch
import logging
import mimetypes
import os
import time
import timeit
import typing as t
from itertools import chain
from pathlib import Path
from typing import NamedTuple

from langchain.schema import Document
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter
from textual.widgets import ProgressBar

from ..errors import LoaderError
from ..types import AnyDict, ProgressProtocol
from ..utils.debug import ExecutionTimer

logger = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    from langchain.document_loaders.base import BaseLoader
    from langchain.schema import Document
    from langchain.text_splitter import TextSplitter

from langchain.document_loaders import (
    DirectoryLoader,
    PDFMinerLoader,
    TextLoader,
)

log = logging.getLogger(__name__)

TLoaderType = t.Tuple[t.Type["BaseLoader"], t.Optional[AnyDict], str | None]

FileInfoMap = t.Dict[str, "FileInfo"]

Source = str


DEFAULT_EXCLUDES = [
    "**/*.pyc", "**/*.pyo", "**/__pycache__", "**/.git", "**/*.jpg",
    "**/*.jpeg", "**/*.png", "**/*.gif", "**/*.mp3", "**/*.mp4",
    "**/*.avi", "**/*.mov"
        ]


def path_is_visible(p: Path) -> bool:
    return not any(part.startswith('.') for part in p.parts)



class FileInfo(NamedTuple):
    ext: str
    lang: str | None
    splitter: "TextSplitter"




class AutoDirLoader(DirectoryLoader):
    """
    AutoDirLoader class that extends DirectoryLoader from Langchain.

    On top of loading files, this class also handles detecting the file type and choosing
    the appropriate text splitter for it. It also saves the file type and any detection
    metadata as document metadata.
    """
    def __init__(self,
                 *args,
                 glob: list[str],
                 exclude: list[str] = [],
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.glob = glob  # type: ignore
        self.exclude = exclude

    def load_parallel(self, pbar: ProgressProtocol) -> list["Document"]:
        """Load all files in directory in parallel and try detect the content type.

        Args:
            pbar: Textual progress bar to update
        """
        p = Path(self.path)
        docs: list["Document"] = []
        items: list[Path] = []

        if self.recursive:
            for g in self.glob:
                items.extend(p.rglob(g))

        else:
            for g in self.glob:
                items.extend(p.glob(g))

        # Exclude patterns
        for pattern in self.exclude:
            items = [
                item for item in items
                if not fnmatch.fnmatch(str(item), pattern) and item.is_file() and (
                    path_is_visible(item.relative_to(p)) or self.load_hidden)
            ]  # type: ignore

        pbar.update_pbar(total=len(items), progress=0)
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_concurrency) as executor:
            executor.map(lambda i: self.load_file(i, p, docs, pbar), items)

        return docs

    def load_and_split_parallel(
        self,
        pbar: ProgressProtocol,
    ) -> list["Document"]:
        """Overload load and split with auto detection heuristics for content type.
        
        the text_splitter passed in is only used as a last resort if auto detection
        failed at the `load()` stage.
        """
        all_docs: list["Document"] = []

        time.sleep(0.1)
        pbar.update_msg("loading documents ...")
        #NOTE: IO bound section (loading)
        with ExecutionTimer("load documents"):
            docs = self.load_parallel(pbar)

        # Get unique sources from the loaded documents
        sources = list(
            set([
                doc.metadata["source"] for doc in docs
                if doc.metadata["source"] is not None
            ]))

        time.sleep(0.1)
        pbar.update_msg("splitting documents ...")
        pbar.update_pbar(total=len(docs), progress=0)
        #NOTE: CPU bound section (splitting)
        with ExecutionTimer(f"split {len(docs)} documents"):
            with concurrent.futures.ProcessPoolExecutor(
                    max_workers=self.max_concurrency) as executor:
                source_docs = {}
                for source in sources:
                    source_docs.setdefault(source, []).extend([
                        doc for doc in docs if doc.metadata["source"] == source
                    ])

                results = executor.map(self.split_documents,
                                       source_docs.values(),
                                       chunksize=100)

                #update the progress as results are received
                for r in results:

                    pbar.update(len(r))
                    all_docs.extend(r)

        langs = list(
            set([doc.metadata["language"] for doc in all_docs]))
        log.debug(f"detected languages: {langs}")

        return all_docs

    def split_documents(self, docs: list["Document"]) -> list["Document"]:
        """Split documents with the appropriate splitter.

        This will be called in a process pool executor and should be picklable and not
        rely on any global state or shared memory.
        """
        files_info = detect_documents(docs)

        # group documents by splitter
        splitter_to_docs: dict["TextSplitter", list["Document"]] = {}
        for doc in docs:
            src = doc.metadata["source"]
            doc.metadata["language"] = files_info[src].lang
            assert src is not None
            splitter = files_info[src].splitter
            splitter_to_docs.setdefault(splitter, []).append(doc)

        # Split documents
        splitted_docs = []
        for splitter, splitter_docs in splitter_to_docs.items():
            splitted_docs.extend(splitter.split_documents(splitter_docs))

        return splitted_docs

def detect_documents(docs: list["Document"]) -> dict[Source, FileInfo]:
    """Detects the file types of loaded paths."""
    fi: dict[Source, FileInfo] = {}
    lang_to_splitter: dict[str, "TextSplitter"] = {}
    for d in docs:
        src = d.metadata["source"]

        assert src is not None
        try:
            ext = get_file_ext(src)
        except LoaderError as e:
            log.warning(
                f"Couldn't guess file type for {src}: fallback to text")
            ext = ""
            lang, splitter = LangSplitter("text",
                                          RecursiveCharacterTextSplitter())
        else:
            lang, splitter = splitter_for_file(ext)
        if lang in lang_to_splitter:
            splitter = lang_to_splitter[lang]
        else:
            lang_to_splitter[lang] = splitter

        fi[src] = FileInfo(ext, lang, splitter)

    return fi



def src_by_lang(fi: FileInfoMap, count_src: bool = False) -> dict[str, list[str]]:
    """Aggregate file paths by language."""
    srcs_by_lang: dict[str, list[str]] = {}
    for src, info in fi.items():
        lang = info.lang
        if lang in srcs_by_lang:
            srcs_by_lang[lang].append(src)
        else:
            srcs_by_lang[lang] = [src]
    if count_src:
        srcs_by_lang = {lang: len(srcs) for lang, srcs in srcs_by_lang.items()}
    return srcs_by_lang
    



def cpu_count():
    """Return the number of CPUs in the system."""
    try:
        return abs((os.cpu_count() or 0) - 2)
    except Exception:
        return 1


DIRECTORY_LOADER = (
    AutoDirLoader,
    {
        "loader_cls":
        TextLoader,
        "loader_kwargs": {
            "autodetect_encoding": True
        },
        "use_multithreading":
        True,
        "max_concurrency":
        cpu_count(),  #nb of parallel threads
        "recursive":
        True,
        "load_hidden":
        False,
        "silent_errors":
        False,
        "glob": ["**/[!.]*"],
        "exclude": DEFAULT_EXCLUDES, 
        }, "Directory")
"""Document loader tuples in the form (loader_cls, loader_kwargs)"""
LOADER_MAPPINGS: dict[str, TLoaderType] = {
    ".txt": (TextLoader, {
        "autodetect_encoding": True
    }, "Text"),
    ".pdf": (PDFMinerLoader, {}, "PDF with PdfMiner"),
    "._dir": DIRECTORY_LOADER
}



class LangSplitter(t.NamedTuple):
    lang: str
    """Langchain text splitter -> Language"""

    splitter: "TextSplitter"


class FileType(t.NamedTuple):
    mime: str
    ext: str | None


def detect_path_filetype(path: str) -> FileType:
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
    return FileType(mime, ext)


def get_file_ext(path_str: str) -> str:
    """Returns the file extension of the given path.

    If the file does not have an extension, it tries to detect the file type and returns
    the corresponding extension."""
    path = Path(path_str)
    file_ext: str | None = path.suffix.lower()

    if file_ext == '':
        #TODO!: handle mimetype not found
        _, file_ext = detect_path_filetype(path_str)

    if file_ext is None:
        raise LoaderError(f"Could not find filetype of {path}")
    return file_ext


def get_loader(path: str) -> t.Optional["BaseLoader"]:
    """Return the loader class for the given path with its default parameters.

    Returns:
        A tuple in the form (loader_cls, loader_kwargs)
    """

    _path = Path(path)

    if _path.is_dir():
        loader_cls, dir_loader_kwargs, _ = DIRECTORY_LOADER
        assert dir_loader_kwargs is not None

        return loader_cls(path, **dir_loader_kwargs)  # type: ignore

    elif _path.is_file():
        file_ext = get_file_ext(path)

        file_loader_cls, loader_kwargs, _ = LOADER_MAPPINGS.get(
            file_ext,
            LOADER_MAPPINGS['.txt']  # default is text loader
        )
        logger.debug("file_loader_cls: %s", file_loader_cls)
        return file_loader_cls(path, **loader_kwargs)  # type: ignore

    return None


lang_map = {
    '.py': 'python',
    '.js': 'javascript',
    '.c': 'c',
    '.cpp': 'cpp',
    '.java': 'java',
    '.rs': 'rust',
    '.go': 'go',
    '.html': 'html',
    '.css': 'css',
    '.json': 'json',
    '.xml': 'xml',
    '.yaml': 'yaml',
    '.toml': 'toml',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'bash',
    '.fish': 'bash',
    '.md': 'markdown',
    '.markdown': 'markdown',
    '.tex': 'tex',
    '.txt': 'text',
}


def splitter_for_file(ext: str) -> LangSplitter:
    """Returns (lang, splitter) for the given file extension"""
    assert ext.startswith('.')
    lang = lang_map.get(ext)
    if lang in list(v.value for v in Language):
        return LangSplitter(
            lang, RecursiveCharacterTextSplitter.from_language(Language(lang)))
    else:
        return LangSplitter("text", RecursiveCharacterTextSplitter())
