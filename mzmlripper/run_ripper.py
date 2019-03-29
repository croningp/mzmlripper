from extractor import*

def main(mzml_folder):
    process_multiple_files(mzml_folder, output_folder)


mzml_folder = ''
output_folder = ''

if __name__ == '__main__':
    main(mzml_folder, output_folder)