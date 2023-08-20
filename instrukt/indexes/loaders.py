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
import itertools
import logging
import mimetypes
import os
import time
import typing as t
from pathlib import Path
from typing import NamedTuple

import chardet
from langchain.document_loaders.blob_loaders.schema import Blob as LcBlob
from langchain.document_loaders.parsers import LanguageParser
from langchain.schema import Document
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter

from ..errors import LoaderError
from ..types import AnyDict, ProgressProtocol
from ..utils.debug import ExecutionTimer

logger = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    from langchain.document_loaders.base import BaseLoader
    from langchain.schema import Document
    from langchain.text_splitter import TextSplitter

from langchain.document_loaders import (
    PDFMinerLoader,
    TextLoader,
)

log = logging.getLogger(__name__)

TLoaderType = t.Tuple[t.Type["BaseLoader"] | t.Type["AutoDirLoader"],
                      t.Optional[AnyDict], str | None]

FileInfoTable = t.Dict[str, "FileInfo"]

Source = str

DEFAULT_EXCLUDES = [
    ".*"
    "**/.git*", ".git*", "__pycache__/**", "**/__pycache__/*"
]
DEFAULT_GLOBS = ["**/[!.]*"]


def path_is_visible(p: Path) -> bool:
    return not any(part.startswith('.') for part in p.parts)


class FileEncoding(NamedTuple):
    """File encoding as the NamedTuple."""

    encoding: str | None
    """The encoding of the file."""
    confidence: float
    """The confidence of the encoding."""
    language: str | None
    """The language of the file."""


def detect_file_encodings(file_path: str,
                          timeout: int = 5) -> list[FileEncoding]:
    """Try to detect file encoding for a file.

    Returns a list of `FileEncoding` tuples with the detected encodings ordered
    by confidence.

    Args:
        file_path: The path to the file to detect the encoding for.
        timeout: The timeout in seconds for the encoding detection.
    """

    def read_and_detect(file_path: str) -> list[dict]:
        with open(file_path, "rb") as f:
            rawdata = f.read()
        return t.cast(list[dict], chardet.detect_all(rawdata))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(read_and_detect, file_path)
        try:
            encodings = future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(
                f"Timeout reached while detecting encoding for {file_path}")

    if all(encoding["encoding"] is None for encoding in encodings):
        raise RuntimeError(f"Could not detect encoding for {file_path}")
    return [
        FileEncoding(**enc) for enc in encodings if enc["encoding"] is not None
    ]


#WIP: autodetect encoding
class Blob(LcBlob):
    detect_encoding: bool = False

    def as_string(self) -> str:
        """Read data as a string."""
        if self.data is None and self.path:
            if not self.detect_encoding:
                with open(str(self.path), "r", encoding=self.encoding) as f:
                    text = f.read()
                    return text
            else:
                text = ""
                try:
                    with open(str(self.path), "r",
                              encoding=self.encoding) as f:
                        text = f.read()
                except UnicodeDecodeError:
                    detected_encodings = detect_file_encodings(self.path)
                    for encoding in detected_encodings:
                        logger.debug(f"Trying encoding: {encoding.encoding}")
                        try:
                            with open(self.path,
                                      encoding=encoding.encoding) as f:
                                text = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                return text
        elif isinstance(self.data, bytes):
            return self.data.decode(self.encoding)
        elif isinstance(self.data, str):
            return self.data
        else:
            raise ValueError(f"Unable to get string for blob {self}")


#TODO!: check FileInfo is instanciated well everywhere
class FileInfo(NamedTuple):
    ext: str | None = None
    """File extension"""

    mime: str | None = None
    """Mime type"""

    encoding: str | None = "utf8"
    """File encoding"""

    lang: str | None = None
    """language: both spoken or programming."""

    splitter: t.Optional["TextSplitter"] = None
    """Asociated splitter"""


