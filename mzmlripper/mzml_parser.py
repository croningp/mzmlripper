"""Module for parsing mzML files
Reads file line by line and extracts out all relevant information
Information being MS1 and MS2 spectra data

Extracts:
    Scan:
    M/z List
    Intensity List
    Parent mass
    Parent Scan
    Mass List
    Retention Time

.. moduleauthor:: Graham Keenan <graham.keenan@glasgow.ac.uk>
.. signature:: dd383a145d9a2425c23afc00c04dc054951b13c76b6138c6373597b9bf55c007

"""

# System imports
import os
import re
import json
from threading import Thread
from typing import List, Optional, Dict

# Ripper imports
from .spectrum import Spectrum
from .logger import make_logger, colour_item

# List of banned phrases to ignore as they can screw with the parsing
BANNED_PHRASES = ["<userParam"]

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
        "binary": r'<binary>(.*?)</binary>',
        "scan": r'scan=([0-9]+)'
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

def banned_phrases(line: str) -> bool:
    """Small check to determine if any banned phrase is in a given line.
    Banned phrases are phrases that can interfere with the parsing and indicate
    that the parser should ignore said line.

    Args:
        line (str): Line to check

    Returns:
        bool: Banned phrase exists
    """

    # Iterate through all banned phrases
    for phrase in BANNED_PHRASES:
        # Phrase is banned
        if phrase in line:
            return True

    # No banned phrases found
    return False

class InvalidInputFile(Exception):
    """Exception for invalid file formats
    """


