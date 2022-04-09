from PIL import Image
import math
import argparse
import numpy as np
import os
from pathlib import Path
from collections import deque
import json

from tqdm import tqdm

from place_op import PlaceOp

NUM_OPS = 160353104
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
parser.add_argument('dumpdir', type=str,
                    help="Directory to dump files to")
parser.add_argument('--target_s',  required=False, default=math.inf, type=int,
                    help="""Terminate upon reaching this time (in seconds), or
                    at the end if not specified""")
parser.add_argument('--dump_s', required=False, default=None, type=int,
                    help="""'If specified, dump png/ops files for every window
                    of dump_s seconds for which there is data in the dataset.

                    {time}.PNG files will be the state of the canvas after the
                    last operation *before* that time. {time}.ops files will be
                    the sequence of ops in the time range [time-1, time)
                    """)
parser.add_argument('--dumplast', required=False, default=True, type=bool,
                    help="""When true (default), dump unexported png/ops files with
                    filename 'final' upon program termination.""")
parser.add_argument('--dumpops', required=False, default=True, type=bool,
                    help="When true (default), dump ops")
parser.add_argument('--dumpims', required=False, default=True, type=bool,
                    help="When true (default),  dump pngs (default true)")

def main(*, csv, dumpdir, target_s, dump_s, dumplast, dumpops, dumpims, check_encoding):

    os.makedirs(dumpdir, exist_ok=True)
    dumpdir = Path(dumpdir)

    metadata = {}

    with open(csv) as f:
        # Garbage line describing the "format" which is for losers
        f.readline()

        def dump(prefix, arr):
            """
            arr describes a png to dump.
            ops_spec[1] should be an iterable of binary
            ops_spec[0] should be the sequence number for the first op in ops_spec[1]
            ops_spec[1] should be an iterable of PlaceOps to dump
            """
            if arr is not None:
                im = Image.fromarray(arr)
                im.save(dumpdir / f"{prefix}.png")

        arr = np.full((SIDE_LENGTH, SIDE_LENGTH, 3), 0xFF, dtype=np.uint8)
        palette_arr = np.full((SIDE_LENGTH, SIDE_LENGTH), 31, dtype=np.uint8)

        seqno = 0

        dump_i = 1
        curr_dump_first_seqno = 1
        curr_dump_n_ops = 0

        TMP_OPS_FILENAME = dumpdir / f"tmp.ops"
        ops_file = None
        if dumpops:
            with open(TMP_OPS_FILENAME, "w+") as _:
                pass
            ops_file = open(TMP_OPS_FILENAME, "rb+")
            ops_file.write((0).to_bytes(4, byteorder='big'))
            ops_file.write((0).to_bytes(4, byteorder='big'))

        def flushops(prefix, create_new=True):
            nonlocal ops_file
            nonlocal curr_dump_first_seqno
            nonlocal curr_dump_n_ops

            ops_file.seek(0)
            ops_file.write(curr_dump_n_ops.to_bytes(4, byteorder='big'))
            ops_file.write(curr_dump_first_seqno.to_bytes(4, byteorder='big'))

            ops_file.close()
            os.rename(TMP_OPS_FILENAME, dumpdir / f"{prefix}.ops")

            if create_new:
                with open(TMP_OPS_FILENAME, "w+") as _:
                    pass
                ops_file = open(TMP_OPS_FILENAME, "rb+")
                ops_file.write((0).to_bytes(4, byteorder='big'))
                ops_file.write((0).to_bytes(4, byteorder='big'))

        for line in tqdm(f):
            seqno += 1
            op = PlaceOp.from_csv_and_palette_arr(line, palette_arr)
            encoded_op = op.to_binary()

            if op.toff >= target_s * 1000:
                break
            if dump_s is not None:
                if (op.toff / (dump_s * 1000) > dump_i):
                    next_dump_i = math.ceil(op.toff / (1000 * dump_s))

                    prefix = "{:06d}".format(dump_i * dump_s)
                    if dumpims:
                        im = Image.fromarray(arr)
                        im.save(dumpdir / f"{prefix}.png")
                    if dumpops:
                        flushops(prefix)
                        curr_dump_first_seqno = seqno
                        curr_dump_n_ops = 0

                    dump_i = next_dump_i

            if dumpops:
                ops_file.write(op.to_binary())
                curr_dump_n_ops += 1

            palette_arr[op.r0, op.c0] = op.palette_i - 1
            arr[op.r0, op.c0] = PALETTE[op.palette_i - 1]

        if dumplast:
            if dumpims:
                im = Image.fromarray(arr)
                im.save(dumpdir / f"final.png")
            if dumpops:
                flushops("final", False)
        ops_file.close()


args = parser.parse_args()

if __name__ == "__main__":
    # Have to do some argument validation...
    if args.dump_s is not None and args.dump_s <= 0:
        raise RuntimeError("dump_s must be > 0")
    elif not (args.dumpops or args.dumpims):
        raise RuntimeError("Told to dump neither ops nor pngs: waste of time")

    if args.check_encoding:
        print("[WARNING]: Performing encoding checks; this will be slow(er)")
    if not args.dumplast:
        print("[WARNING]: Asked not to dump final state. Are you sure?")

    main(**vars(args))