#TODO: handle custom loader_cls
class AutoDirLoader:
    """
    AutoDirLoader is a mix of Langchain's DirectoryLoader and GenericLoader.

    It implements same path lazy loading logic from the FileSystemBlobLoader.

    On top of loading files, this class also handles detecting the file type and choosing
    the appropriate text splitter for it. It also saves the file type and any detection
    metadata as document metadata.

    Args:
        path: Path to the directory to load.
        glob: Glob patterns to match files.
        exclude: Glob patterns to exclude files.
        suffixes: File extensions to match.
    """

    def __init__(
        self,
        path: str,
        glob: list[str] = [],
        exclude: list[str] = [],
        suffixes: list[str] = [],
        load_hidden: bool = False,
        max_concurrency: int = 4,
        mimetype_prefixes: list[str] = [],
    ) -> None:
        self.path = path
        self.glob = glob
        self.exclude = exclude
        self.suffixes = suffixes
        self.mimetype_prefixes = mimetype_prefixes
        self.blob_parser: LanguageParser = LanguageParser()
        self.load_hidden = load_hidden
        self.max_concurrency = max_concurrency
        self._pbar: ProgressProtocol | None = None

    @property
    def pbar(self) -> ProgressProtocol | None:
        """The textual progress bar."""
        return self._pbar

    @pbar.setter
    def pbar(self, value: ProgressProtocol):
        self._pbar = value

    def yield_blobs(self) -> t.Iterable[Blob]:
        """Yield blobs for matched paths."""

        def generate_blobs():
            for path in self.yield_paths():
                yield Blob.from_path(path)

        return generate_blobs()

    def lazy_parse(self, blob: Blob) -> t.Iterator["Document"]:

        def generate_docs():
            for doc in self.blob_parser.lazy_parse(blob):
                if self.pbar is not None:
                    self.pbar.update(1)
                yield doc

        return generate_docs()

    def _lazy_load(self) -> t.Iterator["Document"]:
        """Lazy load and parse all files in a directory.

        Args:
            pbar: Textual progress bar to update
        """

        if self.pbar is not None:
            self.pbar.update_msg("parsing files ...")
            self.pbar.update_pbar(total=self.count_matching_paths(),
                                  progress=0)
        for blob in self.yield_blobs():
            try:
                yield from self.lazy_parse(blob)

            except UnicodeDecodeError as e:
                log.warning(f"Error decoding {blob.path}: {str(e)}")
            except Exception as e:
                log.error(f"Error with {blob.path} occurred: {str(e)}")

    def lazy_load(self):
        return self._lazy_load()

    def load_and_split_pbar(self) -> list["Document"]:
        """Overload load and split with auto detection heuristics for content type.
        
        the text_splitter passed in is only used as a last resort if auto detection
        failed at the `load()` stage.
        """
        all_docs: list["Document"] = []

        _for_cnt, docs = itertools.tee(self.lazy_load(), 2)
        doc_count = sum(1 for _ in _for_cnt)

        time.sleep(0.1)
        if self.pbar is not None:
            self.pbar.update_msg("splitting documents ...")
            self.pbar.update_pbar(total=doc_count, progress=0)

        with ExecutionTimer(f"split {doc_count} documents"):

            with concurrent.futures.ProcessPoolExecutor(
                    max_workers=self.max_concurrency) as executor:

                chunksize = 100  # Number of documents to process in each chunk
                results = []
                while True:
                    chunk_docs = list(itertools.islice(docs, chunksize))
                    if not chunk_docs:
                        break
                    results.append(executor.submit(split_documents,
                                                   chunk_docs))

                for future in concurrent.futures.as_completed(results):
                    r = future.result()
                    all_docs.extend(r)
                    if self.pbar is not None:
                        self.pbar.update(len(r))

                #
                # results = executor.map(self.split_documents,
                #                        docs,
                #                        chunksize=100)
                #
                # for r in results:
                #     all_docs.extend(r)
                #     if self.pbar is not None:
                #         self.pbar.update(len(r))

        langs = list(set([doc.metadata["language"] for doc in all_docs]))
        log.info(f"detected languages: {langs}")

        return all_docs

    def accepted_mimetypes(self):
        raise NotImplementedError

    def yield_paths(self) -> t.Iterator[Path]:
        """Returns an iterator over the paths matching the glob pattern."""
        paths: list[Path] = []
        for g in self.glob:
            paths.extend(Path(self.path).glob(g))

        for path in paths:
            if self.exclude:
                if any(
                        fnmatch.fnmatch(str(path), glob)
                        for glob in self.exclude):
                    continue
            if path.is_file():
                if self.suffixes and path.suffix not in self.suffixes:
                    continue
                if not path_is_visible(path.relative_to(
                        self.path)) and not self.load_hidden:
                    continue
                yield path

    def count_matching_paths(self) -> int:
        """Lazy count files that match the pattern without loading to memory."""
        return sum(1 for _ in self.yield_paths())

    def detect_files(self) -> t.Iterator[tuple[Source, FileInfo]]:
        """Detect metadata from a GenericLoader.

        and return an Iterator over src,FileInfoTable."""
        if self.pbar is not None:
            self.pbar.update_pbar(total=self.count_matching_paths(),
                                  progress=0)
        for path in self.yield_paths():
            if path.is_file():
                try:
                    filetype = detect_filetype(str(path))
                    if filetype.mime is not None and not any(
                            filetype.mime.startswith(prefix)
                            for prefix in self.mimetype_prefixes):
                        continue
                    lang, splitter = splitter_for_file(filetype)
                    fi = FileInfo(filetype.ext, filetype.mime,
                                  filetype.encoding, lang, splitter)
                    yield (str(path), fi)
                except LoaderError:
                    log.warning(f"Couldn't guess file type for <{path}>. skip")
                finally:
                    if self.pbar is not None:
                        self.pbar.update(1)


