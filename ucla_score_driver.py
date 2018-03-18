
import argparse
from protestDB import cursor
import pandas as pd
from analysis.lib import csv_scores as cs
import matplotlib.pyplot as plt
import os

PATH_TO_SAVE = "drivers_output/UCLA_database_scores.csv"

def get_name_hash_mapping(pc):
	imgs = pc.getImages()
	img_name_hash = {}
	for im in imgs:
		img_name_hash[im.name] = im.imageHASH
	return img_name_hash

def main(db, csv_out):
	pc = cursor.ProtestCursor()
	img_name_hash = get_name_hash_mapping(pc) # establish a mapping between names and hashes
	query = "select a.timestamp, b.name as image1, \
	c.name as image2, a.win1, a.win2, a.tie from Comparisons a\
	inner join Images b on a.imageID_1 = b.imageHASH\
	inner join Images c on a.imageID_2 = c.imageHASH\
	where b.source = 'UCLA' and c.source = 'UCLA'\
	order by a.timestamp desc"
	df = pd.read_sql(query, pc.session.bind)
	if not os.path.exists(csv_out):
		print("Generating scores...")
		cs.GenerateChoixScores(df, csv_out)
	scores = cs.MinMax(cs.ReadScoresFromCsv(csv_out), "violence")

	# check distribution
	print("close plot to continue")
	plt.hist(scores['violence'], 50, label = "UCLA", alpha=0.5, density = 1)
	plt.xlabel('violence')
	plt.ylabel('percent')
	plt.show()

	if (db):
		for index, row in scores.iterrows():
			im_hash = img_name_hash[row['fname']]
			violence = row['violence']
			label = pc.insertLabel(
	            im_hash,
	            violence,
	            source = "UCLA original",
	            do_commit=False,
        	)
			print("Inserting:\n\t%s" % label)
		pc.try_commit()




if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		prog = "UCLA score driver",
		description = "This program will calculate the image scores, plot them,\
		and possibly write them in the db"
	)
	parser.add_argument(
		'csv_output',
	    help='the path where the csv of scores will be outputed to, including the filename',
	    default = PATH_TO_SAVE
	)
	parser.add_argument(
		"--include_db",
		action = "store_true"
	)

	args = parser.parse_args()
	main(args.include_db, args.csv_output)


