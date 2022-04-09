use clap::{ArgGroup, Parser};

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

    /// If specified, dump png/ops files for every window
    /// of dump_s seconds for which there is data in the dataset.

    /// {time}.PNG files will be the state of the canvas after the
    /// last operation *before* that time. {time}.ops files will be
    /// the sequence of ops in the time range [time-1, time)
    #[clap(long)]
    target_s: Option<u64>,

    /// When true (default), dump unexported png/ops files with
    /// filename 'final' upon program termination.
    #[clap(long)]
    dumplast: Option<bool>,

    /// When true (default), dump operations
    #[clap(long)]
    dumpops: Option<bool>,

    /// When true (default), dump png files
    #[clap(long)]
    dumpims: Option<bool>,
}

fn main() {
    let args = Args::parse();
}
