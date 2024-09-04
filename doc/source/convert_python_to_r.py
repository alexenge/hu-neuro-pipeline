import pandas as pd

csv_file = '/Users/alexander/Code/hu-neuro-pipeline/doc/source/tables/epoching.csv'

df = pd.read_csv(csv_file)

for python_str in df['Python example']:
    r_str = python_str.\
        replace('\'', '"').\
        replace('[(', 'list(c(').\
        replace(')]', '))').\
        replace(': [', ' = list(').\
        replace('[', 'c(').\
        replace(']', ')').\
        replace('{', 'list(').\
        replace(':', ' =').\
        replace('}', ')').\
        replace('True', 'TRUE').\
        replace('False', 'FALSE').\
        replace('None', 'NULL')
    print(python_str)
    print(r_str, '\n')

    # TODO:
    # * Deal with np.arange (if-statement)
    # * Deal with tuples (starting with "(")
    # * Remove additional text from column (i.e., make each option a different row)
    # * Apply conversion also to the first column ("default")
    # * GitHub action to automatically convert the table
    # * Delete R column
