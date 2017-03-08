#!/usr/bin/env bash

cloc --by-file-by-lang --list-file=cloc_include.txt --exclude-list-file=cloc_exclude.txt --out=cloc_report.txt
