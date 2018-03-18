

from PIL import Image
import numpy as np
import os
import time
import imageio

def ReadImagesFromFolder(folder):
	
	""" Reads all images from a folder and its subfolders into memory"""
	result = []
	for subdir, dirs, files in os.walk(folder):
		for idx, file in enumerate(files):
			print("reading img number ", idx)
			if (file.startswith(".DS")):
				continue
			path = os.path.join(subdir, file)
			img = imageio.imread(path)
			img_array = np.array(img)
			result.append(img_array)
	return np.array(result)