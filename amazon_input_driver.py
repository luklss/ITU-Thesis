#!/usr/bin/env python3
#
# Usage either through:
#   ```
#       ./amazon_input_driver.py --files <file with filenames>
#   ```
#   or:
#   ```
#      cat file_with_filenames.txt | ./amazon_input_driver.py
#   ```

import sys
import os
import random
import argparse
import csv
import imagehash
from PIL import Image

from protestDB.cursor import ProtestCursor
pc = ProtestCursor()

url = "https://s3.eu-central-1.amazonaws.com/ecb-protest/"

def checkValid(pairs, value1, value2, threshold):
    if (len(pairs[value1]) >= threshold or len(pairs[value2]) >= threshold):
        return False
    if (value1 in pairs[value2] or value2 in pairs[value1]):
        return False

    return True

def create_random_pairs(files, n_pairs):
    """
        Returns a dictionary where each key is a file
        the value is a list of other files to pair with
        so that each file is paired with n_pairs other
        files.
        Pairs are created randomly between all files in
        `files`.
    """
    pool = files * n_pairs
    random.shuffle(pool)

    pairs = {}
    print("_" * 80)
    print("Starting")

    # Initialize pairs
    for i in files:
        pairs[i] = []

    for i in files:
        while len(pairs[i]) < n_pairs:
            j = pool.pop()
            if j == i:
                pool = [j] + pool
                continue

            if checkValid(pairs, i, j, n_pairs):
                pairs[i].append(j)
                pairs[j].append(i)
            else:
                pool = [j] + pool
                continue

    return pairs

def create_from(A, B, n_pairs):
    """
    Creates pairs such that for all
    pairs (a, b) a is in A and b is in B

    Requires that A and B are of equal lengths
    """
    assert len(A) == len(B), "A and B must be of equal lenghts"

    pairs = {}
    # initialize pairs:
    for i in A + B:
        pairs[i] = []
    A = A * n_pairs
    B = B * n_pairs
    random.shuffle(A)
    random.shuffle(B)

    for a in A:
        while len(pairs[a]) < n_pairs:
            b = B.pop()

            assert a != b, "Found a violation {} and {} are equal".format(a, b)

            if checkValid(pairs, a, b, n_pairs):
                # create the pair:
                pairs[a].append(b)
                pairs[b].append(a)
            else:
                # Put back b into B:
                B = [b] + B

    return pairs


def main(files=None, A=None, B=None, **kwargs):
    """ A and B is not command line supported, import this driver
        as a module, and call its main function directly to use
        this feature.
    """

    if files is None and A is None and B is None:
        raise ValueError("Either provide a list of files "
                         "or otherwise two pools A and B "
                         "of files"
        )

    n_pairs = kwargs['k_pairs']

    if files is None:
        pairs = create_from(A, B, n_pairs)
    else:
        pairs = create_random_pairs(files, n_pairs)


    header = []
    for i in range(10):
        for j in range(1, 3):
            header.append("image_%s-%s" % (i, j))
    rows = []
    rows.append(header)

    build_url = lambda name: url + name

    pairwise = set()
    for k, v in pairs.items():
        for j in v:
            pair = sorted([k, j])
            pairwise.update([":".join(pair)])

    pairwise = list(pairwise)

    random.shuffle(pairwise)
    row = []
    for pair in pairwise:
        pair = pair.split(":")
        img_a = pair[0]
        img_b = pair[1]
        row.append(build_url(img_a))
        row.append(build_url(img_b))
        if len(row) == 20:
            rows.append(row)
            row = []

    with open(kwargs['output_csv'], "w") as f:
        csvwriter = csv.writer(f, delimiter=",")
        csvwriter.writerows(rows)


    if kwargs['debug']:
        for k, v in pairs.items():
            print("%35s: %-15s" % (k, len(v)))
    print("\nAll done!")
    print("Number of rows: %s" % len(rows))
    print("_" * 80)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Builds an input csvfile compatible with amazon MTurk"
    )

    parser.add_argument(
        "--files",
        type=str,
        help="A name of a file with image names separated by newline"
    )
    parser.add_argument(
        "--images-dir",
        default="images/",
        type=str,
        help="The path to the directory of the images (default: 'images/'"
    )
    parser.add_argument(
        "--output-csv",
        default="mturk-input.csv",
        type=str,
        help="The name of the output csv file (default: 'mturk-input.csv'"
    )
    parser.add_argument(
        "-k",
        "--k-pairs",
        default=10,
        type=int,
        help="The number of pairs to generate for each observation"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Increase verbosity for debugging"
    )

    args = vars(parser.parse_args())

    if args['files'] is None:

        files = []
        for line in sys.stdin:
            if len(line.split(".")) == 1:
                hash_name = line.strip()
            else:
                hash_name = str(
                    imagehash.dhash(
                        Image.open(
                            os.path.join(args['images_dir'], line.strip())
                        )
                    )
                )
            print("hash_name: %s" % hash_name)
            try:
                fname = pc.getImage(hash_name).name
                files.append(fname)
            except AttributeError:
                print("Skipping %s with hash: %s" % (line.strip(),hash_name))

        args["files"] = files

    else:

        files = []
        with open(args["files"], "r") as f:
            for line in f:
                fname = pc.getImage(line.strip()).name
                files.append(fname)
        args["files"] = files



    main(**args)
