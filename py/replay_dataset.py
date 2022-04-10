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
from constants import *
from op_filestreams import *

def main(*, opstream, dumpdir, target_s, dump_s, dumplast, dumpops, dumpims, **kwargs):
    os.makedirs(dumpdir, exist_ok=True)
    dumpdir = Path(dumpdir)

    arr = np.full((SIDE_LENGTH, SIDE_LENGTH, 3), 0xFF, dtype=np.uint8)

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

    for op in tqdm(opstream):
        seqno += 1

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

        if not op.censor:
            arr[op.r0, op.c0] = PALETTE[op.palette_i - 1]
        else:
            for r in range(min(op.r0, op.r1), max(op.r0, op.r1) + 1):
                for c in range(min(op.c0, op.c1), max(op.c0, op.c1) + 1):
                    arr[r, c] = PALETTE[op.palette_i - 1]

    if dumplast:
        if dumpims:
            im = Image.fromarray(arr)
            im.save(dumpdir / f"final.png")
        if dumpops:
            flushops("final", False)
    if ops_file is not None:
        ops_file.close()

#############################################
# Begin the start of the interactive script #
#############################################

parser = argparse.ArgumentParser()

parser.add_argument('--ccsv', help='Path to the cleaned csv', default=None)
parser.add_argument('--bin', metavar='binfile', dest='binfile',
                    help='Path to the custom-formatted binary file', default=None)

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
parser.add_argument('--dumpops', required=False, default=False, type=bool,
                    help="When true (default), dump ops")
parser.add_argument('--dumpims', required=False, default=True, type=bool,
                    help="When true (default),  dump pngs (default true)")


args = parser.parse_args()

if __name__ == "__main__":
    if not (args.ccsv or args.binfile):
        raise RuntimeError("Must be provided either a ccsv or binfile")
    elif (args.ccsv and args.binfile):
        raise RuntimeError("Provided with both a ccsv and binfile???")

    # Have to do some argument validation...
    if args.dump_s is not None and args.dump_s <= 0:
        raise RuntimeError("dump_s must be > 0")
    elif not (args.dumpops or args.dumpims):
        raise RuntimeError("Told to dump neither ops nor pngs: waste of time")

    if not args.dumplast:
        print("[WARNING]: Asked not to dump final state. Are you sure?")

    opstream = None
    if args.ccsv:
        opstream = ReducedCSVOpStream(args.ccsv)
    elif args.binfile:
        opstream = BinOpStream(args.binfile)
    main(opstream=opstream, **vars(args))
