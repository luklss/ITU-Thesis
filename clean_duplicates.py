"""
See this issue: https://trello.com/c/PuMhnTSq/102-duplicate-images

There were 2289 duplicate images caused by an udate to the imagehash
library within the last 3 months, which changed the hash ever so slighty
for some images. This in effect, caused these duplicates.

Therefore, this script will seek to go through the list of duplicates,
and for every image, compute the hash according to the new version of
`imagehash`. Then keep the database entry that corresponds with the
new hash.
"""

import os
import sys
import imagehash
from PIL import Image
import pandas as pd
from protestDB import cursor
pc = cursor.ProtestCursor()

all_duplicates = "select * from Images where Images.name in (select name from (select imageHASH, name, count(name) as count from Images group by name order by count desc) as a where a.count == 2);"

imagepath = "images/"

def imghash(name, imgpath=imagepath):
    return str(imagehash.dhash(Image.open(os.path.join(imgpath, name))))

def print_status(len_imgs, len_labels):
    print("# of images: %s" % len_imgs)
    print("# of labels: %s" % len_labels)

def get_stats():
    return len(pc.getImages()), len(pc.queryLabels().all())

def main():
    num_images, num_labels = get_stats()
    print_status(num_images, num_labels)

    df = pd.read_sql(all_duplicates, pc.session.bind)
    df = df.sort_values(by='name')
    iterable = df.iterrows()
    for index, a in iterable:
        # Since the duplicates resides pairwise
        # we can get both:
        _, b = next(iterable)
        assert a['name'] == b['name'], "Ooops, pair is not duplicate!"

        h = imghash(a['name'])
        if h == a['imageHASH']:
            #print("Keeping A!")
            print("_", end="")
            pc.removeImage(b['imageHASH'], do_commit=False)
        elif h == b['imageHASH']:
            #print("Keeping B!")
            print("_", end="")
            pc.removeImage(a['imageHASH'], do_commit=False)
        else:
            raise Exception("Not equal to either!")
        sys.stdout.flush()

    pc.try_commit()

    num_images_after, num_labels_after = get_stats()
    print_status(num_images_after, num_labels_after)

    print("_" * 80)
    print("Deleted images: %s" % (num_images - num_images_after))
    print("Deleted labels: %s" % (num_labels - num_labels_after))

if __name__ == "__main__":
    main()
