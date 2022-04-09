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
parser.add_argument('--ensure_encoding', required=False, default=False, type=bool)

args = parser.parse_args()

class PlaceOp:
    def __init__(self, toff, censor, c0, r0, c1, r1, palette_i, old_palette_i):
        self.toff = toff
        self.censor = censor
        self.c0 = c0
        self.r0 = r0
        self.c1 = c1
        self.r1 = r1
        self.palette_i = palette_i
        self.old_palette_i = old_palette_i

    @classmethod
    def from_csv_and_pic(cls, csvline, palette_arr):
        parts = line.split(",")

        toff = int(parts[0])
        censor = (parts[2] == "t")
        c0 = int(parts[3])
        r0 = int(parts[4])
        c1 = int(parts[5])
        r1 = int(parts[6])

        palette_i = int(parts[1])
        old_palette_i = palette_arr[self.c0, self.r0]

        self.uint_id = int(parts[7])

        return cls(toff, censor, c0, r0, c1, r1, palette_i, old_palette_i)

    def to_binary(self,):
        # We fit each operation into 16 bytes
        encoding = bytearray(16)
        # Some things to know for the encoding
        # The max toff (last pixel placed) was 300589892 millis from t=0
        # This required 29 bits, so fit into 4 bytes
        encoding[:4] = self.toff.to_bytes(4, byteorder = 'big')

        # First bit of the encoding encodes whether this operation was a use of
        # the rectangle tool
        encoding[0] |= 8 if self.censor else 0

        # The max coordinate for any of the rows/cols is 2000, which takes 11
        # bits
        # We use 2 bytes for each of c0, r0
        # c1 and r1 will be very infrequently used, so we stuff both into three
        # ybytes
        # TODO Could save 2 bytes relatively easily here
        encoding[4:6] = self.c0.to_bytes(2, byteorder = 'big')
        encoding[6:8] = self.r0.to_bytes(2, byteorder = 'big')

        c1_bytes = self.c1.to_bytes(2, byteorder = 'big')
        r1_bytes = self.r1.to_bytes(2, byteorder = 'big')

        encoding[8] = (c1_bytes[0] << 2) + (c1_bytes[1] >> 2)
        encoding[9] = ((c1_bytes[1] & 3) << 2) + r1_bytes[0]
        encoding[10] = r1_bytes[1]

        # Each palette_i < 32 ie takes 5 bits, we just give each a byte
        # We store both new and old palette_i to make bidirectional playback easier
        encoding[11] = self.palette_i.to_bytes(1, byteorder = 'big')
        encoding[12] = self.old_palette_i.to_bytes(1, byteorder = 'big')

        # max uint_id in dataset is 10381163, requiring 24 bits: so another 3
        # bytes
        encoding[12:16] = self.uint_id.to_bytes(3, byteorder = 'big')

    @classmethod
    def from_binary(cls, bytearr):
        # TODO this is WRONG oh my GOD I'm not accounting for the censor bit!!
        toff = int.from_bytes(bytearr[:4] & 0x8000, byteorder = 'big')
        censor = bool(bytearr[0] & 3)
        c0 = int.from_bytes(bytearr[4:6], byteorder = 'big')
        r0 = int.from_bytes(bytearr[6:8], byteorder = 'big')
        c1 = (encoding[8] << 2) + (encoding[9] >> 2)
        r1 = ((encoding[9] & 0xF) << 4) + encoding[10]
        palette_i = int(encoding[11])
        old_palette_i = int(encoding[12])
        uint_id = int.from_bytes(bytearr[13:], byteorder = 'big')

        return cls(toff, censor, c0, r0, c1, r1, palette_i, old_palette_i)


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
        palette_arr = np.full((SIDE_LENGTH, SIDE_LENGTH), 31, dtype=np.uint8)
        curr_ops = deque()

        dumpdir_path = Path(args.dumpdir) if args.dumpdir else None
        def dump_for_timestamp(arr, timestamp, seqno, curr_ops):
            prefix = "{:012d}".format(timestamp)
            im = Image.fromarray(arr)
            im.save(dumpdir_path / f"{prefix}.png")
            if args.dumpops:
                with open(dumpdir_path / f"{prefix}.ops", "rb") as f:
                    # Write the number of ops in the file
                    f.write(len(curr_ops).to_bytes(4, byteorder='big'))
                    # Write the sequence number of the first op in the file
                    f.write(seqno.to_bytes(4, bytesorder='big'))
                    for op in curr_ops:
                        f.write(op.to_binary())
                curr_ops.clear()

        op = None
        seqno = 0
        for line in tqdm(f):
            seqno += 1
            op = PlaceOp.from_csv_and_palettepic(line, palette_arr)
            encoded_op = op.to_binary()

            if args.ensure_encoding:
                decoded_op = PlaceOp.from_binary(encoded_op)
                if op != decoded_op:
                    raise RuntimeError(f"Coding error:\nOp {op}\nEncoded as {encoded_op}\ndecoded as {decoded_op}")

            if op.toff >= args.target_millis:
                break
            if args.dumpdir and (op.toff / args.dump_millis > dump_i):
                dump_for_timestamp(
                    arr,
                    op.toff // args.dump_millis * args.dump_millis, seqno,
                    curr_ops
                )
                dump_i = math.ceil(op.toff / args.dump_millis)

            if args.dumpops:
                curr_ops.append(encoded_op)
            palette_arr[op.c0, op.r0] = op.palette_i - 1
            arr[op.c0, op.r0] = PALETTE[op.palette_i - 1]

        if args.dumplast:
            dump_for_timestamp(arr, op.toff + 1, seqno, curr_ops)
