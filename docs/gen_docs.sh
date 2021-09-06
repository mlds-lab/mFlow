#!/usr/bin/env bash
sphinx-apidoc -o rst/ ../mFlow
make clean
make html
