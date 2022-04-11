use crate::binary_format::{PALETTE, WHITE_PALETTE_I};
use crate::constants::{EDGE_SIZE, IMAGE_SIZE};
use crate::place_op::PlaceOp;
use std::cmp::{max, min};
use std::iter::Iterator;

use std::io::BufRead;
use std::path::Path;

use std::fs::File;
use std::io::BufReader;

use std::collections::HashMap;

use chrono::{DateTime, NaiveDateTime, Utc};

pub struct RawDataFileOpIterator {
    reader: BufReader<File>,
    userhash_to_int: HashMap<String, u64>,
    first_op_time: u64,
    palette_arr: Vec<u8>,
}

impl Iterator for RawDataFileOpIterator {
    type Item = PlaceOp;

    fn next(&mut self) -> Option<Self::Item> {
        let mut buf = String::new();
        match self.reader.read_line(&mut buf) {
            Err(_) => None,
            Ok(_) => {
                // Discard the final trailing newline
                if buf.len() == 0 {
                    return None;
                }
                let parts = csv_line_to_op_parts(&buf);
                let old_palette_i = self.palette_arr[rowcol_to_idx(parts.r0, parts.c0)];
                let uid: u64 = match self.userhash_to_int.get(&parts.user_id) {
                    Some(val) => val.clone(),
                    None => {
                        self.userhash_to_int.insert(parts.user_id, self.userhash_to_int.len().try_into().unwrap()).unwrap()
                    }
                };
                update_palette_arr(parts.palette_i, parts.c0, parts.r0, parts.censor_corner, &mut self.palette_arr);
                match parts.censor_corner.unwrap_or((0, 0)) {
                    (c1, r1) => {
                        return Some(PlaceOp {
                            toff: ((parts.datetime.timestamp() as u64) - self.first_op_time).try_into().unwrap(),
                            censor: parts.censor_corner.is_some(),
                            c0: parts.c0,
                            r0: parts.r0,
                            c1,
                            r1,
                            palette_i: parts.palette_i + 1,
                            old_palette_i: old_palette_i + 1,
                            uint_id: uid as u32,
                        });
                    }
                }
            }
        }
    }
}

struct OpParts {
    datetime: DateTime<Utc>,
    user_id: String,
    palette_i: u8,
    c0: u16,
    r0: u16,
    censor_corner: Option<(u16, u16)>,
}

fn csv_line_to_op_parts(line: &str) -> OpParts {
    let parts: Vec<&str> = line.split(",").collect();


    let c0 = u16::from_str_radix(parts[3].trim_start_matches("\""), 10).unwrap();
    let (r0, corner_coords) = match parts.len() {
        5 => {
            (u16::from_str_radix(parts[4].trim_end_matches("\"\n"), 10).unwrap(), None)
        }
        7 => {
            (
                u16::from_str_radix(parts[4], 10).unwrap(),
                Some((
                    u16::from_str_radix(parts[5], 10).unwrap(),
                    u16::from_str_radix(parts[6].trim_end_matches("\"\n"), 10).unwrap(),
                ))
            )
        }
        x => {
            panic!("Error: The line {} splits into to {} parts != 5 or 7", line, x);
        }
    };

    let naive_datetime =
        NaiveDateTime::parse_from_str(parts[0].trim_end_matches("-07"), "%Y-%m-%d %H:%M:%S%.f").unwrap();
    let datetime = DateTime::<chrono::Utc>::from_utc(naive_datetime, chrono::Utc);

    let palette_i = PALETTE
        .iter()
        .position(|&e| {
            e == u32::from_str_radix(parts[2].trim_start_matches("#"), 16).unwrap()
        })
        .unwrap();

    return OpParts {
        datetime,
        user_id: parts[1].to_string(),
        palette_i: palette_i as u8,
        c0,
        r0,
        censor_corner: corner_coords,
    };
}

fn rowcol_to_idx(row: u16, col: u16) -> usize {
    return (EDGE_SIZE * (row as usize) + (col as usize)) as usize;
}

fn update_palette_arr(palette_i: u8, c0: u16, r0: u16, censor_corner: Option<(u16, u16)>, palette_arr: &mut Vec<u8>) {
    match censor_corner {
        None => {
            palette_arr[rowcol_to_idx(r0, c0)] = palette_i;
        }
        Some((r1, c1)) => {
            for r in min(r0, r1)..max(r0, r1) + 1 {
                for c in min(c0, c1)..max(c0, c1) + 1 {
                    palette_arr[rowcol_to_idx(r, c)] = palette_i;
                }
            }
        }
    }
}

pub fn rawdata_op_stream_from_file(
    path: &Path,
) -> Box<dyn std::iter::Iterator<Item = PlaceOp>> {
    let f = File::open(path).expect("Could not open file for reading");
    let mut buf_reader = BufReader::new(f);

    // Throw away the header line describing the format
    let mut _lb = String::new();
    buf_reader
        .read_line(&mut _lb)
        .expect("Could not read CSV format line???");

    let mut buf = String::new();
    // Get the initial line so that we can set some baselines
    buf_reader
        .read_line(&mut buf)
        .expect("Could not read initial line");

    let start_op_parts = csv_line_to_op_parts(&buf);
    let mut palette_arr = vec![WHITE_PALETTE_I; IMAGE_SIZE];
    let mut userhash_to_int: HashMap<String, u64> = HashMap::new();

    userhash_to_int.insert(start_op_parts.user_id, 0);
    update_palette_arr(start_op_parts.palette_i, start_op_parts.c0, start_op_parts.r0, start_op_parts.censor_corner, &mut palette_arr);

    let first_op = PlaceOp {
        toff: 0,
        censor: start_op_parts.censor_corner.is_some(),
        c0: start_op_parts.c0,
        r0: start_op_parts.r0,
        c1: start_op_parts.censor_corner.unwrap_or((0, 0)).0,
        r1: start_op_parts.censor_corner.unwrap_or((0, 0)).1,
        palette_i: start_op_parts.palette_i,
        old_palette_i: WHITE_PALETTE_I,
        uint_id: 0,
    };

    let rest = RawDataFileOpIterator {
        reader: buf_reader,
        userhash_to_int,
        first_op_time: start_op_parts.datetime.timestamp() as u64,
        palette_arr,
    };
    return Box::new(std::iter::once(first_op).chain(rest));
}
