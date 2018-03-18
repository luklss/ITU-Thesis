
"""
This script takes care of executingt he serp driver for the search parameters given in a csv file. 
The format is: "search_term, search_engine, n_images, label" per line and the header won't be included

"""

import argparse
import csv
from serp_scraper import keyword_scraper

def readParameters(filepath):
	result = []
	total_images_viol = 0
	total_images_peaceful = 0
	with open(filepath, 'r') as csvfile:
		f = csv.reader(csvfile, delimiter = ',')
		next(f, None)
		for row in f:
			search_term = row[0].strip()
			search_engine = row[1].strip()
			n_images = int(row[2].strip())
			label = float(row[3].strip())
			if (label == 1.0): 
				total_images_viol += n_images
			elif(label == 0.0):
				total_images_peaceful += n_images
			entry = (search_term, search_engine, n_images, label)
			result.append(entry)
		print("we have a total of %s violent images and %s non violent images" %(total_images_viol, total_images_peaceful))
		return result

def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n: 
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: 
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """
    
    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')
        
    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print ('please enter y or n.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False



def main(filepath):
	parameters = readParameters(filepath)
	for par in parameters:
		print (par)
	if (confirm("This is the input, should we proced?")):
		for par in parameters:
			scraper = keyword_scraper.Scraper([par[0]], "images", par[2],\
				10, 1, par[3], "local")
			scraper.scrape(par[1])
			scraper = None


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		prog='Search terms scraper',
	    description='This script takes care of executingt he serp driver for the search parameters given in a csv file.\
		The format is: "search_term, search_engine, n_images, label" per line and the header will not be be included',
	)
	parser.add_argument(
		'csv_path',
	    metavar='path',
	    help='Path to the csv file',
	)


	main(parser.parse_args().csv_path)


