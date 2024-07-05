#!/bin/bash

# Ragai - (c) Eric Dodémont, 2024.

# Script which can be used to mount an azure blob container on the local filesystem 'files' directory.

# blobfuse.yaml:
# 
# logging:
#  type: syslog
#  level: log_debug
#
# components:
#   - libfuse
#   - file_cache
#   - attr_cache
#   - azstorage
#
# libfuse:
#   attribute-expiration-sec: 120
#   entry-expiration-sec: 120
#   negative-entry-expiration-sec: 240
#
# file_cache:
#   path: blobfusetmp
#   timeout-sec: 120
#   max-size-mb: 4096
#
# attr_cache:
#   timeout-sec: 7200
#
# azstorage:
#   type: block
#   account-name: bmaeragaisa
#   account-key: xxx
#   endpoint: https://bmaeragaisa.blob.core.windows.net
#   mode: key
#   container: bmae-ragai-blobcontainer

rm -Rf ./blobfusetmp
blobfuse2 mount ./files --config-file=./blobfuse.yaml
