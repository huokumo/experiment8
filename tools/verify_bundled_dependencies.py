#!/usr/bin/env python3
"""Verify the dependencies included in the offline teaching ZIP before building."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root/'BUNDLED_DEPENDENCIES.json').read_text())
locked = json.loads((root/'SOURCE_LOCK.json').read_text())
for name, item in manifest['dependencies'].items():
    if item['commit'] != locked[name]['commit']:
        raise RuntimeError('Bundled dependency revision differs from SOURCE_LOCK: '+name)
    for relative, expected in item['files'].items():
        path = (root/relative).resolve()
        if not path.is_relative_to((root/'src'/name).resolve()):
            raise RuntimeError('Invalid dependency path: '+relative)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Bundled dependency changed; preserve and review it: '+relative)
    print(f'{name}: {len(item["files"])} files verified, revision {item["commit"]}')
print('Bundled dependencies ready. Next: bash tools/build.sh')