def split_documents(docs: list["Document"]) -> list["Document"]:
    """Split documents with the appropriate splitter.

    This will be called in a process pool executor and should be picklable and not
    rely on any global state or shared memory.
    """
    splitted_docs: list["Document"] = []
    # src_info = detect_documents(docs)

    # splitter_to_docs: dict["TextSplitter", list["Document"]] = {}
    #
    # for doc in docs:
    #     src = doc.metadata["source"]
    #     doc.metadata["language"] = files_info[src].lang
    #     assert src is not None
    #     splitter = files_info[src].splitter
    #     splitter_to_docs.setdefault(splitter, []).append(doc)
    #
    # splitted_docs = []
    # for splitter, splitter_docs in splitter_to_docs.items():
    #     splitted_docs.extend(splitter.split_documents(splitter_docs))

    # redo with simple algorithm
    #BUG: duplicate documents in splitting
    for src, info in detect_documents(docs):
        assert info.splitter is not None
        # find doc in docs
        doc = next((d for d in docs if d.metadata["source"] == src), None)
        if doc is None:
            log.error(f"Couldn't find doc for {src}")
        assert doc is not None
        if info.lang is not None:
            doc.metadata["language"] = info.lang
        splitted_docs.extend(info.splitter.split_documents([doc]))

    return splitted_docs


#TODO: add mimetype and encoding detection
#TODO: detect_filetype uses also mimetype to guess extension, use a single mimetype call
# to guess mime and extension
def detect_documents(
        docs: list["Document"]) -> t.Iterator[tuple[Source, FileInfo]]:
    """Detects the file types of loaded paths."""
    lang_to_splitter: dict[str, "TextSplitter"] = {}

    for d in docs:

        src = d.metadata["source"]
        assert src is not None

        #TODO!: if source/language/content_type already set skip the processsing
        # and just get splitter

        # handle docs already parsed by language parser
        _lang, _content_type = (d.metadata.get("language"),
                                d.metadata.get("content_type"))
        if all((_lang, _content_type)) and isinstance(_lang, Language):
            mime, ext, enc = detect_filetype(src, raise_err=False)
            yield src, FileInfo(
                ext,
                mime,
                enc,
                _lang,
                splitter=RecursiveCharacterTextSplitter.from_language(_lang))

        try:
            ft = detect_filetype(src)

            # if we still don't have a file extension or mime skip this document
            if ft.ext is None and ft.mime is None:
                log.warning(f"Couldn't guess file type for {src}: skipping")
                continue

            lang, splitter = splitter_for_file(ft)

        except LoaderError as e:
            log.warning(f"Couldn't find file type for {src}: skipping...\n{e}")
            continue

        # reuse the same splitter object
        if lang in lang_to_splitter:
            splitter = lang_to_splitter[lang]
        else:
            lang_to_splitter[lang] = splitter

        yield src, FileInfo(ft.ext, ft.mime, ft.encoding, lang, splitter)


def src_by_lang(files: t.Iterator[tuple[Source, FileInfo]],
                count_src: bool = False) -> dict[str, list[str]]:
    """Aggregate sources by language."""
    srcs_by_lang: dict[str, list[str]] = {}
    for src, info in files:
        assert info.lang is not None
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
        "glob": DEFAULT_GLOBS,
        "max_concurrency": cpu_count(),  #nb of parallel threads
        "load_hidden": False,
        "exclude": DEFAULT_EXCLUDES,
        "mimetype_prefixes": ["text/"]
    },
    "Directory")
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
    encoding: str | None


def detect_filetype(path_str: str,
                    raise_err=True,
                    autodecode=False) -> FileType:
    """Returns the file extension of the given path.

    If the file does not have an extension, it tries to detect the file type and returns
    the corresponding extension."""
    path = Path(path_str)
    ext: str | None = path.suffix.lower()

    # first try to guess mime
    mime, encoding = mimetypes.guess_type(path_str)

    if mime is None:
        try:
            import magic
        except ImportError:
            raise LoaderError("magic library is required to detect file type")
        mime = magic.from_file(path_str, mime=True)

    if ext == "":
        ext = mimetypes.guess_extension(mime, )

    if ext is None and mime is None and raise_err:
        raise LoaderError(f"Could not find filetype for {path}")

    if encoding is None and autodecode:
        raise NotImplementedError

    return FileType(mime, ext, encoding)


def get_loader(path: str) -> t.Optional["BaseLoader"]:
    """Return the loader class for the given path with its default parameters.

    Returns:
        A tuple in the form (loader_cls, loader_kwargs)
    """

    _path = Path(path).expanduser()

    if _path.is_dir():
        loader_cls, dir_loader_kwargs, _ = DIRECTORY_LOADER
        assert dir_loader_kwargs is not None

        return loader_cls(path, **dir_loader_kwargs)  # type: ignore

    elif _path.is_file():
        ft = detect_filetype(path)

        file_loader_cls, loader_kwargs, _ = LOADER_MAPPINGS.get(
            ft.ext or "",
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


def splitter_for_file(ft: FileType) -> LangSplitter:
    """Returns (lang, splitter) for the given file extension"""
    lang = ""
    ext = ft.ext
    if ext is not None:
        assert ext.startswith('.'), f"ext should start with . got {ft.ext}"
        lang = lang_map.get(ft.ext)

    # fallback to lang then mime to choose the splitter
    elif ext is None and ft.mime is not None and ft.mime.startswith("text/"):
        lang = "text"

    if lang in list(v.value for v in Language):
        return LangSplitter(
            lang, RecursiveCharacterTextSplitter.from_language(Language(lang)))
    else:
        return LangSplitter("text", RecursiveCharacterTextSplitter())
