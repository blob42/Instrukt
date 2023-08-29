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
"""Document loaders utils."""

import concurrent
import itertools
import logging
import mimetypes
import os
import typing as t
from pathlib import Path

import chardet
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter

from ...errors import LoaderError
from .const import lang_map
from .schema import FileEncoding, FileInfo, FileInfoMap, FileType, LangSplitter, Source

if t.TYPE_CHECKING:
    from chardet.resultdict import ResultDict
    from langchain.document_loaders.base import BaseLoader
    from langchain.schema import Document
    from langchain.text_splitter import TextSplitter

log = logging.getLogger(__name__)


def path_is_visible(p: Path) -> bool:
    return not any(part.startswith('.') for part in p.parts)


def batched(iterable: t.Iterable, n: int) -> t.Iterable:
    """Yield batches from an iterable."""
    if n < 1:
        raise ValueError("batch size must be >= 1")
    it = iter(iterable)
    while batch := tuple(itertools.islice(it, n)):
        yield batch


def detect_file_encodings(file_path: str,
                          timeout: int = 5) -> list[FileEncoding]:
    """Try to detect file encoding for a file.

    Returns a list of `FileEncoding` tuples with the detected encodings ordered
    by confidence.

    Args:
        file_path: The path to the file to detect the encoding for.
        timeout: The timeout in seconds for the encoding detection.
    """

    def read_and_detect(file_path: str) -> list["ResultDict"]:
        with open(file_path, "rb") as f:
            rawdata = f.read()
        return chardet.detect_all(rawdata)

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


def splitter_for_file(ft: FileType) -> LangSplitter:
    """Returns (lang, splitter) for the given file extension"""
    lang: str | None = ""
    ext = ft.ext
    if ext is not None:
        assert ext.startswith('.'), f"ext should start with . got {ft.ext}"
        lang = lang_map.get(ext)

    # fallback to lang then mime to choose the splitter
    elif ext is None and ft.mime is not None and ft.mime.startswith("text/"):
        lang = "text"

    if lang in list(v.value for v in Language):
        return LangSplitter(
            lang, RecursiveCharacterTextSplitter.from_language(Language(lang)))
    elif lang is not None:
        return LangSplitter(lang, RecursiveCharacterTextSplitter())
    else:
        return LangSplitter("text", RecursiveCharacterTextSplitter())


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


def src_by_lang(files: t.Iterator[tuple[Source, FileInfo]],
                count_src: bool = False) -> dict[str, list[str]]:
    """Aggregate document sources by language."""
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


def probe_documents(
        docs: t.Iterator["Document"]) -> t.Iterator[tuple[Source, FileInfo]]:
    """Detects various doc metadata for a given iterator of Document."""
    # every language will share the same splitter
    lang_to_splitter: dict[str, "TextSplitter"] = {}

    src_seen: set[str] = set()

    for d in docs:
        src = d.metadata["source"]
        assert src is not None

        if src in src_seen:
            continue
        src_seen.add(src)

        # handle docs already parsed by language parser
        _lang, _content_type = (d.metadata.get("language"),
                                d.metadata.get("content_type"))
        if all((_lang, _content_type)) and isinstance(_lang, Language):
            mime, ext, enc = detect_filetype(src, raise_err=False)
            if _lang in lang_to_splitter:
                splitter = lang_to_splitter[_lang]
            else:
                splitter = RecursiveCharacterTextSplitter.from_language(_lang)
                lang_to_splitter[_lang] = splitter

            yield src, FileInfo(ext, mime, enc, _lang, splitter=splitter)
            continue

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
        else:
            # reuse the same splitter object
            if lang in lang_to_splitter:
                splitter = lang_to_splitter[lang]
            else:
                lang_to_splitter[lang] = splitter

            yield src, FileInfo(ft.ext, ft.mime, ft.encoding, lang, splitter)


def split_documents(
        docs: list["Document"]) -> tuple[list["Document"], FileInfoMap]:
    """Split documents with the appropriate splitter.

    This will be called in a process pool executor and should be picklable and not
    rely on any global state or shared memory.
    """
    splitted_docs: list["Document"] = []
    splitter_to_docs: dict["TextSplitter", list["Document"]] = {}

    _docs, _probed_docs = itertools.tee(docs, 2)
    infomap: FileInfoMap = {
        src: info
        for src, info in probe_documents(_probed_docs)
    }

    for doc in _docs:
        src = doc.metadata["source"]
        assert src is not None
        if infomap.get(src) is None:
            log.warning(f"Skipping {src} as it has no file info")
            continue
        doc.metadata["language"] = infomap[src].lang
        splitter = infomap[src].splitter
        assert splitter is not None
        splitter_to_docs.setdefault(splitter, []).append(doc)

    for splitter, to_split in splitter_to_docs.items():
        splitted_docs.extend(splitter.split_documents(to_split))

    return splitted_docs, infomap


def get_loader(path: str) -> t.Optional["BaseLoader"]:
    """Return the loader class for the given path with its default parameters.

    Returns:
        A tuple in the form (loader_cls, loader_kwargs)
    """
    from .dirloader import DIRECTORY_LOADER
    from .mappings import LOADER_MAPPINGS

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
        log.debug("file_loader_cls: %s", file_loader_cls)
        return file_loader_cls(path, **loader_kwargs)  # type: ignore

    return None


def cpu_count():
    """Return the number of CPUs in the system."""
    try:
        return abs((os.cpu_count() or 0) - 2)
    except Exception:
        return 1
