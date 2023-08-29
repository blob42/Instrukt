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
"""Directory  Loader."""
#TODO: website loader for url paths
#TODO: git loader for git repo paths

import importlib
import concurrent
import fnmatch
import itertools
import logging
import time
import typing as t
from pathlib import Path

from langchain.document_loaders.blob_loaders.schema import Blob as LcBlob
from langchain.document_loaders.parsers import LanguageParser
from langchain.document_loaders.base import BaseBlobParser

from ...errors import LoaderError
from ...types import ProgressProtocol
from ...utils.debug import ExecutionTimer
from .const import DEFAULT_EXCLUDES, DEFAULT_GLOBS
from .schema import FileInfo, FileInfoMap, Source
from .utils import (
    batched,
    cpu_count,
    detect_file_encodings,
    detect_filetype,
    path_is_visible,
    split_documents,
    splitter_for_file,
    src_by_lang,
)
from .mappings import LOADER_MAPPINGS, PARSER_MAPPINGS

logger = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    from langchain.schema import Document

log = logging.getLogger(__name__)


class Blob(LcBlob):
    detect_encoding: bool = False
    filetype: str = ""

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


#TODO: handle custom loader_cls
#TODO: language parser threshold
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
        self.load_hidden = load_hidden
        self.max_concurrency = max_concurrency
        self._pbar: ProgressProtocol | None = None

        #default blob parser
        self._default_blob_parser: LanguageParser = LanguageParser(parser_threshold=100)


    @property
    def pbar(self) -> ProgressProtocol | None:
        """The textual progress bar."""
        return self._pbar

    @pbar.setter
    def pbar(self, value: ProgressProtocol):
        self._pbar = value

    def get_blob_parser(self, blob: Blob) -> BaseBlobParser:
        """The blob_parser property."""
        if blob.path is None:
            raise ValueError("blobs without paths are not handled")

        ext = Path(blob.path).suffix.lower()
        if ext in PARSER_MAPPINGS:
            parser = PARSER_MAPPINGS[ext]
            return parser.parser_cls(**parser.options)

        return self._default_blob_parser

    def yield_blobs(self) -> t.Iterable[Blob]:
        """Yield blobs for matched paths."""

        def generate_blobs():
            for path in self.yield_paths():
                log.info(f"{path}")
                yield Blob.from_path(path)

        return generate_blobs()

    def lazy_parse(self, blob: Blob) -> t.Iterator["Document"]:
        parser = self.get_blob_parser(blob)

        def generate_docs():
            for doc in parser.lazy_parse(blob):
                if self.pbar is not None:
                    self.pbar.update(1)
                yield doc
            if self.pbar is not None:
                self.pbar.update_pbar(total=None)

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

    def load_and_split(self) -> list["Document"]:
        """Overload load and split with auto detection heuristics for content type.
        
        the text_splitter passed in is only used as a last resort if auto detection
        failed at the `load()` stage.
        """
        all_docs: list["Document"] = []

        # duplicate the iterator for counting
        _for_cnt, docs = itertools.tee(self.lazy_load(), 2)
        doc_count = sum(1 for _ in _for_cnt)
        infomap: FileInfoMap = {}

        time.sleep(0.1)
        if self.pbar is not None:
            self.pbar.update_msg("splitting documents ...")
            self.pbar.update_pbar(total=doc_count, progress=0)

        with ExecutionTimer(f"split {doc_count} documents"):

            with concurrent.futures.ProcessPoolExecutor(
                    max_workers=self.max_concurrency) as executor:

                chunksize = 100  # Number of documents to process in each chunk
                results = []
                for batch in batched(docs, chunksize):
                    results.append(executor.submit(split_documents, batch))

                for future in concurrent.futures.as_completed(results):
                    splitted, info = future.result()
                    all_docs.extend(splitted)
                    infomap.update(info)
                    if self.pbar is not None:
                        self.pbar.update(len(splitted))

        langs = src_by_lang(((k, v) for k, v in infomap.items()),
                            count_src=True)
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

        and return an Iterator over Osrc,FileInfo)."""
        try:
            # try importing magic
            importlib.import_module("magic")
        except ImportError as e:
            from ...tuilib.strings import LIBMAGIC_INSTALL
            raise LoaderError(
                    f"magic library missing:  {e}. {LIBMAGIC_INSTALL}")

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


DIRECTORY_LOADER = (
    AutoDirLoader,
    {
        "glob": DEFAULT_GLOBS,
        "max_concurrency": cpu_count(),  #nb of parallel threads
        "load_hidden": False,
        "exclude": DEFAULT_EXCLUDES,
        "mimetype_prefixes": ["text/", "application/pdf"]
    },
    "Directory")
"""Default configuration for DirectoryLoader."""

# register loader mapping
LOADER_MAPPINGS["._dir"] = DIRECTORY_LOADER
