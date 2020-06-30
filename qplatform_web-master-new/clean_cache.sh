#!/usr/bin/env bash

find ./ -name "__pycache__" | xargs rm -rf
find ./ -name "_build" | xargs rm -rf
find ./ -name "pip-wheel-metadata" | xargs rm -rf
find ./ -name ".mypy_cache" | xargs rm -rf
