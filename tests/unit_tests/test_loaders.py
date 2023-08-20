"""Test index module"""
import enum
import logging
from random import choice
from string import ascii_lowercase
from pathlib import Path
import instrukt
from unittest.mock import MagicMock

import pytest
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter

from instrukt.indexes.loaders import (DIRECTORY_LOADER, LOADER_MAPPINGS,
                                      detect_file_encodings,
                                      get_loader, splitter_for_file,
                                      Blob,
                                      AutoDirLoader)
"""
Creating an index should:
    - Use the Index model to represent the new index
    - Decide which loader to use based on the file type 
    - Use directory loader for directories
    - Load document(s) into a loader
    - create split text from the document(s)
    - prepare the vectorstore 
    - load the split text into the vectorstore as embeddings
"""

TEST_TEXT = "This is a test text"


def random_string(length=5):
    return ''.join(choice(ascii_lowercase) for _ in range(length))


def random_file_name(length=10, ext=""):
    file_name = random_string(length)
    if bool(ext):
        return file_name + ext
    else:
        return file_name + random_string()




class TestDirectoryLoader:
    """Test the GenericLoader and BlobLoader features"""

    def test_get_directory_loader(self, tmp_path):
        """directory paths should use a directory loader"""
        path = str(tmp_path)
        loader = get_loader(path)
        assert loader is not None
        assert isinstance(loader, DIRECTORY_LOADER[0])

    def test_warning_unknown_encodings(self, caplog):
        caplog.set_level(logging.WARNING)
        pbar = MagicMock()
        examples = Path(__file__).parent / "examples"
        non_utf = examples / "example-non-utf8.txt"
        loader = AutoDirLoader(str(examples), **DIRECTORY_LOADER[1])

        list(loader.lazy_load())
        assert f"Error decoding {non_utf}" in caplog.text



    @pytest.mark.requires("pdfminer")
    @pytest.mark.parametrize("ext, loader_mapping", [
        (".txt", LOADER_MAPPINGS[".txt"][0]),
        (".pdf", LOADER_MAPPINGS[".pdf"][0]),
    ])

    def test_get_loader(self, tmp_path, ext, loader_mapping):
        """file paths should use the correct loader"""
        path = str(tmp_path / f"test{ext}")
        with open(path, "w") as f:
            f.write(TEST_TEXT)
        loader = get_loader(path)
        assert loader is not None
        assert isinstance(loader, loader_mapping)

    def test_splitting_docs(self):
        raise NotImplementedError("duplicate documents when splitting")

@pytest.mark.parametrize("ext",
                         [f".{language.value}" for language in Language] +
                         [f".{random_string()}" for _ in range(5)])
def test_source_code_splitter(ext):
    file_name = random_file_name(ext=ext)
    if ext in Language.__members__.values():
        assert isinstance(
            RecursiveCharacterTextSplitter.from_language(ext),
            RecursiveCharacterTextSplitter)

        lang, spl = splitter_for_file(file_name)
        assert spl == RecursiveCharacterTextSplitter.from_language(lang)

    # non handled
    else:
        with pytest.raises(ValueError):
            RecursiveCharacterTextSplitter.from_language(ext)

@pytest.mark.skip(reason="slow test")
@pytest.mark.requires("chardet")
def test_detect_encoding_timeout(tmpdir: str) -> None:
    path = Path(tmpdir)
    file_path = str(path / "blob.txt")
    # 2mb binary blob
    with open(file_path, "wb") as f:
        f.write(b"\x00" * 2_000_000)

    with pytest.raises(TimeoutError):
        detect_file_encodings(file_path, timeout=1)

    detect_file_encodings(file_path, timeout=10)

@pytest.mark.requires("chardet")
def test_detect_encoding_blob_as_string():
    examples_dir = Path(__file__).parent / "examples"

    with pytest.raises(UnicodeDecodeError):
        b = Blob(path=str(examples_dir / "example-non-utf8.txt"))
        b.as_string()

    b = Blob(path=str(examples_dir / "example-non-utf8.txt"), detect_encoding=True)
    b.as_string()

#TEST:
# def test_detect_files():
#     raise NotImplementedError
#
# def test_detect_mimetypes():
#     raise NotImplementedError 
#
# def test_detect_encodings():
#     raise NotImplementedError
