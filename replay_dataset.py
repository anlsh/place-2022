from PIL import Image
import math
import argparse
import numpy as np

from tqdm import tqdm

SIDE_LENGTH = 2000

PALETTE = [
    0x000000,
    0x00756F,
    0x009EAA,
    0x00A368,
    0x00CC78,
    0x00CCC0,
    0x2450A4,
    0x3690EA,
    0x493AC1,
    0x515252,
    0x51E9F4,
    0x6A5CFF,
    0x6D001A,
    0x6D482F,
    0x7EED56,
    0x811E9F,
    0x898D90,
    0x94B3FF,
    0x9C6926,
    0xB44AC0,
    0xBE0039,
    0xD4D7D9,
    0xDE107F,
    0xE4ABFF,
    0xFF3881,
    0xFF4500,
    0xFF99AA,
    0xFFA800,
    0xFFB470,
    0xFFD635,
    0xFFF8B8,
    0xFFFFFF
]

parser = argparse.ArgumentParser()

parser.add_argument('csv', help='Path to the cleaned csv')
parser.add_argument('outfile', help='Png to export the final png to')
parser.add_argument('--target_seqno', help='Terminate at last frame before @ this seqno', required=False, default=math.inf, type=int)
parser.add_argument('--target_millis', help='Terminate at last frame before this millis', required=False, default=math.inf, type=int)

args = parser.parse_args()

if __name__ == "__main__":

    with open(args.csv) as f:
        f.readline()
        seqno = 1

        arr = np.full((SIDE_LENGTH, SIDE_LENGTH), 0xFFFFFF, dtype=np.int32)

        for line in tqdm(f):
            if seqno >= args.target_seqno:
                break
            seqno += 1
            parts = line.split(",")

            toff = int(parts[0])
            palette_i = int(parts[1])
            censorship = (parts[2] == "t")
            x0 = int(parts[3])
            y0 = int(parts[4])
            x1 = int(parts[5])
            y1 = int(parts[6])
            # uint_id = int(parts[7])
            # seqno = int(parts[8])

            arr[y0, x0] = PALETTE[palette_i - 1]

        im = Image.fromarray(arr)
        im.save(args.outfile)
