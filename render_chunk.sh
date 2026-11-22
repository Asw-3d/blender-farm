#!/bin/bash
# Render satu rentang frame saja. Pakai: ./render_chunk.sh <awal> <akhir> [pct]
set -e
cd "$(dirname "$0")/scene"
RENDER_PCT="${3:-50}" blender -b -P scene.py -- anim "$1" "$2"
ls frames | wc -l
