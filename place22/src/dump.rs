use crate::place_op::*;
use std::path::Path;
use std::fs::File;
use std::io::{BufWriter, Write, Seek};
use std::cmp::{min,max};

use crate::constants::{EDGE_SIZE, IMAGE_SIZE};
use crate::binary_format::{PALETTE, BINFILE_HEADER_BYTES};

// The idea is to be easily able to switch to a 3-byte rgb encoding
const PNG_PIXEL_BYTES: usize = 4;
const PNG_COLOR_TYPE: png::ColorType = png::ColorType::Rgba;

fn set_pixel_in_pngbuf(row: usize, col: usize, palette_i: u8, buf: &mut [u8; IMAGE_SIZE * PNG_PIXEL_BYTES]) {
    let root_i = ((row * EDGE_SIZE) + col) * PNG_PIXEL_BYTES;
    let color = PALETTE[palette_i as usize];
    buf[root_i] = ((color & 0xFF0000) >> 16) as u8;
    buf[root_i + 1] = ((color & 0xFF00) >> 8) as u8;
    buf[root_i + 2] = (color & 0xFF) as u8;
}

fn dump_png_to_file(pngbuf: &[u8; IMAGE_SIZE * PNG_PIXEL_BYTES], path: &Path) {
    // https://docs.rs/png/latest/png/
    let file = File::create(path).expect("Could not initialize png file for writing");
    let ref mut w = BufWriter::new(file);
    let mut encoder = png::Encoder::new(w, EDGE_SIZE as u32, EDGE_SIZE as u32);

    encoder.set_color(PNG_COLOR_TYPE);
    encoder.set_depth(png::BitDepth::Eight);

    // I hope to be able to comment this entire block
    encoder.set_trns(vec!(0xFFu8, 0xFFu8, 0xFFu8, 0xFFu8));
    encoder.set_source_gamma(png::ScaledFloat::from_scaled(45455)); // 1.0 / 2.2, scaled by 100000
    encoder.set_source_gamma(png::ScaledFloat::new(1.0 / 2.2));     // 1.0 / 2.2, unscaled, but rounded
    let source_chromaticities = png::SourceChromaticities::new(     // Using unscaled instantiation here
        (0.31270, 0.32900),
        (0.64000, 0.33000),
        (0.30000, 0.60000),
        (0.15000, 0.06000)
    );
    encoder.set_source_chromaticities(source_chromaticities);
    // End useless block
    let mut writer = encoder.write_header().unwrap();
    writer.write_image_data(pngbuf).unwrap();
}

fn new_tmpops_writer(
    tmpfile: &Path,
) -> BufWriter<File> {
    // Creates the tmpfile, writes a placeholder header, and returns a writer
    let mut new_writer = BufWriter::new(File::create(tmpfile).expect("Could not create temp ops file"));
    // Write placeholder bytes for the num_ops and starting_seqno, since
    // we don't know the first yet and the second is actually impossible to know
    new_writer.write_all(&[0; BINFILE_HEADER_BYTES]).expect("Could not write placeholder bytes to tmp ops file");
    return new_writer;
}

fn flush_ops_file_and_writer(
    tmpfile: &Path, dst: &Path,
    writer: &mut BufWriter<File>,
    num_ops: u32, starting_seqno: u32,
) {
    // Renames tmpfile to dst and writes the header
    writer.seek(std::io::SeekFrom::Start(0)).expect("Could not seek 0");

    // Man I should really learn to use the byteorder crate
    let mut header = [0; 8];
    header[0] =  ((num_ops & 0xFF000000) >> 24) as u8;
    header[1] =  ((num_ops & 0x00FF0000) >> 16) as u8;
    header[2] =  ((num_ops & 0x0000FF00) >> 8) as u8;
    header[3] =  ((num_ops & 0x000000FF) >> 0) as u8;

    header[4] =  ((starting_seqno & 0xFF000000) >> 24) as u8;
    header[5] =  ((starting_seqno & 0x00FF0000) >> 16) as u8;
    header[6] =  ((starting_seqno & 0x0000FF00) >> 8) as u8;
    header[7] =  ((starting_seqno & 0x000000FF) >> 0) as u8;

    writer.write_all(&header).expect("Could not write header");

    std::fs::rename(tmpfile, dst).expect("Could not move tmpfile to dst");
}

pub fn dump(
    opstream: Box<dyn Iterator<Item = PlaceOp>>,
    dumpdir: &Path,
    target_s: Option<u64>,
    dump_s: Option<u64>,
    dumplast: bool,
    dumpops: bool,
    dumpims: bool
) {
    let mut pngbuf = [0xFF; IMAGE_SIZE * PNG_PIXEL_BYTES];
    // let mut palettebuf = [31; IMAGE_SIZE];

    let mut seqno = 1;
    let mut dump_i = 1;
    let mut curr_dump_first_seqno = 1;
    let mut curr_dump_n_ops = 0;

    let tmp_ops_filename = dumpdir.join("tmp.ops");

    // Oh, how I long for lexical closures :/
    let mut ops_writer = match dumpops {
        false => None,
        true => Some(new_tmpops_writer(&tmp_ops_filename))
    };

    for op in opstream {
        seqno += 1;

        // Can't use "match" here because I need to break from the look
        match target_s {
            None => (),
            Some(target_s) => {
                if op.toff as u64 > target_s * 1000 {
                    break;
                }
            }
        }

        dump_s.map(|dump_s| {
            if op.toff as u64 > dump_s * 1000 * dump_i {
                let next_dump_i = (((op.toff as f64) / ((1000 * dump_s) as f64)).ceil()) as u64;

                // TODO There was some silliness with with strings being moved, figure that out
                let png_name = format!("{:06}.png", dump_i * dump_s);
                let ops_name = format!("{:06}.ops", dump_i * dump_s);

                if dumpims {
                    dump_png_to_file(&pngbuf, dumpdir.join(png_name).as_path());
                }
                match ops_writer {
                    None => (),
                    Some(ref mut writer) => {
                        flush_ops_file_and_writer(
                            &tmp_ops_filename, dumpdir.join(ops_name).as_path(),
                            writer, curr_dump_n_ops, curr_dump_first_seqno);
                        ops_writer = Some(new_tmpops_writer(&tmp_ops_filename));
                        curr_dump_first_seqno = 0;
                        curr_dump_n_ops = 0;
                    }
                }
                dump_i = next_dump_i;
            }
        });

        match ops_writer {
            None => (),
            Some(ref mut writer) => {
                writer.write_all(&op_to_binary(&op)).expect("Could not write op to binary!");
            }
        }
        if !op.censor {
            set_pixel_in_pngbuf(op.r0.into(), op.c0.into(), op.palette_i, &mut pngbuf);
        } else {
            for r in min(op.r0, op.r1)..max(op.r0, op.r1) + 1 {
                for c in min(op.c0, op.c1)..max(op.c0, op.c1) + 1 {
                    set_pixel_in_pngbuf(r.into(), c.into(), op.palette_i, &mut pngbuf);
                }
            }
        }
    }

    if dumplast {
        if dumpims {
            dump_png_to_file(&pngbuf, dumpdir.join("final.png").as_path());
        }
        match ops_writer {
            None => (),
            Some(ref mut writer) => {
                flush_ops_file_and_writer(
                    &tmp_ops_filename, dumpdir.join("final.ops").as_path(),
                    writer, curr_dump_n_ops, curr_dump_first_seqno);
            }
        }
    }
}
