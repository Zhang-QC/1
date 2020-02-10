# CS122: Linking restaurant records in Zagat and Fodor's data sets
#
# Jason Zhang


import numpy as np
import pandas as pd
import jellyfish
import util

def find_matches(mu, lambda_, block_on_city=False):
    # WRITE YOUR CODE HERE
    # AND REPLACE THE BELOW RETURN STATEMENT
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


if __name__ == '__main__':
    matches, possibles, unmatches = \
        find_matches(0.005, 0.005, block_on_city=False)

    print("Found {} matches, {} possible matches, and {} "
          "unmatches with no blocking.".format(matches.shape[0],
                                               possibles.shape[0],
                                               unmatches.shape[0]))
