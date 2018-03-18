#!/bin/bash
#
# Provided with an argument indicating the images directory, will pack
# all images that are not named with either 'test' or 'train' in their name
# e.g. avoid packing all image names from the UCLA data set. All other files in the image
# directory will be packed into an `images.zip` file.
#
# Usage:
#   `./pack_non_ucla.sh images/`
#
# Where `images/` in this case is the relative path to the folder of images. 

if [ -z $1 ]; then
    echo "Missing argument of path to image directory";
else
    find $1 -type f ! -regex '.*[test,train].*.jpg' | xargs zip images.zip
    unzip -l images.zip | tail -n 2
fi;
