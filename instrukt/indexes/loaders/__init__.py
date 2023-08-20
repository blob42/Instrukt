from langchain.document_loaders import (
    PDFMinerLoader,
    TextLoader,
)

from .const import DEFAULT_EXCLUDES, DEFAULT_GLOBS, TLoaderType, lang_map
from .dirloader import DIRECTORY_LOADER, AutoDirLoader
from .utils import get_loader, src_by_lang

LOADER_MAPPINGS: dict[str, TLoaderType] = {
    ".txt": (TextLoader, {
        "autodetect_encoding": True
    }, "Text"),
    ".pdf": (PDFMinerLoader, {}, "PDF with PdfMiner"),
    "._dir": DIRECTORY_LOADER
}
"""Document loader tuples in the form (loader_cls, loader_kwargs)"""

__all__ = [
    'LOADER_MAPPINGS', 'DEFAULT_EXCLUDES', 'DEFAULT_GLOBS', 'lang_map',
    'AutoDirLoader', 'src_by_lang', 'get_loader'
]
