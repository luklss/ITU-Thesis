#!/usr/bin/env python3
"""
" This script computes the scores from the
" pairwise comparisons.
"
" The input is the Batch csv output from MTurk
" if output file is provided, the output will be of the format:
"   ```
"   #row, image1, image2, win1, win2, tie
"   ```
" In any case, unless `--dry-run` or `--no-db` is set,
" the computed scores and the parsed pairwise comparisons
" will be inserted into the database.
"
" Where win1 indicates the total number that image1
" was selected as the most violent in the comparisons
" between the two images - similarly for `win2` but with
" opporsite meaning.
" The tie indicates the total amount of users that answered the
" violence depicted was similar for the two images.
"
" Remember that each image pair is labelled by ten
" different individuals.
"
" **Usage:**
"
" ```
"   ./score_driver --input <batch_output_csv>
" ```
"
"
" **The header row includes the following named columns:**
"
" AcceptTime
" Answer.choice0
" Answer.choice1
" Answer.choice2
" Answer.choice3
" Answer.choice4
" Answer.choice5
" Answer.choice6
" Answer.choice7
" Answer.choice8
" Answer.choice9
" ApprovalTime
" Approve
" AssignmentDurationInSeconds
" AssignmentId
" AssignmentStatus
" AutoApprovalDelayInSeconds
" AutoApprovalTime
" CreationTime
" Description
" Expiration
" HITId
" HITTypeId
" Input.image_0-1
" Input.image_0-2
" Input.image_1-1
" Input.image_1-2
" Input.image_2-1
" Input.image_2-2
" Input.image_3-1
" Input.image_3-2
" Input.image_4-1
" Input.image_4-2
" Input.image_5-1
" Input.image_5-2
" Input.image_6-1
" Input.image_6-2
" Input.image_7-1
" Input.image_7-2
" Input.image_8-1
" Input.image_8-2
" Input.image_9-1
" Input.image_9-2
" Keywords
" Last30DaysApprovalRate
" Last7DaysApprovalRate
" LifetimeApprovalRate
" LifetimeInSeconds
" MaxAssignments
" NumberOfSimilarHITs
" Reject
" RejectionTime
" RequesterAnnotation
" RequesterFeedback
" Reward
" SubmitTime
" Title
" WorkTimeInSeconds
" WorkerId
"""

import csv
import argparse
import choix
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from protestDB import cursor, models
pc = cursor.ProtestCursor()

base = "https://s3.eu-central-1.amazonaws.com/ecb-protest/"
def get_name(url, _base=None):
    return url.replace(_base or base, '')

def get_hash(url, _base=None):
    return get_name(url, _base=_base).split('.')[0]

def as_dsv(row):
    cols = "{:<8} {:<25} {:<25} {:5} {:5} {:5}"
    return cols.format(*row)

class image:
    """ Just a placeholder class
        that can hold a name and an index
        and is hashable, comparable etc
    """
    def __init__(self, name, index):
        self.name  = name
        self.index = index

    def __hash__(self):
        return self.name.__hash__()

    def __eq__(self, other):
        if type(other) == str:
            return other == self.name
        return other.name == self.name


