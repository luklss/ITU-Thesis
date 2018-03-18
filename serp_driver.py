	
from serp_scraper import keyword_scraper
import argparse

def main():

	parser = argparse.ArgumentParser(
		prog='Keyword scraper',
	    description='Commandline line tool for scraping images from search engines',
	)
	parser.add_argument(
		'download_folder',
	    metavar='folder',
	    help='Path to the directory the images will be saved on, if it does not exist it will be created',
	)

	parser.add_argument(
		'include_db',
		metavar='includedb',
		help='0 or 1 if to include the images on the database or not. 0 does not include, 1 includes',
		type=int,
		choices=[0,1],
	)

	parser.add_argument(
		'type',
		metavar='type',
		help=' "local" if the images are to be saved on your local pc, "test" if these images are to be\
		disregarded or online if they are to sit in the cloud, or "online".',
		type=str,
		choices=["local", "online", "test"],
	)

	parser.add_argument(
		'--sr',
		nargs='+',
		metavar = 'search engines',
		default = ['google'],
		help='search engines separated by spaces. Default is google'
	)

	parser.add_argument(
		'--key_words',
		nargs='+',
		metavar='kwords',
		required = True,
		help='The key words to be scraped, separated by a comma.',
	)

	parser.add_argument(
	    '--n_images',
	    help='The number of images to be scraped per key word per search engine. Defaulted to 10 images',
	    default='10',
	    type = int,
	)

	parser.add_argument(
	    '--timeout',
	    help='Timeout in seconds. Defaulted to 10 seconds',
	    default='10',
	    type = float,
	)

	parser.add_argument(
		'--label',
		metavar='label',
		help='a float between 0 and 1',
		type=float,
		choices=[Range(0,1)],
	)

	args = parser.parse_args()
	#print(args.label)
	scraper = keyword_scraper.Scraper(args.key_words, args.download_folder, args.n_images,\
	args.timeout, args.include_db, args.label, args.type)
	
	for searchEng in args.sr:
		scraper.scrape(searchEng)
	

class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def __eq__(self, other):
        return self.start <= other <= self.end



if __name__ == '__main__':
	main()