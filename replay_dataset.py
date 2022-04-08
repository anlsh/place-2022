from PIL import Image
import math
import argparse
import numpy as np
import os
from pathlib import Path
from collections import deque

from tqdm import tqdm

SIDE_LENGTH = 2000

PALETTE = np.array([
    [0x00, 0x00, 0x00],
    [0x00, 0x75, 0x6F],
    [0x00, 0x9E, 0xAA],
    [0x00, 0xA3, 0x68],
    [0x00, 0xCC, 0x78],
    [0x00, 0xCC, 0xC0],
    [0x24, 0x50, 0xA4],
    [0x36, 0x90, 0xEA],
    [0x49, 0x3A, 0xC1],
    [0x51, 0x52, 0x52],
    [0x51, 0xE9, 0xF4],
    [0x6A, 0x5C, 0xFF],
    [0x6D, 0x00, 0x1A],
    [0x6D, 0x48, 0x2F],
    [0x7E, 0xED, 0x56],
    [0x81, 0x1E, 0x9F],
    [0x89, 0x8D, 0x90],
    [0x94, 0xB3, 0xFF],
    [0x9C, 0x69, 0x26],
    [0xB4, 0x4A, 0xC0],
    [0xBE, 0x00, 0x39],
    [0xD4, 0xD7, 0xD9],
    [0xDE, 0x10, 0x7F],
    [0xE4, 0xAB, 0xFF],
    [0xFF, 0x38, 0x81],
    [0xFF, 0x45, 0x00],
    [0xFF, 0x99, 0xAA],
    [0xFF, 0xA8, 0x00],
    [0xFF, 0xB4, 0x70],
    [0xFF, 0xD6, 0x35],
    [0xFF, 0xF8, 0xB8],
    [0xFF, 0xFF, 0xFF]
], dtype=np.uint8)

parser = argparse.ArgumentParser()

parser.add_argument('csv', help='Path to the cleaned csv')
# parser.add_argument('outfile', help='Png to export the final png to')
# parser.add_argument('--target_seqno', help='Terminate at last frame before @ this seqno', required=False, default=math.inf, type=int)
parser.add_argument('--target_millis', help='Terminate at last frame before this millis', required=False, default=math.inf, type=int)

# Args concerning dumps to png files... christ I'm gonna kill my storage
parser.add_argument('--dump_millis', required=False, default=None, type=int)
parser.add_argument('--dumpdir', required=False, default=None, type=str)
parser.add_argument('--dumplast', required=False, default=True, type=bool)
parser.add_argument('--dumpops', required=False, default=None, type=bool)

args = parser.parse_args()

if __name__ == "__main__":

    # Have to do some argument validation...
    if bool(args.dump_millis) != bool (args.dumpdir):
        raise RuntimeError("DumpDir and dumpmillis must both be specified")
    if args.dump_millis == 0:
        raise RuntimeError("Dumping every 0 millis... Not even defined!")
    elif args.dumpops and not args.dumpdir:
        raise RuntimeError("NoDumplast and/or dumpops should only be set when dumping!")

    if args.dumpdir:
        os.makedirs(args.dumpdir, exist_ok=False)

    with open(args.csv) as f:
        # Garbage line describing the "format" which is for losers
        f.readline()
        dump_i = 0

        arr = np.full((SIDE_LENGTH, SIDE_LENGTH, 3), 0xFF, dtype=np.uint8)
        curr_ops = deque()

        dumpdir_path = Path(args.dumpdir) if args.dumpdir else None
        def dump_for_timestamp(arr, timestamp, curr_ops):
            prefix = "{:012d}".format(timestamp)
            im = Image.fromarray(arr)
            im.save(dumpdir_path / f"{prefix}.png")
            if args.dumpops:
                with open(dumpdir_path / f"{prefix}.ops", "w+") as f:
                    for line in curr_ops:
                        f.write(f"{line}\n")
                curr_ops.clear()


        toff = palette_i = censor = x0 = y0 = x1 = y1 = seqno = None

        for line in tqdm(f):
            parts = line.split(",")

            toff = int(parts[0])
            palette_i = int(parts[1])
            censorship = (parts[2] == "t")
            x0 = int(parts[3])
            y0 = int(parts[4])
            x1 = int(parts[5])
            y1 = int(parts[6])
            # uint_id = int(parts[7])
            seqno = int(parts[8])

            if toff >= args.target_millis:
                break
            if args.dumpdir and (toff / args.dump_millis > dump_i):
                dump_for_timestamp(
                    arr,
                    toff // args.dump_millis * args.dump_millis,
                    curr_ops
                )
                dump_i = math.ceil(toff / args.dump_millis)

            if args.dumpops:
                curr_ops.append(line)
            arr[y0, x0] = PALETTE[palette_i - 1]

        if args.dumplast:
            dump_for_timestamp(arr, toff + 1, curr_ops)
