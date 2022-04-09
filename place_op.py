class PlaceOp:
    def __init__(self, toff, censor, c0, r0, c1, r1, palette_i, old_palette_i, uint_id):
        self.toff = toff
        self.censor = censor
        self.c0 = c0
        self.r0 = r0
        self.c1 = c1
        self.r1 = r1
        self.palette_i = palette_i
        self.old_palette_i = int(old_palette_i)
        self.uint_id = uint_id

    @classmethod
    def from_csv_and_palette_arr(cls, csvline, palette_arr):
        parts = csvline.split(",")

        toff = int(parts[0])
        censor = (parts[2] == "t")
        c0 = int(parts[3])
        r0 = int(parts[4])
        c1 = int(parts[5])
        r1 = int(parts[6])

        palette_i = int(parts[1])
        old_palette_i = palette_arr[r0, c0]

        uint_id = int(parts[7])

        return cls(toff, censor, c0, r0, c1, r1, palette_i, old_palette_i, uint_id)

    def __eq__(self, other):
        toff = self.toff == other.toff
        censor = self.censor == other.censor
        c0 = self.c0 == other.c0
        r0 = self.r0 == other.r0
        c1 = self.c1 == other.c1
        r1 = self.r1 == other.r1
        palette_i = self.palette_i == other.palette_i
        old_palette_i = self.old_palette_i == other.old_palette_i
        uint_id = self.uint_id == other.uint_id

        return toff and censor and c0 and r0 and c1 and r1 and palette_i and old_palette_i and uint_id

    def to_binary(self,):
        # We fit each operation into 16 bytes
        encoding = bytearray(16)
        # Some things to know for the encoding
        # The max toff (last pixel placed) was 300589892 millis from t=0
        # This required 29 bits, so fit into 4 bytes
        encoding[:4] = self.toff.to_bytes(4, byteorder = 'big')

        # First bit of the encoding encodes whether this operation was a use of
        # the rectangle tool
        encoding[0] |= 0x80 if self.censor else 0

        # The max coordinate for any of the rows/cols is 2000, which takes 11
        # bits
        # We use 2 bytes for each of c0, r0
        # c1 and r1 will be very infrequently used, so we stuff them both into
        # three bytes
        encoding[4:6] = self.c0.to_bytes(2, byteorder = 'big')
        encoding[6:8] = self.r0.to_bytes(2, byteorder = 'big')

        c1_bytes = self.c1.to_bytes(2, byteorder = 'big')
        r1_bytes = self.r1.to_bytes(2, byteorder = 'big')

        # encoding[8] = (c1_bytes[0] << 4) + (c1_bytes[1] >> 4)
        # encoding[9] = ((c1_bytes[1] & 7) << 4) + r1_bytes[0]
        # encoding[10] = r1_bytes[1]
        encoding[8] = (self.c1 & 0xFF0) >> 4
        # TODO remove
        if r1_bytes[0] != r1_bytes[0] & 0xF:
            raise RuntimeError(f"yo wtf {r1} is way too crazy")
        encoding[9] = ((self.c1 & 0xF) << 4) + r1_bytes[0]
        encoding[10] = r1_bytes[1]

        # Each palette_i < 32 ie takes 5 bits, we just give each a byte
        # We store both new and old palette_i to make bidirectional playback easier
        encoding[11] = self.palette_i.to_bytes(1, byteorder = 'big')[0]
        encoding[12] = self.old_palette_i.to_bytes(1, byteorder = 'big')[0]

        # max uint_id in dataset is 10381163, requiring 24 bits: so another 3
        # bytes
        encoding[13:16] = self.uint_id.to_bytes(3, byteorder = 'big')

        return encoding

    @classmethod
    def from_binary_stream(cls, stream):
        # Will advance the stream by reading 16 bytes
        toff_bytes = stream.read(4)
        toff = int.from_bytes(toff_bytes, byteorder = 'big') & (~0x80000000)
        censor = bool(toff_bytes[0] & 0x80)
        c0 = int.from_bytes(stream.read(2), byteorder = 'big')
        r0 = int.from_bytes(stream.read(2), byteorder = 'big')

        cc_bytes = stream.read(3) # cc for censor coordinates
        c1 = (cc_bytes[0] << 4) + (cc_bytes[1] >> 4)
        r1 = ((cc_bytes[1] & 0xF) << 8) + cc_bytes[2]
        palette_i = int(stream.read(1))
        old_palette_i = int(stream.read(1))
        uint_id = int.from_bytes(stream.read(4), byteorder = 'big')

        return cls(toff, censor, c0, r0, c1, r1, palette_i, old_palette_i, uint_id)
