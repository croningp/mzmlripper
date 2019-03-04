import re
import os
import sys
import json
from threading import Thread
from spectrum import Spectrum


def create_regex_mapper() -> dict:
    """Creates a mapping of tags to RegEx strings

    Returns:
        dict -- Mapping of tags to RegEx
    """

    return {
        "spec_index": r'index="(.+?)"',
        "array_length": r'defaultArrayLength="(.+?)"',
        "value": r'value="(.+?)"',
        "name": r'name="(.+?)"',
        "binary": r'<binary>(.*?)</binary>'
    }


def value_finder(regex: str, line: str) -> str:
    """Finds a value using RegEx from a given line

    Returns None if nothing found

    Arguments:
        regex {str} -- RegEx string
        line {str} -- Line to parse
    
    Returns:
        str -- Match if found, None if not
    """

    result = re.search(regex, line)

    if result:
        return result.group(1)
    return None


def write_json(data: dict, filename: str):
    """Writes data to JSON file

    Arguments:
        data {dict} -- Data to write
        filename {str} -- Name fo the file
    """

    with open(filename, "w") as f_d:
        json.dump(data, f_d, indent=4)


class MzmlParser(object):
    """Class for parsing an mzML file.

    Extracts all MS1 and MS2 data, along with retention time and parent mass

    Arguments:
        filename {str} -- Name of the file to parse
        output_dir {str} -- Location of where to save the JSON file
    """

    def __init__(self, filename: str, output_dir: str):
        self.filename = filename
        self.output_dir = output_dir
        self.in_spectrum = False
        self.re_expr = create_regex_mapper()
        self.spectra = []
        self.ms1 = []
        self.ms2 = []
        self.spec = Spectrum()
        self.curr_spec_bin_type = -1


    def parse_file(self):
        """Reads the file line by line and obtains all information

        Data is then bulk processed by MS level
        """

        with open(self.filename) as f_d:
            print(f"Parsing file: {self.filename}...")
            for line in f_d.readlines():
                self.process_line(line)

        print(f"Parsing complete!\nTotal Spectra: {len(self.spectra)}")
        print("Processing spectra...")
        ms1 = [spec for spec in self.spectra if spec.ms_level == "1"]
        ms2 = [spec for spec in self.spectra if spec.ms_level == "2"]

        self.bulk_process(ms1, ms2)
        self.write_out_to_file(self.ms1, self.ms2)
        print("Complete!")


    def bulk_process(self, ms1: list, ms2: list):
        """Creates threads for processing MS1 and MS2 data simultaneously
        
        Arguments:
            ms1 {list} -- MS1 data
            ms2 {list} -- MS2 data
        """

        t1 = Thread(target=self.process_spectra, args=(ms1,))
        t2 = Thread(target=self.process_spectra, args=(ms2,))

        t1.start()
        t2.start()

        t1.join()
        t2.join()


    def process_spectra(self, spectra: list):
        """Processes spectra from a list and serialises the data

        Arguments:
            spectra {list} -- List of Spectra
        """

        for spec in spectra:
            spec.process()
            spec = spectra.pop(0)
            if spec.ms_level == "1":
                self.ms1.append(spec)
            elif spec.ms_level == "2":
                self.ms2.append(spec)


    def build_output(self):
        # TODO::Comment
        output = {
            "ms1": {},
            "ms2": {}
        }

        ms1_out, ms2_out = output["ms1"], output["ms2"]
        self.ms1 = sorted(self.ms1, key=lambda x: x.retention_time)
        self.ms2 = sorted(self.ms2, key=lambda x: x.retention_time) 

        for pos, spec in enumerate(self.ms1):
            if not spec.serialized:
                spec.process()
            ms1_out[f"spectrum_{pos+1}"] = spec.serialized

        for pos, spec in enumerate(self.ms2):
            if not spec.serialized:
                spec.process()
            ms2_out[f"spectrum_{pos+1}"] = spec.serialized

        return output


    def write_out_to_file(self, ms1: list, ms2: list):
        """Writes out the MS2 and MS2 data to JSON format
        
        If any spectra are not processed, they are processed here

        Arguments:
            ms1 {list} -- MS1 spectra
            ms2 {list} -- MS2 spectra
        """

        output = self.build_output()

        # Write out
        if sys.platform == "posix":
            name = self.filename.split("/")[0]
        else:
            name = self.filename.split("\\")[0]
        
        # Create output directory if it doesnt exist already
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

        out_path = os.path.join(self.output_dir, name.replace(".mzML", ".json"))
        write_json(output, out_path)


    def process_line(self, line: str):
        """Processes a line from mzML

        Checks if we are in a spectrum or not
        If we're not in a spectrum, check for spectrum tag and pull information

        Continuously check if we've reached the end tag of the spectrum and add the
        spectrum to a list

        If we're in a spectrum and not reached the end tag, check and pull relevant information
        
        Arguments:
            line {str} -- Line form mzML
        """

        if not self.in_spectrum:
            self.start_spectrum(line)
        else:
            if "</spectrum>" in line:
                self.spectra.append(self.spec)
                self.in_spectrum = False
                self.spec = Spectrum()
            else:
                self.extract_information(line)


    def start_spectrum(self, line: str):
        """Initiates the spectrum data gathering process

        Check we get a match for spectrum index tag
        If not, we've got junk and just return
        If we are, extract all information from that line
        
        Arguments:
            line {str} -- Line form mzML
        """

        spec_id = value_finder(self.re_expr["spec_index"], line)
        if not spec_id:
            return

        self.in_spectrum = True
        self.spec.id = spec_id
        self.spec.array_length = value_finder(
            self.re_expr["array_length"],
            line
        )

    def extract_information(self, line: str):
        """Attempts to extract information from a given line

        Information here:
        Retention Time
        32 or 64 bit data
        Type of compression
        MZ data
        Intensity Data
        
        Arguments:
            line {str} -- Line from mzML
        
        Raises:
            Exception -- unable to determine what kind of binary data we're looking at
        """

        if "ms level" in line:
            self.spec.ms_level = value_finder(self.re_expr["value"], line)
        elif "scan start time" in line:
            self.spec.retention_time = value_finder(self.re_expr["value"], line)
        elif "MS:1000521" in line or "MS:1000523" in line:
            self.spec.d_type = value_finder(self.re_expr["name"], line)
        elif "MS:1000574" in line:
            self.spec.compression = value_finder(self.re_expr["name"], line)
        elif "selected ion m/z" in line:
            self.spec.parent = value_finder(self.re_expr["value"], line)
        elif "m/z array" in line:
            self.curr_spec_bin_type = 0
        elif "intensity array" in line:
            self.curr_spec_bin_type = 1
        elif "<binary>" in line:
            binary_text = value_finder(self.re_expr["binary"], line)

            if self.curr_spec_bin_type == 0:
                self.spec.mz = binary_text
            elif self.curr_spec_bin_type == 1:
                self.spec.intensity = binary_text
            else:
                raise Exception("Error setting binary type")
        else:
            return
