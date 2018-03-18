


"""
This script is designed to select a sample to be annotated on mechanical turk. It works by, first pulling all the images that were
annotated as being protest related (ProtestNonProtestVotes.is_protest == 1). Then it iterates through every image and computing the hamming
distance to every other image available. If the distance is lower then the threshold set, it removes one of the images from the dataset.
It then shuffle the result, prints the original hashes of those images (as in the db) and saves them locally in a folder that can be specifided.
"""


from protestDB import cursor
from protestDB import models
from imagehash import dhash
import argparse
import os
from PIL import Image
from collections import defaultdict
import random
import shutil



SIMILARITY_THRESHOLD = 38 #percent

def hamming(s1, s2):
    """Calculate the Hamming distance between two bit strings"""
    assert len(s1) == len(s2)
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def cleanOrCreateFolder(path):
	""" removes a folder and all its contents, and then creates it again"""
	shutil.rmtree(path)
	os.makedirs(path)

def removeSimilarImages(image_list, folder_source):
	"""
	This function will remove images from a list based if there is a similiarty with another image in the list
	above a certain threshold.
	:param image_list: a list of image objects
	:param folder_source: the folder where the images are sitting
	"""
	#print ("processing hashes")
	original_images = {}
	original_hashes = []
	for idx, image in enumerate(image_list): # creates a list of hasehs and a mapping between hashes and image objects
		#print("processing image hash ", image.name, " index ", idx, " out of ", len(image_list))
		path = os.path.join(folder_source, image.name)
		hashh = str(dhash(Image.open(path))) # this could be skipped given we already have the d-hash. But it makes it easy to change as well.
		original_hashes.append(hashh)
		original_images[hashh] = image

	result_hashes = list(original_hashes) # creates a copy of the hashes so we do not remove hasehes on the original list while iterating through it
	#print("processing comparisons")
	for idx, hash1 in enumerate(original_hashes):
		#print("processing hash similiarity to ", hash1, " index ", idx, " out of ", len(original_hashes))
		for jdx in range(idx + 1, len(original_hashes)): # iterate through every other remaining image
			hash2 = original_hashes[jdx]
			dist = hamming(hash1, hash2)
			similarity = (len(hash1) - dist) * 100 / len(hash1)
			#print(similarity)
			if (similarity > SIMILARITY_THRESHOLD):
				try:
					result_hashes.remove(hash2)
				except Exception as e:
					pass
	result = []
	for hashh in result_hashes: # populates the result based on the original mapping
		result.append(original_images[hashh])

	return result


def main(folder_source, folder_dest, seed):
	random.seed(seed) # set the seed 
	pc = cursor.ProtestCursor()
	images = pc.query(models.Images).join(models.ProtestNonProtestVotes,models.ProtestNonProtestVotes.imageID ==
	models.Images.imageHASH).filter(models.ProtestNonProtestVotes.is_protest == 1) # gets protest images

	img_list = []
	for image in images: # get a list of image objects rather than a query object
		img_list.append(image)

	temp_list = removeSimilarImages(img_list, folder_source)

	random.shuffle(temp_list)
	#print("result size is ", len(temp_list))

	cleanOrCreateFolder(folder_dest)

	for img in temp_list[0:1000]: # output the hashes and save images
		path = os.path.join(folder_dest, img.name) #save sample
		img.get_image().save(path)
		print(img.imageHASH)




if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description=""
	)
	parser.add_argument(
		"dir_source",
		type = str,
	)
	parser.add_argument(
		"--dir_dest",
		type = str,
		default = "sample"
	)
	parser.add_argument(
		"--seed",
		type = int,
		default = 3000
	)
	args = parser.parse_args()
	main(args.dir_source, args.dir_dest, args.seed)