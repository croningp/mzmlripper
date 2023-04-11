import extractor as ripper
mzml_filename = 'Cinchonidine_MS5_20230327014135.mzML'
target_directory = '.'
ripper_data = ripper.process_mzml_file(mzml_filename, target_directory)
