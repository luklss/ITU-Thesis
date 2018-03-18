
import csv
import statistics
from PIL import Image
import requests
from io import BytesIO
import argparse

PATH_TO_FILE = "../mturk/Batch_3134899_batch_results.csv"

"""
This script has two purposes. First is to calculate a divergency measure defined as "the percentage of votes that deviate from the most frequent vote across
the whole data set". The second purpouse is, given a worker, visually inspects his votes.
"""

class Worker:
	"""Defines a mturk worker as his id and votes he had"""

	def __init__(self, id):
		self.id = id
		self.votes = {}

	def add_vote(self, img_tuple, vote):
		self.votes[img_tuple] = vote

	def __eq__(self, other):
		return self.id == other.id

	def __repr__(self):
		return str(self.votes)

	def inspectVote(self, img_tuple):
		print(img_tuple)
		try:
			img1_req = requests.get(img_tuple[0], timeout = 10)
			img1 = Image.open(BytesIO(img1_req.content))
			img2_req = requests.get(img_tuple[1], timeout = 10)
			img2 = Image.open(BytesIO(img2_req.content))

			img1.show()
			input("image 1")
			img2.show()
			input("image 2")

			print(self.votes[img_tuple])
		except Exception as e:
			print ("could not load link")
			print(e)



def GetWorkersVotesAndMostVoted(csv_path):
	"""
	Given an csv path, this function loads a dictonary with the most frequent vote per pair of images
	and another one mapping a workerid to a worker object. The worker object also contains a dictonary
	that maps a pair of images to the worker vote
	"""
	header = {}

	with open(csv_path, 'r') as f:
		reader = csv.reader(f, delimiter = ',', quotechar = '"')
		header_input = next(reader)
		votes = {}
		votes_count = {}
		workers = {}
		for k, v in enumerate(header_input):
			header[v] = k
		for row in reader:

			worker_id = row[header["WorkerId"]]

			for i in range(10):
				img_1 = row[header["Input.image_" + str(i) + "-1"]]
				img_2 = row[header["Input.image_" + str(i) + "-2"]]
				vote = int(row[header["Answer.choice" + str(i)]])
				#print(img_1, " ", img_2, " ", vote)
				if (img_1, img_2) not in votes:
					votes[(img_1, img_2)] = [vote]
				else:
					votes[(img_1, img_2)].append(vote)

				if worker_id not in workers:
					workers[worker_id] = Worker(worker_id)

				workers[worker_id].add_vote((img_1, img_2), vote)


		for key, value in votes.items():
			#print(key)
			try:
				votes_count[key] = statistics.mode(value)
			except Exception:
				continue

	return votes_count, workers



def GetWorkersDivergencyPercentage(votes, workers):
	"""
	Given a dictonary "votes" mapping a pair of images (tuple) to the mode of the votes,
	and a dictonary mapping workers ids to worker objects,
	this function returns a dictonary mapping a worker id to the percentage of times he 
	diverges from the most frequent vote
	"""

	result = {}

	for worker_id, worker in workers.items():
		total_votes = len(worker.votes)
		divergent_votes = 0
		for pair, vote in worker.votes.items():
			if pair not in votes:
				continue
			most_voted = votes[pair]
			if vote != most_voted:
				divergent_votes += 1
		result[worker_id] = float(divergent_votes/total_votes)
	return result


def outPutWorkerDivergency(workers_div):
	"""Prints out the results from the worker divergence dict """
	for tup in sorted(workers_div.items(), key=lambda x: x[1]):
		print(tup[0], ",", tup[1])

def inspectWorkersVotes(worker_id, workers):
	""" display the images and vote for each pair for a given worker """
	worker = workers[worker_id]
	for pair in worker.votes:
		worker.inspectVote(pair)
		input("next pair")


def main(csv_path, worker_id):
	pairs_most_votes, workers = GetWorkersVotesAndMostVoted(csv_path)
	if worker_id is None:
		workers_divergency = GetWorkersDivergencyPercentage(pairs_most_votes, workers)
		outPutWorkerDivergency(workers_divergency)
	else:
		inspectWorkersVotes(worker_id, workers)



if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		prog='Annomaly detection script',
	    description='This script can output a sorted list with the id of each worker and its\
	    divergency percentage score OR given a workerid, it can be used to visually inspect\
	    the workers vote'
	)
	parser.add_argument(
		'--csv_path',
	    metavar='path',
	    help='Path to the csv file',
	    default = PATH_TO_FILE
	)
	parser.add_argument(
		'--worker_id',
	    metavar='path',
	    help='Path to the csv file',
	    type = str
	)
	args = parser.parse_args()
	main(args.csv_path, args.worker_id)
