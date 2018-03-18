library ("dplyr")

FILE_PATH = "../mturk/Batch_3134899_batch_results.csv"

data = read.table(FILE_PATH, fill = TRUE, sep = ",", header = TRUE)

