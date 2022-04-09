from place_op import PlaceOp
from constants import *

class ReducedCSVOpStream:
    # Meant to read place2022_final.csv
    def __init__(self,filename,):
        self.filename = filename
        self.palette_arr = np.full((SIDE_LENGTH, SIDE_LENGTH), 31, dtype=np.uint8)
    def __iter__(self,):
        with open(self.filename, "r") as f:
            # Throw away the single line describing the columns
            f.readline()
            for line in f:
                op = PlaceOp.from_csv_and_palette_arr(line, self.palette_arr)
                self.palette_arr[op.r0, op.c0] = op.palette_i
                yield op

class BinOpStream:
    # Meant to read my custom binary format
    def __init__(filename,):
        self.filename = filename
    def __iter__(self,):
        with open(self.filename, "rb") as f:
            n_ops = int.from_bytes(f.read(4), byteorder = 'big')

            for _ in range(n_ops):
                yield PlaceOp.from_binary_stream(f)
