import re


def extract_title_blocks(full_text):
    """
    Scans 'full_text' for blocks of the form:
        --------------
        TITLE
        --------------
      and returns a list of (title, lines_for_that_block).
    Each block is everything from the line after the second row of dashes
    up to (but not including) the next block's dashes, or end of text.
    """
    lines = full_text.splitlines()
    n = len(lines)
    blocks = []

    i = 0
    while i < n - 2:
        line_i = lines[i].strip()
        line_i1 = lines[i+1].strip() if (i+1 < n) else ""
        line_i2 = lines[i+2].strip() if (i+2 < n) else ""

        # Check if lines i and i+2 are "dashes", and i+1 is a potential title
        # A simple check is to see if it's at least some repeated '-' characters.
        # You can tweak this regex or the test as needed.
        dash_pattern = r'^-+\s*$'

        if (re.match(dash_pattern, line_i) and
            # i+1 is not dashes => could be the title
            not re.match(dash_pattern, line_i1) and
                re.match(dash_pattern, line_i2)):
            # We found a title block
            title = line_i1  # The actual text of the title
            # Move index to the line after i+2
            i += 3

            # Collect lines for this block until we hit another dashed line
            # that might indicate a new block (or EOF).
            block_lines = []
            while i < n:
                # Peek ahead to see if the next lines look like a new title block
                # If so, break
                if i + 2 < n:
                    maybe_dash = lines[i].strip()
                    maybe_title = lines[i+1].strip()
                    maybe_dash2 = lines[i+2].strip()
                    if (re.match(dash_pattern, maybe_dash) and
                        not re.match(dash_pattern, maybe_title) and
                            re.match(dash_pattern, maybe_dash2)):
                        # This signals the start of a new block
                        break
                # Otherwise, add this line to the current block
                block_lines.append(lines[i])
                i += 1

            blocks.append((title, block_lines))
        else:
            i += 1

    return blocks


def parse_matrix_block(block_lines):
    """
    Given the lines of a block that presumably contains the
    multi-chunk matrix (like the ONE ELECTRON MATRIX or OVERLAP MATRIX),
    parse them using the column-chunk approach.
    Returns a 2D list (matrix) or None if parsing fails.
    """

    data_dict = {}
    all_rows = set()
    all_cols = set()

    i = 0
    while i < len(block_lines):
        line = block_lines[i].rstrip()
        # Check if the line is a column-indices line
        # e.g. "      0          1          2          3          4          5"
        # We split and see if all are digits:
        col_parts = line.split()
        if all(re.match(r'^\d+$', c) for c in col_parts):
            # This means we found a chunk specifying columns
            cols_current_chunk = list(map(int, col_parts))
            i += 1

            # Now read subsequent lines which should be row index + floats
            while i < len(block_lines):
                row_line = block_lines[i].strip()
                row_parts = row_line.split()
                if not row_parts:
                    i += 1
                    continue

                # The first part might be a row index
                if re.match(r'^\d+$', row_parts[0]):
                    row_idx = int(row_parts[0])
                    all_rows.add(row_idx)

                    float_parts = row_parts[1:]
                    # We expect len(float_parts) == len(cols_current_chunk)
                    if len(float_parts) != len(cols_current_chunk):
                        # If mismatch, it might mean we've reached another columns line or end
                        break

                    for col_idx, val_str in zip(cols_current_chunk, float_parts):
                        val = float(val_str)
                        data_dict[(row_idx, col_idx)] = val
                        all_cols.add(col_idx)

                    i += 1
                else:
                    # We hit something that doesn't look like a row
                    # => could be next chunk
                    break
        else:
            i += 1

    if not data_dict:
        return None

    max_row = max(all_rows)
    max_col = max(all_cols)
    size = max(max_row, max_col) + 1  # in case it's square

    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    for (r, c), val in data_dict.items():
        matrix[r][c] = val

    return matrix


def parse_all_matrices(full_text):
    """
    1) Finds all blocks in 'full_text' of the form:
           --------------
           TITLE
           --------------
       and collects the text that follows each until the next block.
    2) Tries to parse each block as a matrix (with chunked columns).
    3) Returns a dictionary:  { title : matrix_data, ... }
       If a block cannot be parsed as a matrix, we store None (or skip it).
    """
    blocks = extract_title_blocks(full_text)
    results = {}

    for title, block_lines in blocks:
        # Attempt to parse it as a matrix
        matrix = parse_matrix_block(block_lines)
        results[title] = matrix

    return results


# ------------------------------------------------------------------------
# DEMO with your sample text
if __name__ == "__main__":
    text_block = r"""
Diagonalization of the overlap matrix:
Smallest eigenvalue                        ... 3.385e-01
Time for diagonalization                   ...    0.005 sec
Threshold for overlap eigenvalues          ... 1.000e-08
Number of eigenvalues below threshold      ... 0
Time for construction of square roots      ...    0.002 sec
Producing symmetrization matrix            ... done (   0.001 sec)
Total time needed                          ...    0.008 sec

------------------------
ONE ELECTRON MATRIX (AU)
------------------------
                  0          1          2          3          4          5    
      0      -5.096089  -1.776195  -3.779156  -1.595649  -2.088509   0.000000
      1      -1.776195 -32.728255  -7.614542  -0.018560   0.000000   0.000000
      2      -3.779156  -7.614542  -9.341458  -0.217795   0.000000   0.000000
      3      -1.595649  -0.018560  -0.217795  -7.551373   0.000000   0.000000
      4      -2.088509   0.000000   0.000000   0.000000  -7.628461   0.000000
      5       0.000000   0.000000   0.000000   0.000000   0.000000  -7.463078
      6      -1.574080  -1.776195  -3.779156  -1.595649   2.088509   0.000000
                  6    
      0      -1.574080
      1      -1.776195
      2      -3.779156
      3      -1.595649
      4       2.088509
      5       0.000000
      6      -5.096089
--------------
OVERLAP MATRIX
--------------
                  0          1          2          3          4          5    
      0       1.000000   0.054790   0.478949   0.233409   0.319445   0.000000
      1       0.054790   1.000000   0.236704   0.000000   0.000000   0.000000
      2       0.478949   0.236704   1.000000  -0.000000   0.000000   0.000000
      3       0.233409   0.000000  -0.000000   1.000000   0.000000   0.000000
      4       0.319445
"""

    matrices = parse_all_matrices(text_block)

    # Print out what we got
    for title, matrix_data in matrices.items():
        print(f"\nTITLE BLOCK: {title}")
        if matrix_data is None:
            print(" -> Could not parse as matrix.")
        else:
            print(" -> Parsed matrix:")
            for row in matrix_data:
                print("    ", row)
