// Binary file format is as follows (all numbers are most-significant-byte first)
// 4 bytes specifying num_ops = the number of ops in the file
// 4 bytes specifying the sequence number of the first op in the file
//
// Then num_ops blocks of 16 bytes, each specifying an op
//
// For each op (ranges are 0 index, exclusive of last index)
//
// The first bit is 0 when the operation is normal, 1 when it is a use of the
// rectangle tool (rare)
//
// The lower 31 bits of Bytes 0:4 specify the op's timestamp, as the number of
// milliseconds since the first op was placed
//
// Bytes 4:6 encode the column for the op, and bytes 6:8 encode the row
//
// Bytes 8:11 are garbage except for when the op is an instance of the rectangle
// tool. We stuff both the r1 into these three bytes (each requires 12 bits)
// to save a byte so that the entire operation can fit into 16 bytes
//
// The upper 4 bits of byte 10 encode the lower four bits of c1, and byte 9
// encodes the upper 8. The lower four bits of byte 10 encode the upper four bits
// of r1, and byte 11 encodes the lower 8
//
// Byte 11 encodes the palette_index placed by this op
// Bytes 12 encodes the old palette_index, ie the one *replaced* by this op
// it is garbage when the op is an instance of the rectangle tool
//
// Bytes 13:16 encode the user ID for the OP

pub const BINFILE_NUM_BYTES_FOR_OPCOUNT: u32 = 4;
pub const BINFILE_NUM_BYTES_FOR_STARTING_SEQNO: u32 = 4;
pub const BINFILE_HEADER_BYTES: usize =
    (BINFILE_NUM_BYTES_FOR_OPCOUNT + BINFILE_NUM_BYTES_FOR_STARTING_SEQNO) as usize;
pub const BINFILE_OP_SIZE_IN_BYTES: usize = 16;

pub const WHITE_PALETTE_I: u8 = 31;
pub const PALETTE: [u32; 32] = [
    0x000000, 0x00756F, 0x009EAA, 0x00A368, 0x00CC78, 0x00CCC0, 0x2450A4, 0x3690EA, 0x493AC1,
    0x515252, 0x51E9F4, 0x6A5CFF, 0x6D001A, 0x6D482F, 0x7EED56, 0x811E9F, 0x898D90, 0x94B3FF,
    0x9C6926, 0xB44AC0, 0xBE0039, 0xD4D7D9, 0xDE107F, 0xE4ABFF, 0xFF3881, 0xFF4500, 0xFF99AA,
    0xFFA800, 0xFFB470, 0xFFD635, 0xFFF8B8, 0xFFFFFF,
];
