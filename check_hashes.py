#!/usr/bin/env python3

from os import listdir, path
from os.path import isfile, join
from PIL import Image
import argparse
import imagehash
import configparser

from protestDB.cursor import ProtestCursor

pc = ProtestCursor()
dhashes = {}
ahashes = {}
config = configparser.ConfigParser()
config.read("alembic.ini")


def main(**kwargs):
    d_clash_counter = 0
    a_clash_counter = 0
    image_dir = kwargs['image_dir'] or config['alembic']['image_dir']
    image_files = [ path.join(image_dir, f) for f in listdir(image_dir) if path.isfile(path.join(image_dir, f))]
    c = 0

    for filename in image_files:
        c += 1
        ahash = str(imagehash.average_hash(Image.open(filename)))
        dhash = str(imagehash.dhash(Image.open(filename)))
        img = pc.getImage(ahash)
        if dhash in dhashes:
            d_clash_counter += 1
            dhashes[dhash] += [filename]
            print("{:<8} {:<5} {:<5} {:<18} {:<18} {:<18}".format(c, a_clash_counter, d_clash_counter, filename, ahash, dhash))
        else:
            dhashes[dhash] = [filename]
        if ahash in ahashes:
            a_clash_counter += 1
            ahashes[ahash] += [filename]
            if not kwargs['no_ahash_output']:
                print("{:<8} {:<5} {:<5} {:<18} {:<18} {:<18}".format(c, a_clash_counter, d_clash_counter, filename, ahash, dhash))
        else:
            ahashes[ahash] = [filename]

    print("_" * 80)
    print("d_Clashes: %s\t a_classhes: %s" % (d_clash_counter, a_clash_counter))
    print("_" * 80)
    for k, v in dhashes.items():
        if len(v) == 1: continue
        print(k, ", ".join(v))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=""
    )
    parser.add_argument(
        "--image_dir",
        default=None,
    )
    parser.add_argument(
        "--no-ahash-output",
        action="store_true",
        help="If set, will not output clashes caused by using average image hashing",
    )

    args = parser.parse_args()

    main(**vars(args))

