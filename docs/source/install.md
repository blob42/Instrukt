# Installation Guide

Instrukt is not yet available on package managers. To install it, you can install it from the source code or download the [pre-built pacakges](https://github.com/blob42/Instrukt/releases).

## Minimum requirements

- Python 3.9 or newer
- a modern terminal emulator (e.g. alacritty, kitty, st, urxvt, xterm)

## Easy install from pip repository

`pip install instrukt[all]`

- For indexes with local embeddings, you need to install the `local` extra.

`pip install instrukt[local]`

## Installing from source

- Clone the repository

- **Make sure you are using the latest pip** `pip install -U pip`
If the installation fails with the package `chromadb` it means
your pip version is old.

- Install poetry with `pip install poetry`
- To do a comprehensive install with all features use:

```sh
    poetry install -E all
```

## Extra Dependencies
- xsel or xclip for copying messages to the clipboard.
- libmagic: file type detection
- sqlite: caching
- docker: [optional] for Patreons with access to the docker based agents.

