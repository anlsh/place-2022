use clap::{Command, Arg};

fn main() {
    let arg_dumpdir = Arg::new("dumpdir")
        .takes_value(true)
        .required(true)
        .long("dumpdir")
        .help("Directory to dump files to");
    let arg_ccsv = Arg::new("ccsv")
        .takes_value(true)
        .conflicts_with("bin")
        .required(true)
        .long("ccsv")
        .help("Path to the custom-formatted CSV");
    let arg_bin = Arg::new("bin")
        .takes_value(true)
        .conflicts_with("ccsv")
        .required(true)
        .long("bin")
        .help("Path to the custom-formatted binary file");
    let arg_target_s = Arg::new("target_s")
        .takes_value(true)
        .required(false)
        .long("target_s")
        .help(
            "If specified, dump png/ops files for every window
of dump_s seconds for which there is data in the dataset.

{time}.PNG files will be the state of the canvas after the
last operation *before* that time. {time}.ops files will be
the sequence of ops in the time range [time-1, time)",
        );
    let arg_dumplast = Arg::new("dumplast")
        .takes_value(true)
        .required(false)
        .long("dumplast")
        .help(
            "When true (default), dump unexported png/ops files with
filename 'final' upon program termination.",
        );
    let arg_dumpops = Arg::new("dumpops")
        .takes_value(true)
        .required(false)
        .long("dumpops")
        .help("When true (default) dump operations");
    let arg_dumpims = Arg::new("dumpims")
        .takes_value(true)
        .required(false)
        .long("dumpims")
        .help("When true (default), dump pngs");

    let matches = Command::new("Place 2022 Dataset Processor in Rust")
        .version("0.1")
        .author("Anish Moorthy <anlsh@protonmail.com>")
        .arg(arg_dumpdir)
        .arg(arg_ccsv)
        .arg(arg_bin)
        .arg(arg_target_s)
        .arg(arg_dumplast)
        .arg(arg_dumpops)
        .arg(arg_dumpims)
        .get_matches();
}
