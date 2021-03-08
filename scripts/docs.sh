#!/bin/bash

set -eu
poetry install
sphinx-apidoc -f -o ./docs .
sphinx-build -b singlehtml ./docs ./docs/_build
