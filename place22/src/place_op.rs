use crate::binary_format::BINFILE_OP_SIZE_IN_BYTES;

#[derive(Debug, Eq, PartialEq)]
pub struct PlaceOp {
    pub toff: u32,
    pub censor: bool,
    pub c0: u16,
    pub r0: u16,
    pub c1: u16,
    pub r1: u16,
    pub palette_i: u8,
    pub old_palette_i: u8,
    pub uint_id: u32
}

pub fn buffer_to_op(buf: &[u8; BINFILE_OP_SIZE_IN_BYTES]) -> PlaceOp {
    let toff: u32 = ((buf[0] as u32) << 24) + ((buf[1] as u32) << 16) + ((buf[2] as u32) << 8) + (buf[3] as u32) & !(0x80000000);
    let censor: bool = buf[0] & 0x80 > 0;
    let c0: u16 = ((buf[4] as u16) << 8) + (buf[5] as u16);
    let r0: u16 = ((buf[6] as u16) << 8) + (buf[7] as u16);
    let c1: u16 = ((buf[8] as u16) << 4) + ((buf[9] as u16) >> 4);
    let r1 = (((buf[9] as u16) & 0xF) << 8) + (buf[10] as u16);
    let palette_i = buf[11] as u8;
    let old_palette_i = buf[12] as u8;
    let uint_id: u32 = ((buf[13] as u32) << 16) + ((buf[14] as u32) << 8) + (buf[15] as u32);

    return PlaceOp {
        toff, censor,
        c0, r0, c1, r1,
        palette_i, old_palette_i, uint_id
    };
}

pub fn op_to_binary(op: &PlaceOp) -> [u8; BINFILE_OP_SIZE_IN_BYTES] {
    let mut buf = [0; BINFILE_OP_SIZE_IN_BYTES];

    buf[0] = (((op.toff & 0xFF000000) >> 24) as u8) | ((op.censor as u8) << 7);
    buf[1] = ((op.toff & 0x00FF0000) >> 16) as u8;
    buf[2] = ((op.toff & 0x0000FF00) >> 8) as u8;
    buf[3] = ((op.toff & 0x000000FF)) as u8;

    buf[4] = ((op.c0 & 0xFF00) >> 8) as u8;
    buf[5] = (op.c0 & 0xFF) as u8;
    buf[6] = ((op.r0 & 0xFF00) >> 8) as u8;
    buf[7] = (op.r0 & 0xFF) as u8;

    buf[8] = ((op.c1 & 0xFF0) >> 4) as u8;
    buf[9] = (((op.c1 & 0xF) << 4) as u8) + (((op.r1 & 0xFF00) >> 8) as u8);
    buf[10] = (op.r1 & 0xFF) as u8;

    buf[11] = op.palette_i;
    buf[12] = op.old_palette_i;

    buf[13] = ((op.uint_id & 0xFF0000) >> 16) as u8;
    buf[14] = ((op.uint_id & 0x00FF00) >> 8) as u8;
    buf[15] = ((op.uint_id & 0x0000FF) >> 0) as u8;

    return buf;
}
