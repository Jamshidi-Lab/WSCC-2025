import numpy as np


def parse_orca_output(output_file_path):
    """
    Parse the ORCA output file to extract:
    - Overlap matrix S
    - Kinetic matrix T (if available)
    - Nuclear attraction matrix V (if available)
    - Two-electron integrals or Fock matrix
    Returns a dictionary with these arrays.
    """

    S = None
    T = None
    V = None
    ERI = None

    # ... read lines, parse data into arrays ...
    # e.g.:
    # with open(output_file_path, 'r') as f:
    #     lines = f.readlines()
    #     # parse lines for matrix data

    return {
        "S": S,
        "T": T,
        "V": V,
        "ERI": ERI
    }
