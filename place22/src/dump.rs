use crate::place_op::*;
use std::path::Path;
use std::fs::File;
use std::io::BufWriter;

use crate::constants::{EDGE_SIZE, IMAGE_SIZE};
use crate::binary_format::PALETTE;

fn set_pixel_in_pngbuf(row: usize, col: usize, palette_i: usize, buf: &mut [u8; IMAGE_SIZE]) {
    let root_i = (row * EDGE_SIZE) + col;
    let color = PALETTE[palette_i];
    buf[root_i] = ((color & 0xFF0000) >> 16) as u8;
    buf[root_i + 1] = ((color & 0xFF00) >> 8) as u8;
    buf[root_i + 2] = (color & 0xFF) as u8;
}

// I wish I could just use std::io::sink here but it doesn't really work :/
struct NoopWriter {}
impl std::io::Write for NoopWriter {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> { return Ok(0); }
    fn flush(&mut self) -> std::io::Result<()> { Ok(()) }
}

// fn get_pngwriter_for_file(prefix: string, )

pub fn Dump(
    opstream: Box<dyn Iterator<Item = PlaceOp>>,
    dumpdir: &Path,
    target_s: Option<u64>,
    dump_s: Option<u64>,
    dumplast: bool,
    dumpops: bool,
    dumpims: bool
) {
    let mut pngbuf = [0xFF; IMAGE_SIZE];
    let mut palettebuf = [31; IMAGE_SIZE];

    let mut seqno = 1;
    let mut dump_i = 1;
    let mut curr_dump_first_seqno = 1;
    let mut curr_dump_n_ops = 0;

    let tmp_ops_filename = dumpdir.join("tmp.ops");
    let ops_file: Box<dyn std::io::Write> = match dumpops {
        false => Box::new(NoopWriter {}),
        true => Box::new(NoopWriter {})
    };
}
