use std::iter::Iterator;

use crate::place_op::{buffer_to_op, PlaceOp};
use std::io::Read;
use std::path::Path;

use std::fs::File;
use std::io::BufReader;

pub struct BinaryFileOpIterator {
    reader: BufReader<File>,
    n_expected_ops: u32,
    n_ops_read: u32,
}

impl Iterator for BinaryFileOpIterator {
    type Item = PlaceOp;

    fn next(&mut self) -> Option<Self::Item> {
        if self.n_ops_read == self.n_expected_ops {
            return None;
        }
        // It's possible this buffer should actually be declared somewhere else
        // to cut down allocations? Or maybe this is already fine?
        let mut buf = [0; 16];
        self.reader
            .read_exact(&mut buf)
            .expect("Fell off the end of the buffer!");
        self.n_ops_read += 1;
        return Some(buffer_to_op(&buf));
    }
}

pub fn binary_op_stream_from_file(path: &Path) -> BinaryFileOpIterator {
    let f = File::open(path).expect("Could not open file for reading");
    let mut buf_reader = BufReader::new(f);

    let mut sbuf = [0; 4];
    buf_reader
        .read_exact(&mut sbuf)
        .expect("Could not read the size");

    let num_ops: u32 = ((sbuf[0] as u32) << 24)
        + ((sbuf[1] as u32) << 16)
        + ((sbuf[2] as u32) << 8)
        + (sbuf[3] as u32);

    // Disregard the starting seqno
    buf_reader
        .read_exact(&mut sbuf)
        .expect("Could not read the starting seqno");

    return BinaryFileOpIterator {
        reader: buf_reader,
        n_expected_ops: num_ops,
        n_ops_read: 0,
    };
}
