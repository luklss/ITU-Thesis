
import annotator.annotator as annotator
import argparse
from protestDB.cursor import ProtestCursor
import argparse

def main(folder, include_db):
	pc = ProtestCursor()
	ann = annotator.Annotator(
		img_folder = "images", 
		dbcursor = pc,
		includetoDB = include_db,
	)



if __name__ == '__main__':

	parser = argparse.ArgumentParser(
		prog = "Annotator",
		description = "Binary annotator for protest vs non protest images"
	)

	parser.add_argument(
		"image_folder",
		metavar = "folder",
		help = "The path to the folder where the images sit"
	)

	parser.add_argument(
		'include_db',
		metavar='includedb',
		help='0 or 1 if to include the images on the database or not. 0 does not include, 1 includes',
		type=int,
		choices=[0,1],
	)

	args = parser.parse_args()


	main(args.image_folder, args.include_db)