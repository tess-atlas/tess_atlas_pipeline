#!/bin/bash
set -eu

version=$(rsync --version | head -1 | tr -s ' ' | cut -d' ' -f3)
curl -sO https://raw.githubusercontent.com/WayneD/rsync/v${version}/support/rrsync
chmod +x rrsync
