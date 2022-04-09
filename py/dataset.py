import argparse
import csv
import gzip
from datetime import datetime
import re
from tqdm import tqdm

parser = argparse.ArgumentParser(description='Dataset cleaner for /r/place 2022')

# As described in
# https://old.reddit.com/r/place/comments/txvk2d/rplace_datasets_april_fools_2022/
parser.add_argument('rawdata_file', help='Path to gz file containing the raw dataset')
parser.add_argument('out_file', help='Idk you export the data here or something')

args = parser.parse_args()

def gz_lines(fname):
    with gzip.open(fname) as f:
        f.readline()
        for line in f:
            yield line.decode('utf-8')

def file_lines(fname):
    with open(fname) as f:
        f.readline()
        for line in f:
            yield line

if __name__ == "__main__":

    lines_fn = None
    if args.rawdata_file[-3:] == ".gz":
        lines_iter = gz_lines(args.rawdata_file)
    else:
        lines_iter = file_lines(args.rawdata_file)

    # Ignore user hashes, they are very big
    line_pattern = re.compile('(.*) UTC,.*==,#(.*),"(.*)"')
    n_lines = 0

    for line in tqdm(lines_iter):
        match = line_pattern.match(line).groups()
        tstr, color, coords = match
        if "." not in tstr:
            tstr = tstr + ".000"
        tobj = datetime.strptime(str(tstr + "000"), "%Y-%m-%d %H:%M:%S.%f")
        unix_ts = int(tobj.timestamp()*1000)
        n_lines += 1

    print(n_lines)
