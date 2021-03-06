use clap::{ArgGroup, Parser};
use binary_op_iterator::ops_from_binary_file;
use sortedcsv_op_iterator::ops_from_sorted_csv;
use std::iter::Iterator;
use std::path::Path;

mod binary_format;
mod constants;
mod dump;
mod binary_op_iterator;
mod place_op;
mod sortedcsv_op_iterator;

/// Simple program to greet a person
#[derive(Parser)]
#[clap(group(ArgGroup::new("spec").required(true).args(&["csv", "bin"])))]
struct Args {
    /// Directory to dump files to
    #[clap(short, long, required = true)]
    dumpdir: String,

    /// Path to the raw data CSV. It's not quite the raw data provided by
    /// reddit: it has to be sorted by timestamp, unfortunately
    #[clap(short, long)]
    csv: Option<String>,

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

    /// When true (default false), verify the binary encoding on every operation
    /// by checking that x = decode(encode(x))
    #[clap(long)]
    checkencoding: Option<bool>,
}

fn main() {
    let args = Args::parse();

    let dumpdir = Path::new(&args.dumpdir);
    std::fs::create_dir_all(dumpdir).expect("Could not create dump directory");

    let dumplast = args.dumplast.unwrap_or(true);
    let dumpops = args.dumpops.unwrap_or(false);
    let dumpims = args.dumpims.unwrap_or(true);
    let checkencoding = args.checkencoding.unwrap_or(false);

    if !(dumpops || dumpims) {
        panic!("Told to dump neither ops nor images! Terrible idea");
    } else if args.target_s.is_none() && !dumplast {
        panic!("Not given target_s, but not told to dump last either. Sad!");
    }

    if !dumplast {
        println!("WARNING: Told not to dump final state, which is usually useful");
    }
    if checkencoding {
        println!("WARNING: Encoding checks are enabled! This will slow things down a lot!");
    }

    let mut op_iterator: Option<Box<dyn Iterator<Item = place_op::PlaceOp>>> = None;

    if args.bin.is_some() {
        op_iterator = Some(Box::new(ops_from_binary_file(Path::new(
            &args.bin.unwrap(),
        ))));
    } else if args.csv.is_some() {
        // panic!("Ok, unfortunately the csv arg is unimplemented for now");
        op_iterator = Some(ops_from_sorted_csv(Path::new(
            &args.csv.unwrap(),
        )));
    }

    match op_iterator {
        None => panic!("Somehow, we haven't made an iterator? fucking clap"),
        Some(i) => dump::dump(
            i,
            dumpdir,
            args.target_s,
            args.dump_s,
            dumplast,
            dumpops,
            dumpims,
            checkencoding,
        ),
    };
}
