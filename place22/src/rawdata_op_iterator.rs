use std::iter::Iterator;
use crate::place_op::PlaceOp;
use crate::constants::{IMAGE_SIZE, EDGE_SIZE};
use crate::binary_format::{PALETTE, WHITE_PALETTE_I};
use std::cmp::{min,max};

use std::path::Path;
use std::io::{Read, BufRead};

use std::fs::File;
use std::io::BufReader;

use std::collections::HashMap;

use chrono::{NaiveDateTime, DateTime, Utc};

pub struct RawDataFileOpIterator {
    reader:BufReader<File>,
    uid_to_int: HashMap<String, u64>,
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
                let uid: u64 = match self.uid_to_int.get(parts.user_id.as_str()) {
                    Some(val) => { val.clone() },
                    None => {
                        let new_assoc = self.uid_to_int.len() as u64;
                        self.uid_to_int.insert(parts.user_id.clone(), new_assoc);
                        new_assoc
                    }
                };
                update_palette_arr_for_op_parts(&parts, &mut self.palette_arr);
                match parts.censor_corner.unwrap_or((0, 0)) {
                    (c1, r1) => {
                        return Some(
                            PlaceOp {
                                toff: ((parts.datetime.timestamp() as u64) - self.first_op_time) as u32,
                                censor: parts.censor_corner.is_some(),
                                c0: parts.c0,
                                r0: parts.r0,
                                c1,
                                r1,
                                palette_i: parts.palette_i + 1,
                                old_palette_i: old_palette_i + 1,
                                uint_id: uid as u32,
                            }
                        );
                    }
                }
            }
        }
    }
}

struct op_parts {
    datetime:DateTime<Utc>,
    user_id: String,
    palette_i: u8,
    c0: u16,
    r0: u16,
    censor_corner: Option<(u16, u16)>
}

fn csv_line_to_op_parts(
    line: &str
) -> op_parts {
    let parts: Vec<&str> = line.split(",").collect();

    let naive_datetime = NaiveDateTime::parse_from_str(parts[0].trim_end_matches("-07"), "%Y-%m-%d %H:%M:%S%.f").expect(&format!("Failed to parse time string {}, {}DONEZO {}", parts[0], line, line.len()));
    let datetime = DateTime::<chrono::Utc>::from_utc(naive_datetime, chrono::Utc);

    let palette_i = PALETTE.iter().position(|&e|e == u32::from_str_radix(parts[2].trim_start_matches("#"), 16).expect("problem")).unwrap();

    let c0 = u16::from_str_radix(parts[3].trim_start_matches("\""), 10).expect("flub");
    let mut r0 = 0;
    let mut offs: Option<(u16, u16)> = None;

    match parts.len() {
        5 => {
            r0 = u16::from_str_radix(parts[4].trim_end_matches("\"\n"), 10).expect("aluba");
        }
        7 => {
            r0 = u16::from_str_radix(parts[4], 10).expect("duba");
            offs = Some((
                    u16::from_str_radix(parts[5], 10).expect("wubba"),
                    u16::from_str_radix(parts[6].trim_end_matches("\"\n"), 10).expect("GRUUUUB")
                )
            )
        }
        _ => {panic!("Something went seriously wrong parsing")}
    }

    return op_parts {datetime, user_id: parts[1].to_string(), palette_i: palette_i as u8, c0, r0, censor_corner: offs}
}

fn rowcol_to_idx(row: u16, col: u16) -> usize {
    return (EDGE_SIZE * (row as usize) + (col as usize)) as usize
}

fn update_palette_arr_for_op_parts(parts: &op_parts, palette_arr: &mut Vec<u8>) {
    match parts.censor_corner {
        None => {
            palette_arr[rowcol_to_idx(parts.r0, parts.c0)] = parts.palette_i;
        }
        Some((r1, c1)) => {
            for r in min(parts.r0, r1)..max(parts.r0, r1) + 1 {
                for c in min(parts.c0, c1)..max(parts.c0, c1) + 1 {
                    palette_arr[rowcol_to_idx(r, c)] = parts.palette_i;
                }
            }
        }
    }
}

pub fn rawdata_op_stream_from_file(path: &Path)
-> std::iter::Chain<std::iter::Once<PlaceOp>, RawDataFileOpIterator>
{
    let f = File::open(path).expect("Could not open file for reading");
    let mut buf_reader = BufReader::new(f);

    // Throw away the header line describing the format
    let mut _lb = String::new();
    buf_reader.read_line(&mut _lb).expect("Could not read CSV format line???");

    let mut buf = String::new();
    // Get the initial line so that we can set some baselines
    buf_reader.read_line(&mut buf).expect("Could not read initial line");

    let start_op_parts = csv_line_to_op_parts(&buf);
    let mut palette_arr = vec![WHITE_PALETTE_I; IMAGE_SIZE];
    let mut u_id_to_int: HashMap<String, u64> = HashMap::new();

    u_id_to_int.insert(start_op_parts.user_id.clone(), 0);
    update_palette_arr_for_op_parts(&start_op_parts, &mut palette_arr);

    let first_op = PlaceOp { toff: 0, censor: start_op_parts.censor_corner.is_some(), c0: start_op_parts.c0, r0: start_op_parts.r0,
                             c1: start_op_parts.censor_corner.unwrap_or((0, 0)).0,
                             r1: start_op_parts.censor_corner.unwrap_or((0, 0)).1,
                             palette_i: start_op_parts.palette_i, old_palette_i: WHITE_PALETTE_I, uint_id: 0  };

    let start_unix_time = start_op_parts.datetime.timestamp() as u64;

    let rest = RawDataFileOpIterator { reader: buf_reader, uid_to_int: u_id_to_int,
                                   first_op_time: start_unix_time, palette_arr };
    return std::iter::once(first_op).chain(rest);
}
