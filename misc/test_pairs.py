
import random

def checkValid(pairs, value1, value2, threshold):
	#print(pairs)
	#print(value1, value2, threshold)
	if (len(pairs[value1]) >= threshold or len(pairs[value2]) >= threshold):
		return False
	if (value1 in pairs[value2] or value2 in pairs[value1]):
		return False
	else:
		return True

def main():

	n_pairs = 10

	data = list(range(0, 1000))


	pool = data * 10
	random.shuffle(pool)

	pairs = {}

	for i in data:
		pairs[i] = []



	for i in data:

		while (len(pairs[i]) < n_pairs):
			#j = random.randint(0, len(data) -1)
			#print(j)
			j = pool.pop()
			if (j == i):
				pool = [j] + pool
				continue
			
			if (checkValid(pairs, i, j, n_pairs)): 
				pairs[i].append(j)
				pairs[j].append(i)
				#print(counter)
			else:
				pool = [j] + pool
				continue
	print (pairs)

if __name__ == '__main__':
	main()





