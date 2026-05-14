#!/bin/bash

TARGET_DIR="${1:-.}"

find "$TARGET_DIR" -name "*.zip" -type f | while read zipfile; do
    hash=$(sha256sum "$zipfile" | awk '{print $1}')
    touch "${zipfile}.${hash}"
    echo "Created: ${zipfile}.${hash}"
done
