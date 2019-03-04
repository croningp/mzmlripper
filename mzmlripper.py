import os
import sys
import filetools
from mzml_parser import MzmlParser

def process_single_file(filename, out_dir):
    MzmlParser(filename, out_dir).parse_file()

def process_multiple_files(data_folder, out_folder):
    for mzmlfile in filetools.list_files(data_folder):
        if not ".mzML" in mzmlfile:
            continue
        process_single_file(mzmlfile, out_folder)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"MZML folder and output directory required!")
        sys.exit(-1)
    
    process_multiple_files(sys.argv[1], sys.argv[2])