def main(input_file, **kwargs):
    """
    The `main` def for the driver file.
    """

    # The keys will be unique per image pair comparison,
    # the values will be a list of 3 entries with the format:
    # [win1, win2, tie]
    pair_dict = {}
    header = {}
    data = []
    UCLA_header      = ["row", "image1", "image2", "win1", "win2", "tie"]
    ucla_header_dict = { v: k for k, v in enumerate(UCLA_header) }
    tuples           = []    # a list of tuples used for choix score computation
    n_items          = set() # used to count number of unique items
    unique_images    = []    # in-order placement of image names matching the choix output

    def rowToDict(row, header=None):
        header   = header or ucla_header_dict
        row_dict = {}
        for k, v in header.items():
            row_dict[k] = row[v]
        return row_dict



    with open(input_file, 'r') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')

        # Parse the header row in to a dict
        # so that each key is a column name, and the value
        # is the row index
        header = { v: k for k, v in enumerate(next(reader)) }

        # The image column names follows the same (weird) structure
        # so we can just generate the names of all of them:
        img_cols = [
            "Input.image_%s-%s" % (j, i) for j in range(10) for i in range(1, 3)
        ]

        for row in reader:
            # Get the values from the image columns,
            # and parse get the image names from the url:
            images = list(map(
                lambda x: get_name(row[header.get(x)]),
                img_cols
            ))

            # get: Answer.choice[0-9]
            # for every image pair
            for pair in range(0, len(img_cols), 2):

                answer = row[header.get("Answer.choice%s" % int(pair/2))]
                vote = [ 1 if i-1 == int(answer) else 0 for i in range(3) ]

                # The image pair sits adjacent in the row of HITs:
                img_a, img_b = images[pair:pair+2]

                # Count the items:
                if not img_a in n_items:
                    #n_items[img_a] = "ost"
                    n_items.update([
                        image(name=img_a, index=len(unique_images))
                    ])
                    unique_images.append(img_a)
                if not img_b in n_items:
                    n_items.update([
                        image(name=img_b, index=len(unique_images))
                    ])
                    unique_images.append(img_b)

                # Compute key, uniquely for this pair of images:
                pair_key = ";".join(sorted([img_a, img_b]))

                # Sum up current score:
                pair_dict[pair_key] = [ x + vote[i] for i, x in enumerate(
                    pair_dict.get(pair_key, [0, 0, 0]))
                ]


        if kwargs['dry_run']:
            print(as_dsv(UCLA_header))


        c = 0
        indices = { i.name: i.index for i in n_items }

        #Check indices:
        for i in n_items:
            assert i.name == unique_images[i.index], "Enough of your mumbo jumbo!"

        assert len(indices.items()) == len(n_items), "You fucked it up, cowboy!"

        for k, v in pair_dict.items():
            c += 1
            row = [
                c,               # Row number
                k.split(";")[0], # image 1
                k.split(";")[1], # image 2
                v[0],            # win1
                v[2],            # win2
                v[1],            # tie
            ]
            data.append(row)
            row_dict = rowToDict(row, ucla_header_dict)

            # Add to list of tuples:
            img_a   = row_dict.get("image1")
            img_b   = row_dict.get("image2")
            index_a = indices[img_a]
            index_b = indices[img_b]


            ### Insert number of wins and ties for the pair:
            for win1 in range(row_dict.get("win1")):
                tuples.append((index_a, index_b))
                tuples.append((index_a, index_b))

            for win2 in range(row_dict.get("win2")):
                tuples.append((index_b, index_a))
                tuples.append((index_b, index_a))

            for tie in range(row_dict.get("tie")):
                tuples.append((index_a, index_b))
                tuples.append((index_b, index_a))


            if kwargs['dry_run']:
                print(as_dsv(row))


            if not kwargs['no_db'] and not kwargs['dry_run']:

                comparison = pc.insertComparison(
                    imageID_1   = get_hash(row_dict.get("image1"), ""),
                    imageID_2   = get_hash(row_dict.get("image2"), ""),
                    win1        = row_dict.get("win1"),
                    win2        = row_dict.get("win2"),
                    tie         = row_dict.get("tie"),
                    source      = "Luca Rossi - ECB, 1000",
                    do_commit   = False,
                )
                print("Inserting:\n\t%s" % comparison)

    # commit comparisons:
    if not kwargs['no_db'] and not kwargs['dry_run']:
        pc.try_commit()


    if kwargs["output_file"] and not kwargs['dry_run']:
        with open(kwargs['output_file'], "w") as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(UCLA_header)
            writer.writerows(data)

    print("_" * 80)
    print("n_items: %s" % len(n_items))
    print("Computing choix pairwise scores...")
    scores          = choix.opt_pairwise(len(n_items), tuples)
    v               = np.matrix(scores)
    scaler          = MinMaxScaler()
    scaled          = scaler.fit_transform(v.T)

    print(scaled)

    # Pair image names with the violence score for the image:
    for t in [(unique_images[i], scaled[i][0]) for i in range(len(n_items)) ]:
        img_hash = get_hash(t[0], '')
        violence = t[1]

        exists = pc.instance_exists(models.Images, imageHASH=img_hash)
        if not exists:
            raise ValueError("Image with hash: %s, does not exists!" % img_hash)

        label = pc.insertLabel(
            img_hash,
            violence,
            source = "Luca Rossi - ECB, 1000",
            do_commit=False,
        )
        if kwargs['dry_run'] or kwargs['no_db'] or not kwargs['insert_labels']:
            print("Would insert:\n\t%s" % label)
        else:
            print("Inserting:\n\t%s" % label)

    if kwargs['dry_run'] or kwargs['no_db']:
        pc.session.rollback()
    elif kwargs['insert_labels']:
        pc.try_commit()
    else:
        print("\nWill not commit insertion of labels, use '--insert-labels' to commit labels to db")
        pc.session.rollback()

    print("_" * 80)



################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description= "A script to clean and compute the scores from the MTurk "
                     "batch output file. The scores will be inserted into the "
                     "`comparisons` table in the `protestDB`.                 "
    )
    parser.add_argument(
        "-i",
        "--input-file",
        metavar = "file",
        type    = str,
        help    = "The MTurk batch file with HIT results."
    )
    parser.add_argument(
        "-o",
        "--output-file",
        metavar = "file",
        type    = str,
        help    = " The filename to send the output to. In general this is not       "
                  " needed as the outcome typically is to insert the                 "
                  " equivalent rows into the database, however, if set, a            "
                  " csvfile in the same format as the UCLA file                      "
                  " `pairwise_annot.csv` will be written to.                         "
                  " The output is equivalent to what is inserted into the comparison "
                  " table.                                                           "
    )
    parser.add_argument(
        "--no-db",
        action = "store_true",
        help   = " If set, will not insert anything into the db. If no output file "
                 " is provided, then is equivalent to setting --dry-run.           "
    )
    parser.add_argument(
        "--dry-run",
        action  = "store_true",
        help    =  " If set, will not do anything, but will output the potential "
                   " content of a file to stdout.                                "
    )
    parser.add_argument(
        "--insert-labels",
        action  = "store_true",
        help    = " If set, will also insert the computed labels into the database."
    )

    main(
        **vars(parser.parse_args())
    )
