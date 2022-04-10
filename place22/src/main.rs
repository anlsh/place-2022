use clap::{ArgGroup, Parser};
use op_iterators::binary_op_stream_from_file;
use std::path::Path;
use std::iter::Iterator;

mod binary_format;
mod op_iterators;
mod place_op;
mod dump;
mod constants;

/// Simple program to greet a person
#[derive(Parser)]
#[clap(group(ArgGroup::new("spec").required(true).args(&["ccsv", "bin"])))]
struct Args {
    /// Directory to dump files to
    #[clap(short, long, required=true)]
    dumpdir: String,

    /// Path to the custom-formatted CSV
    #[clap(short, long)]
    ccsv: Option<String>,

    /// Path to the custom-formatted binary file
    #[clap(short, long)]
    bin: Option<String>,

    /// Terminate upon reaching this time (in seconds), or at the end if not
    /// specified
    #[clap(short, long)]
    target_s: Option<u64>,

    /// If specified, dump png/ops files for every window
    /// of dump_s seconds for which there is data in the dataset.

    /// {time}.PNG files will be the state of the canvas after the
    /// last operation *before* that time. {time}.ops files will be
    /// the sequence of ops in the time range [time-1, time)
    #[clap(long)]
    dump_s: Option<u64>,

    /// When true (default), dump unexported png/ops files with
    /// filename 'final' upon program termination.
    #[clap(long)]
    dumplast: Option<bool>,

    /// When true (default false), dump operations
    #[clap(long)]
    dumpops: Option<bool>,

    /// When true (default), dump png files
    #[clap(long)]
    dumpims: Option<bool>,
}

fn main() {
    let args = Args::parse();

    let dumpdir = Path::new(&args.dumpdir);
    std::fs::create_dir_all(dumpdir).expect("Could not create dump directory");

    let dumplast = args.dumplast.unwrap_or(true);
    let dumpops = args.dumpops.unwrap_or(false);
    let dumpims = args.dumpims.unwrap_or(true);

    if !(dumpops || dumpims) {
        panic!("Told to dump neither ops nor images! Terrible idea");
    } else if args.target_s.is_none() && !dumplast {
        panic!("Not given target_s, but not told to dump last either. Sad!");
    }

    if !dumplast {
        print!("WARNING: Told not to dump final state, which is usually useful");
    }

    let mut op_iterator: Option<Box<dyn Iterator<Item = place_op::PlaceOp>>> = None;

    if args.bin.is_some() {
        op_iterator = Some(Box::new(
            binary_op_stream_from_file(Path::new(&args.bin.unwrap()))
        ));
    } else if args.ccsv.is_some() {
        panic!("Ok, unfortunately the ccsv arg is unimplemented for now");
    }

    match op_iterator {
        None => panic!("Somehow, we haven't made an iterator? fucking clap"),
        Some(i) => dump::Dump(i, dumpdir, args.target_s, args.dump_s, dumplast, dumpops, dumpims)
    };
}
