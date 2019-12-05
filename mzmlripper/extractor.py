"""Module for extracting information out of mzML files
Parses the file to extrac tinformation and saves it to a JSON file
Single processing and bulk processing available.

.. note:: Can be RAM intensive on larger file sizes

.. moduleauthor:: Graham Keenan (Cronin Group 2019) <graham.keenan@glasgow.ac.uk>
.. signature:: dd383a145d9a2425c23afc00c04dc054951b13c76b6138c6373597b9bf55c007

"""

from .mzml_parser import MzmlParser


def process_mzml_file(filename: str, out_dir: str, int_threshold=1000):
    """Constructs a parser for the mzML file and extracts information

    Arguments:
        filename {str} -- Name of the mzML file
        out_dir {str} -- Directory to store the output

    Keyword Arguments:
        int_threshold {int} -- Intensity threshold for peaks (default: {1000})
    """

    return MzmlParser(filename, out_dir, int_threshold=int_threshold).parse_file()
