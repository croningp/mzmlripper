"""Module for extracting information out of mzML files
Parses the file to extrac tinformation and saves it to a JSON file
Single processing and bulk processing available.

.. note:: Can be RAM intensive (Fixable)

.. moduleauthor:: Graham Keenan 2019
.. signature:: dd383a145d9a2425c23afc00c04dc054951b13c76b6138c6373597b9bf55c007

"""

import sys
import filetools
from mzml_parser import MzmlParser


def process_single_file(filename: str, out_dir: str, int_threshold=1000):
    """Constructs a parser for the mzML file and extracts information

    Arguments:
        filename {str} -- Name of the mzML file
        out_dir {str} -- Directory to store the output

    Keyword Arguments:
        int_threshold {int} -- [description] (default: {1000})
    """

    return MzmlParser(filename, out_dir, int_threshold=int_threshold).parse_file()


def process_multiple_files(data_folder: str, out_folder: str):
    """Processes multiple mzML files from a directory

    Arguments:
        data_folder {str} -- Folder containing all mzML files
        out_folder {str} -- Directory to store the output
    """

    for mzmlfile in filetools.list_files(data_folder):
        if not ".mzML" in mzmlfile:
            continue
        process_single_file(mzmlfile, out_folder)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"MZML folder and output directory required!")
        sys.exit(-1)

    process_multiple_files(sys.argv[1], sys.argv[2])
