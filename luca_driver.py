#!/usr/bin/env python3

import os
import argparse
import csv
from shutil import copyfile
from sqlalchemy.exc import IntegrityError
from PIL import Image
import imagehash
import imghdr
import configparser
config = configparser.ConfigParser()
config.read("alembic.ini")
from protestDB.cursor import ProtestCursor
pc = ProtestCursor()

def main(**kwargs):
    is_violence = ['1.0', '1', 'yes']
    image_dir = kwargs['image_dir']
    """ The fields: rt_count and image_name has been switched
        in the csv file, hence the odd indexing in the following
    """
    if kwargs['remove_old']:
        for_all = False
        for img in pc.queryImages().filter_by(source="Luca Rossi - ECB"):
            img_dir = config['alembic']['image_dir']
            if not for_all:
                confirm = input("Delete %s [Y/n/All]: " % os.path.join(img_dir, img.name))
            if confirm.lower() == "all":
                for_all = True
            if confirm == 'Y' or confirm == '' or for_all :
                print("Deleting image: %s" % img)
                try:
                    os.remove(os.path.join(img_dir, img.name))
                except FileNotFoundError:
                    print("File not found, continue")
                pc.removeImage(img)
            else:
                print("Not removing image: %s" % img)
        return

    with open(kwargs['csv_file'], 'r') as f:
        csvfile = csv.DictReader(f, delimiter=";")
        c = 0
        for row in csvfile:
            c += 1
            label = None
            if row['Violence'] != "":
                label = float(row['Violence'].lower() in is_violence)

            image_name = row['rt_count']
            path_and_name = os.path.join(image_dir, image_name)

            if not os.path.exists(path_and_name):
                continue
            try:
                img = pc.insertImageLater(
                    path_and_name=path_and_name,
                    source = "Luca Rossi - ECB",
                    origin = "local",
                    label=label,
                    tags = ['twitter', 'luca rossi', 'ECB', 'Frankfurt'],
                )
                if img is None:
                    print("Not inserting: %s" % image_name)
                    continue

                if kwargs['destination_dir']:
                    hash_name = str(imagehash.dhash(Image.open(path_and_name)))
                    extension = imghdr.what(path_and_name)
                    copyfile(path_and_name, os.path.join(kwargs['destination_dir'], "%s.%s" % (hash_name, extension)))
                    img.name = "%s.%s" % (hash_name, extension)
                print("Inserted rows: %s" % c)
            except IntegrityError:
                print("Failed for %s" % image_name)
            except OSError:
                print("File not found for %s" % image_name)

        pc.try_commit()





if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Data insert from initial image data set from Luca Rossi"
    )
    parser.add_argument(
        "--image-dir",
        type=str,
        help="The directory containing images"
    )
    parser.add_argument(
        "--csv-file",
        type=str,
        help="The CSV file containing labels and other description of the images"
    )
    parser.add_argument(
        "--destination-dir",
        type=str,
        default="",
        help="If set, the images will be copied to this folder upon injection into the database"
    )
    parser.add_argument(
        "--remove-old",
        action="store_true",
        help="If True, will remove all currently held images from the Luca Rossi data set from the ECB protest",
    )

    main(**vars(parser.parse_args()))
