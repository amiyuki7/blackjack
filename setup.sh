#!/bin/sh

set -e

# Best to have pyenv recognise the version in ./.python-version
python -m venv venv
source venv/bin/activate

pip install pyright black flit
flit install --symlink
