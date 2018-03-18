#!/usr/bin/env python3
"""
" This file depends on the `amazon_input_driver
"
" It is not made for a general case, but instead for the
" specific caase of drawing N samples from the UCLA dataset
" and similarly N samples from the Luca Rossi dataset.
"
" Resulting in a combined sample set of 2*N records
" It then calls the amazon_input_sample_driver in order to
" create the pairwise comparisons so that each pair of images:
"   (a, b), a in Luca and b in UCLA
" and that the matchups are randomly put together, from the
" randomly drawn images
"
"""
import os
import random
import argparse
import pandas as pd
from shutil import copyfile
from sqlalchemy import not_

from protestDB import cursor, models
import amazon_input_driver

pc = cursor.ProtestCursor()

def main(**kwargs):
    # Default arguments for amazon_input_driver:
    default_args = {
     "output_csv":  "mturk-input.csv",
     "images_dir":  "images/",
     "k_pairs"   :  10,
     "debug"     :  False
    }
    # set default params if missing:
    for k, v in default_args.items():
        if kwargs[k] is None:
            kwargs[k] = v

    print("_" * 80)
    print("Creating {} pairwise comparisons from {} samples".format(
                kwargs["k_pairs"],
                kwargs['n_samples'],
           ),
          "from Luca Rossi dataset and from the UCLA dataset"
    )

    # We will only consider UCLA images that has the `is protest` tag:
    protest_hashes = [ i.imageHASH for i in pc.getTag("protest").images ]

    ucla_q = pc.query(models.Images.imageHASH).filter(
        models.Images.imageHASH.in_(
            protest_hashes
        )
    ).filter_by(
        source="UCLA"
    )

    ucla_image_ids = pd.read_sql(ucla_q.statement, pc.session.bind).rename(
        columns={
            "imageHASH": "imageid"
        }
    )


    # We will only consider the 1000 images that were used in first
    # MTurk sample:

    # returns distinct from Comparisons table by `column`:
    def onlyLucaSource(column):
        return pc.query(
            getattr(models.Comparisons, column)
        ).filter(
            models.Comparisons.source == "Luca Rossi - ECB, 1000"
        ).distinct()



    q1 = onlyLucaSource("imageID_1")

    q2 = onlyLucaSource("imageID_2").filter(
        not_(models.Comparisons.imageID_2.in_(q1)) # avoid duplicates
    )

    luca_image_ids = pd.concat([
        pd.read_sql(q1.statement, pc.session.bind).rename(columns={"imageID_1":"imageid"}),
        pd.read_sql(q2.statement, pc.session.bind).rename(columns={"imageID_2":"imageid"})
    ])

    assert len(luca_image_ids) == 1000, "Expected 1000 image hashes got: {}".format(
        len(luca_image_ids)
    )

    sample_A, sample_B = (ucla_image_ids.sample(n=kwargs['n_samples']),
                          luca_image_ids.sample(n=kwargs['n_samples']))
    sample_A, sample_B = list(sample_A.imageid), list(sample_B.imageid)

    print("Writing total of {} samples to {}".format(
        len(sample_A) + len(sample_B),
        kwargs["dump_sample"])
    )
    with open(kwargs['dump_sample'], "w") as f:
        for line in sample_A:
            f.write(line)
            f.write("\n")
        for line in sample_B:
            f.write(line)
            f.write("\n")

    # Translate image ids to image names:
    sample_A = [ pc.getImage(h).name for h in sample_A ]
    sample_B = [ pc.getImage(h).name for h in sample_B ]

    # if copy is set, will copy all images to the given directory:
    if not kwargs['copy_to_dir'] is None:
        for img in sample_A + sample_B:
            copyfile("images/" + img, os.path.join(kwargs['copy_to_dir'], img))

    amazon_input_driver.main(
        A=sample_A,
        B=sample_B,
        **kwargs
    )


################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This is a special case of the amazon_input_driver. "
                    "All arguments are as specified in `amazon_input_driver "
                    "therefore, refer to the mothership for the real "
                    "definitions! The only orignal argument is the sample "
                    "filename. This is to store the the two sets of images "
                    "from Luca and UCLA. So, if nothing else is specified, "
                    "this file and the `mturk-input.csv` file are the "
                    "important ones."
    )

    parser.add_argument(
        "--copy-to-dir",
        type=str,
        help="If set, will copy the sample images to this directory"
    )

    parser.add_argument(
        "-n",
        "--n-samples",
        type=int,
        default=100,
        help="The number of samples to draw from each dataset"
    )
    parser.add_argument(
        "--dump-sample",
        default="sample-luca-ucla.txt",
        help="The output file of the randomly drawn samples from Luca and UCLA datasets"
    )
    parser.add_argument(
        "--output-csv",
        help="See `amazon_input_driver.py --help`"
    )
    parser.add_argument(
        "--images-dir",
        help="See `amazon_input_driver.py --help`"
    )
    parser.add_argument(
        "--k-pairs",
        help="See `amazon_input_driver.py --help`"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="See `amazon_input_driver.py --help`"
    )

    args = vars(parser.parse_args())

    main(**args)