class MzmlParser:
    """Class for parsing an mzML file.

    Extracts all MS1 and MS2 data, along with retention time and parent mass

    Args:
        filename (str): Name of the file to parse
        output_dir (str): Location of where to save the JSON file
        rt_units (int, optional): Retention time units. Defaults to `None`
        int_threshold (int, optional): Intensity Threshold. Defaults to 1000.
        relative_intensity (bool, optional): Specifies whether final intensities
            for individual ions in spectra are displayed as relative (%) or
            absolute intensities. Defaults to False.
    """

    def __init__(
        self,
        filename: str,
        output_dir: str,
        rt_units: Optional[int] = None,
        int_threshold: Optional[int] = 1000,
        relative_intensity: Optional[bool] = False
    ):
        self.logger = make_logger("MzMLRipper")
        self.filename = filename
        self.output_dir = os.path.abspath(output_dir)
        self.in_spectrum = False
        self.re_expr = create_regex_mapper()
        self.spectra = []
        self.ms1, self.ms2, self.ms3, self.ms4 = [], [], [], []
        self.spec = Spectrum(
            intensity_threshold=int_threshold,
            relative=relative_intensity
        )
        self.relative = relative_intensity
        self.spec_int_threshold = int_threshold
        self.curr_spec_bin_type = -1
        self.rt_units = rt_units

    def _check_file(self):
        """Checks if a file is valid for the parser
        Checks if the file is actually a file and if it is an mzML file

        Raises:
            InvalidInputFile: File is invalid
        """

        if (
            not os.path.isfile(self.filename)
            or not self.filename.endswith(".mzML")
        ):
            raise InvalidInputFile(f"File {self.filename} is not valid!")

    def parse_file(self) -> Dict:
        """Reads the file line by line and obtains all information

        Data is then bulk processed by MS level

        Returns:
            Dict: Dictionary of each spectrum split by MS level
        """

        # CHeck the file exists and is an MzML file
        self._check_file()

        # Open the file and process each line individually
        with open(self.filename) as f_d:
            self.logger.info(
                f"Parsing file: {colour_item(self.filename, 'yellow')}..."
            )
            for line in f_d.readlines():
                self.process_line(line)

        self.logger.info(
            f"Parsing complete!\nTotal Spectra:\
 {colour_item(str(len(self.spectra)), 'green')}"
        )
        self.logger.info("Processing spectra...")

        # Get all MS level spectra from the collection
        ms_levels = [
            [spec for spec in self.spectra if spec.ms_level == str(level)]
            for level in range(1, 5)
        ]

        # Process and write out to file
        self.bulk_process(*ms_levels)
        output = self.write_out_to_file()
        self.logger.info(f"{colour_item('Complete', 'green')}")

        return output

    def bulk_process(self, *ms_levels: List[Spectrum]):
        """Creates threads for processing MS1 and MS2 data simultaneously

        Arguments:
            ms_levels (List[Spectrum]): Collection of MS spectra
        """

        pool = [
            Thread(target=self.process_spectra, args=(ms,))
            for ms in ms_levels
        ]

        [thread.start() for thread in pool]
        [thread.join() for thread in pool]

    def process_spectra(self, spectra: List[Spectrum]):
        """Processes spectra from a list and serialises the data

        Arguments:
            spectra (List[Spectrum]): List of Spectra
        """

        for spec in spectra:
            spec.process()
            if spec.ms_level == "1":
                self.ms1.append(spec)
            elif spec.ms_level == "2":
                self.ms2.append(spec)
            elif spec.ms_level == "3":
                self.ms3.append(spec)
            elif spec.ms_level == "4":
                self.ms4.append(spec)

    def build_output(self) -> Dict:
        """Builds the MS data output from the MS1 and MS2 data

        Returns:
            Dict: MS spectra split by level
        """

        # Create the output
        output = {
            "ms1": {},
            "ms2": {},
            "ms3": {},
            "ms4": {}
        }

        # Set vars to work with
        ms1_out = output["ms1"]
        ms2_out = output["ms2"]
        ms3_out = output["ms3"]
        ms4_out = output["ms4"]

        # Sort the MS spectra by retention time
        self.ms1 = sorted(self.ms1, key=lambda x: x.retention_time)
        self.ms2 = sorted(self.ms2, key=lambda x: x.retention_time)
        self.ms3 = sorted(self.ms3, key=lambda x: x.retention_time)
        self.ms4 = sorted(self.ms4, key=lambda x: x.retention_time)

        # Populate the output
        for pos, spec in enumerate(self.ms1):
            if not spec.serialized:
                spec.process()
            if spec.serialized["mass_list"]:
                ms1_out[f"spectrum_{pos+1}"] = spec.serialized

        for pos, spec in enumerate(self.ms2):
            if not spec.serialized:
                spec.process()
            if spec.serialized["mass_list"]:
                ms2_out[f"spectrum_{pos+1}"] = spec.serialized

        for pos, spec in enumerate(self.ms3):
            if not spec.serialized:
                spec.process()
            if spec.serialized["mass_list"]:
                ms3_out[f"spectrum_{pos+1}"] = spec.serialized

        for pos, spec in enumerate(self.ms4):
            if not spec.serialized:
                spec.process()
            if spec.serialized["mass_list"]:
                ms4_out[f"spectrum_{pos+1}"] = spec.serialized

        return output

    def write_out_to_file(self):
        """Writes out the MS1 and MS2 data to JSON format

        If any spectra are not processed, they are processed here

        Arguments:
            ms1 List[Spectrum] MS1 spectra
            ms2 List[Spectrum] MS2 spectra
        """

        output = self.build_output()

        name = self.filename.split(os.sep)[-1]

        name = "ripper_" + name
        out_path = os.path.join(
            self.output_dir, name.replace(".mzML", ".json"))

        if not os.path.exists(os.path.dirname(out_path)):
            os.makedirs(os.path.dirname(out_path))
        write_json(output, out_path)

        return output

    def process_line(self, line: str):
        """Processes a line from mzML

        Checks if we are in a spectrum or not
        If we're not in a spectrum, check for spectrum tag and pull information

        Continuously check if we've reached the end tag of the spectrum and
        add the spectrum to a list

        If we're in a spectrum and not reached the end tag,
        check and pull relevant information

        Arguments:
            line {str} -- Line form mzML
        """

        # Currently not in a spectrum, set the spectrum flag
        if not self.in_spectrum:
            self.start_spectrum(line)

        # Look for end of spectrum tag
        else:
            if "</spectrum>" in line:
                self.spectra.append(self.spec)
                self.in_spectrum = False
                self.spec = Spectrum(
                    intensity_threshold=self.spec_int_threshold,
                    relative=self.relative
                )
            else:
                if banned_phrases(line):
                    return

                self.extract_information(line)

    def start_spectrum(self, line: str):
        """Initiates the spectrum data gathering process

        Check we get a match for spectrum index tag
        If not, we've got junk and just return
        If we are, extract all information from that line

        Arguments:
            line (str): Line from mzML
        """

        # Extract the spectrum ID
        spec_id = value_finder(self.re_expr["spec_index"], line)
        if not spec_id:
            return

        # Set the flag and ID
        self.in_spectrum = True
        self.spec.id = spec_id

        # Find the size of the data array
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
            line (str): Line from mzML

        Raises:
            Exception: Unable to determine what kind of binary data
            we're looking at.
        """

        # MS Level
        if "MS:1000511" in line:
            self.spec.ms_level = value_finder(self.re_expr["value"], line)

        # Scan Number
        elif "MS:1000796" in line:
            self.spec.scan = value_finder(self.re_expr["scan"], line)

        # Retention time
        elif "MS:1000016" in line:
            rt_converter = 1
            if self.rt_units == 'sec':
                rt_converter = 60
            self.spec.retention_time = str(float(value_finder(
                self.re_expr["value"], line)) / rt_converter)

        # Data type (32 or 64 bit)
        elif "MS:1000521" in line or "MS:1000523" in line:
            self.spec.d_type = value_finder(self.re_expr["name"], line)

        # Compression type
        elif "MS:1000574" in line:
            self.spec.compression = value_finder(self.re_expr["name"], line)

        # Parent mass
        elif "MS:1000744" in line:
            self.spec.parent_mass = value_finder(self.re_expr["value"], line)

        # Parent Scan
        elif "<precursor spectrumRef" in line:
            self.spec.parent_scan = value_finder(self.re_expr["scan"], line)

        # Suggested parent mass
        elif "MS:1000512" in line:
            suggested_parent = value_finder(self.re_expr["value"], line)
            self.update_parent(suggested_parent)

        # MZ data
        elif "MS:1000514" in line:
            self.curr_spec_bin_type = 0

        # Intensity data
        elif "MS:1000515" in line:
            self.curr_spec_bin_type = 1

        # Binary blob
        elif "<binary>" in line:
            binary_text = value_finder(self.re_expr["binary"], line)

            # Looking at MZ values
            if self.curr_spec_bin_type == 0:
                self.spec.mz = binary_text

            # Looking at intensity values
            elif self.curr_spec_bin_type == 1:
                self.spec.intensity = binary_text

            # No idea what we're looking at
            else:
                raise Exception("Error setting binary type")

        # Nothing
        else:
            return

    def update_parent(self, filter_string: str):
        """Updates the parent for MS3 and above

        Arguments:
            filter_string (str): String containing parent
        """

        # Below MS level 3
        if int(self.spec.ms_level) < 3:
            return

        # Sets the parent for MS levels 3 and above
        parents = filter_string.split("@")
        if self.spec.ms_level == "3":
            self.spec.parent_mass = parents[1].split(" ")[-1]
        elif self.spec.ms_level == "4":
            self.spec.parent_mass = parents[2].split(" ")[-1]
