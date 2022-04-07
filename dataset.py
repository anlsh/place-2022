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

if __name__ == "__main__":
    with gzip.open(args.rawdata_file) as f:

        # We just totally ignore the userhashes for now, they are too big
        line_pattern = re.compile('(.*) UTC,.*==,#(.*),"(.*)"')

        # Garbage formal line
        f.readline()

        n_lines = 0
        # Parsing the actual data
        for line in tqdm(f):
            line = line.decode('utf-8')
            match = line_pattern.match(line).groups()
            tstr, color, coords = match
            if "." not in tstr:
                tstr = tstr + ".000"
            tobj = datetime.strptime(str(tstr + "000"), "%Y-%m-%d %H:%M:%S.%f")
            unix_ts = int(tobj.timestamp()*1000)
            n_lines += 1

        print(n_lines)
