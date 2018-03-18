#!/usr/bin/env python3

import os
import sys
import csv
from PIL import Image
import re
import psutil
import argparse
import configparser
import imagehash
config = configparser.ConfigParser()
config.read("alembic.ini")


from protestDB.cursor import ProtestCursor
import protestDB.models as models

def main(**kwargs):
    image_dir = config['alembic']['image_dir']

    pc = ProtestCursor()

    if kwargs['validate_logs']:
        r_hash   = re.compile("[0-9a-zA-Z]{16}")
        r_name   = re.compile("(test|train)-[0-9]+.jpg")
        log_file = kwargs['log_file']
        with open(log_file, "r") as f:
            print("{:<16} {:<16} {:<16} {:<16}".format("Name", "aHash", "pHash 1", "pHash 2"))
            for line in f:
                if not "IntegrityError" in line:
                    continue
                line   = line.strip()
                hash   = r_hash.search(line).group(0)
                name   = r_name.search(line).group(0)
                img    = pc.getImage(hash)
                tmpimg = Image.open(os.path.join(image_dir, name))
                print("{:<16} {:<16} {:<16} {:<16}".format(name, hash, str(imagehash.phash(img.get_image())), str(imagehash.phash(tmpimg))))
                try:
                    img.show()
                    tmpimg.show()
                except:
                    continue
                try:
                    if input("Continue?") == "":
                        kill_displays()
                        continue
                except:
                    kill_displays(True)
    elif kwargs['fix_primaries']:
        all_images = pc.session.query(models.Images).all()
        c          = 0
        for img in all_images:
            c += 1
            sys.stdout.write('\r')
            #print("%s %s %s" % (c, img, len(img.tags)))
            # the exact output you're looking for:
            step = c/len(all_images)
            sys.stdout.write("[%-50s] %d%%" % ('='*int(step*50), step*100))
            sys.stdout.flush()
            try:
                o     = img.get_image()
                dhash = str(imagehash.dhash(o))
                ahash = str(imagehash.average_hash(o))
            except FileNotFoundError:
                print("FILE NOT FOUND %s" % img)
                #pc.removeImage(img)
                continue

            for ti in pc.query(models.TaggedImages).filter_by(imageID=ahash):
                tag = pc.get(models.Tags, tagID=ti.tagID)
                img.tags.append(tag)

            for l in pc.query(models.Labels).filter_by(imageID=ahash):
                l.imageID = dhash

            if pc.instance_exists(models.Images, imageHASH=dhash):
                sys.stdout.write('\r')
                #print("ALREADY EXISTS: %s" % img)
                continue


            img.imageHASH = dhash
        pc.try_commit()
    else:
        ucla_dir = kwargs['ucla_dir']
        if not os.path.exists(ucla_dir):
            raise ValueError(
                "Cannot find UCLA image folder '%s' in image directory '%s'" % (
                    ucla_dir,
                    image_dir,
                )
            )
        if not kwargs['no_test']:
            extract_rows("test", ucla_dir, pc)
        if not kwargs['no_train']:
            extract_rows("train", ucla_dir, pc)

def kill_displays(also_exit=False):
    for proc in psutil.process_iter():
        if proc.name() == "display":
            proc.kill()
    if also_exit:
        sys.exit()

def extract_rows(name, full_path, pc):
    """ name should be either `train` or `test` since
        these are the only two prepended names for UCLA filenames
    """
    filename = "annot_%s.txt" % name
    with open(os.path.join(full_path, filename)) as f:
        csvreader = csv.reader(f, delimiter='\t')
        header = csvreader.__next__()
        c = 0
        for row in csvreader:
            parsed_row = parse_row(row, header)
            try:
                img = pc.insertImageLater(
                    path_and_name = os.path.join(full_path, "img/%s" % name, parsed_row['fname']),
                    source        = "UCLA",
                    origin        = "local",
                    label         = parsed_row['violence'],
                    tags          = ["UCLA-%s" % name] + list(filter(
                        lambda x: not x is None,
                        [ k if v == 1 else None
                          for k, v in parsed_row.items()
                        ]
                    ))
                )
                if not img is None:
                    c += 1
                    print("_" * 80)
                    print("Inserting %s %45s" % (parsed_row['fname'], c))
                    img.name = parsed_row['fname']
                else:
                    print("_" * 80)
                    print("Nothing for %s " % parsed_row['fname'])
            except Exception as e:
                print("_" * 80)
                print("ERROR")
                print(e)
                continue
        pc.try_commit()


def parse_row(row, header):
    parsed = {}
    for k, v in enumerate(header):
        try:
            parsed[v] = float(row[k])
        except:
            parsed[v] = row[k] if row[k] != "-" else None
    return parsed



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Include the protest images collected by UCLA into sqlite db"
    )

    parser.add_argument(
        "--ucla-dir",
        default = "UCLA-protest",
        type    = str,
        help    = "The name of the UCLA image directory (default: 'UCLA-protest')"
    )
    parser.add_argument(
        "--no-test",
        action = "store_true",
        help   = "If set, will not include the UCLA test set"
    )
    parser.add_argument(
        "--no-train",
        action = "store_true",
        help   = "If set, will not include UCLA train set"
    )
    parser.add_argument(
        "--validate-logs",
        action = "store_true",
        help   = "If set, will go through an error log and open the images that failed due to integrity error"
    )
    parser.add_argument(
        "--log-file",
        type = str,
        help = "Expected if `validate-logs` is set"
    )
    parser.add_argument(
        "--fix-primaries",
        action = "store_true",
        help   = "If set, will set primary keys of all existing images to the dhash value of the image."
    )

    args = parser.parse_args()
    main(**vars(args))
