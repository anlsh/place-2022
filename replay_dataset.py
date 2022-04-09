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
parser.add_argument('--check_encoding', required=False, default=False, type=bool,
                    help="""Whether to verify the decoding-encoding operation
                    with each operation. Default false, use only for testing purposes""")

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

    os.makedirs(args.dumpdir, exist_ok=True)
    dumpdir = Path(args.dumpdir)

    metadata = {}

    with open(args.csv) as f:
        # Garbage line describing the "format" which is for losers
        f.readline()

        def dump(prefix, arr, ops_spec):
            """
            arr describes a png to dump.
            ops_spec[1] should be an iterable of binary
            ops_spec[0] should be the sequence number for the first op in ops_spec[1]
            ops_spec[1] should be an iterable of PlaceOps to dump
            """
            if arr is not None:
                im = Image.fromarray(arr)
                im.save(dumpdir / f"{prefix}.png")
            if ops_spec:
                first_seqno, ops = ops_spec
                with open(dumpdir / f"{prefix}.ops", "wb") as f:
                    # Write the number of ops in the file
                    f.write(len(curr_ops).to_bytes(4, byteorder='big'))
                    # Write the sequence number of the first op in the file
                    f.write(first_seqno.to_bytes(4, byteorder='big'))
                    for op in ops:
                        f.write(op.to_binary())


        arr = np.full((SIDE_LENGTH, SIDE_LENGTH, 3), 0xFF, dtype=np.uint8)
        palette_arr = np.full((SIDE_LENGTH, SIDE_LENGTH), 31, dtype=np.uint8)

        dump_i = 1
        seqno = 0
        first_seqno_of_dump = 1
        curr_ops = deque()

        for line in tqdm(f):
            seqno += 1
            op = PlaceOp.from_csv_and_palette_arr(line, palette_arr)
            encoded_op = op.to_binary()

            if args.check_encoding:
                decoded_op = PlaceOp.from_binary(encoded_op)
                if op != decoded_op:
                    raise RuntimeError(f"Coding error:\nOp {vars(op)}\nEncoded as {encoded_op}\ndecoded as {vars(decoded_op)}")

            if op.toff >= args.target_s * 1000:
                break
            if args.dump_s is not None:
                if (op.toff / (args.dump_s * 1000) > dump_i):
                    next_dump_i = math.ceil(op.toff / (1000 * args.dump_s))

                    ops_spec = None
                    if args.dumpops:
                        ops_spec = first_seqno_of_dump, curr_ops
                    dump(
                        "{:06d}".format(dump_i * args.dump_s),
                        arr if args.dumpims else None,
                        ops_spec
                    )
                    first_seqno_of_dump = seqno
                    curr_ops.clear()
                    dump_i = next_dump_i

            if args.dumpops:
                curr_ops.append(op)

            palette_arr[op.r0, op.c0] = op.palette_i - 1
            arr[op.r0, op.c0] = PALETTE[op.palette_i - 1]

        if args.dumplast:
            ops_spec = None
            if args.dumpops:
                ops_spec = first_seqno_of_dump, curr_ops
            dump(
                "final",
                arr if args.dumpops else None,
                ops_spec
            )
