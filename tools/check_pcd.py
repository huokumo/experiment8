#!/usr/bin/env python3
"""Read a PCL binary PCD header and validate its stored XYZ records."""
import argparse
import json
from pathlib import Path
import numpy as np


def inspect(path):
    header = {}
    with Path(path).open('rb') as stream:
        while True:
            line = stream.readline()
            if not line:
                raise ValueError('PCD header is incomplete')
            parts = line.decode('ascii').strip().split()
            if parts and not parts[0].startswith('#'):
                header[parts[0]] = parts[1:]
            if parts and parts[0] == 'DATA':
                break
        if header['DATA'] != ['binary']:
            raise ValueError('Expected uncompressed binary PCD written by this mapper')
        names, fields = header['FIELDS'], []
        for name, kind, size, count in zip(names, header['TYPE'], header['SIZE'], header['COUNT']):
            kind = {'F': 'f', 'I': 'i', 'U': 'u'}[kind]
            count = int(count)
            fields.append((name, '<'+kind+size) if count == 1 else (name, '<'+kind+size, (count,)))
        dtype = np.dtype(fields)
        data = stream.read()
    count = int(header['POINTS'][0])
    if len(data) != count*dtype.itemsize:
        raise ValueError('PCD binary payload length does not match POINTS')
    if count != int(header['WIDTH'][0])*int(header['HEIGHT'][0]) or count < 1000:
        raise ValueError('Invalid or unexpectedly small PCD dimensions')
    points = np.frombuffer(data, dtype=dtype, count=count)
    xyz = np.column_stack([points[name] for name in ('x', 'y', 'z')])
    if not np.isfinite(xyz).all():
        raise ValueError('Nonfinite PCD coordinates')
    return {'status': 'PASS', 'path': str(path), 'points': count, 'bytes': Path(path).stat().st_size,
            'header': header, 'xyz_min': xyz.min(axis=0).tolist(), 'xyz_max': xyz.max(axis=0).tolist()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--output')
    args = parser.parse_args()
    result = inspect(args.path)
    text = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(text)
    print(text)
