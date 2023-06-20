# Installation Guide

Instrukt is not yet available on package managers. To install it, you can install it from the source code or download the [pre-built pacakges](https://github.com/blob42/Instrukt/releases).

## Minimum requirements

- python 3.9 or newer
- a modern terminal emulator (e.g. alacritty, kitty, st, urxvt, xterm)


## Installing from source

- Clone the repository

- **Make sure you are using the latest pip** `pip install -U pip`
If the installation fails with the package `chromadb` it means
your pip version is old.

- Install poetry with `pip install poetry`
- Install the dependencies with:

```sh
    poetry install -E tools -E loaders
```

## Extra Dependencies
- xsel or xclip for copying messages to the clipboard.
- libmagic (file type detection)
- sqlite (for caching)
- docker: optional for Patreons with access to the docker agent preview.
