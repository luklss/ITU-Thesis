

"""This is script is used to insert scores from UCLA into the db based on the csv file they've sent us """

import argparse
import csv
from protestDB import cursor
from protestDB import models

PATH_TO_FILE = "misc/pairwise_annot.csv"

def main(csv_path, add_to_db):

	pc = cursor.ProtestCursor()
	imgs = pc.getImages()
	img_name_hash = {}
	images_not_found = set()

	# store a mapping between name and hash

	for im in imgs:
		img_name_hash[im.name] = im.imageHASH


	with open(csv_path, 'r') as f:
		reader = csv.reader(f, delimiter = ',', quotechar = '"')
		header = {}
		header_input = next(reader)
		log = open("logs/comparisons_images_not_found.txt", "w")
		for k, v in enumerate(header_input):
			header[v] = k
		
		for indx, row in enumerate(reader):
			img1_name = row[header["image1"]]
			img2_name = row[header["image2"]]
			win1 = row[header["win1"]]
			win2 = row[header["win2"]]
			tie = row[header["tie"]]


			if img1_name not in img_name_hash:
				print(img1_name, " could not be retrieved")
				images_not_found.update([img1_name])	
				continue
			else:
				img1_hash = img_name_hash[img1_name]


			if img2_name not in img_name_hash:
				print(img2_name, " could not be retrieved")
				images_not_found.update([img2_name])	
				continue
			else:
				img2_hash = img_name_hash[img2_name]


			print ("inserting pair number ", indx, ": ", img1_name, img2_name, win1, win2, tie)
			pc.insertComparison(
			imageID_1 = img1_hash,
            imageID_2 = img2_hash,
            win1      = win1,
            win2      = win2,
            tie       = tie,
            source    = "UCLA_original",
            do_commit = False
        )
		
		if add_to_db:
			pc.try_commit()

	for img in images_not_found:
		log.write(img)
		log.write("\n")

	log.close()




if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		prog='Annomaly detection script',
	    description='This is script is used to insert scores from UCLA into the db based on the csv file\
	    sent by them'
	)
	parser.add_argument(
		'--csv_path',
	    metavar='path',
	    help='Path to the csv file',
	    default = PATH_TO_FILE
	)
	parser.add_argument(
		'--db',
	    help='flag, if true it will ad to db',
	    action="store_true"
	)
	args = parser.parse_args()
	main(args.csv_path, args.db)