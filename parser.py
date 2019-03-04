import re
import sys
import json
from multiprocessing import Process
from threading import Lock, Thread
from spectrum import Spectrum

# TODO::Bulk processing of multiple mzML files

def create_regex_mapper() -> dict:
    return {
        "spec_index": r'index="(.+?)"',
        "array_length": r'defaultArrayLength="(.+?)"',
        "value": r'value="(.+?)"',
        "name": r'name="(.+?)"',
        "binary": r'<binary>(.*?)</binary>'
    }


def value_finder(regex: str, line: str) -> str:
    result = re.search(regex, line)

    if result:
        return result.group(1)
    return None

def write_json(data, filename):
    with open(filename, "w") as f_d:
        json.dump(data, f_d, indent=4)


def split_list(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


class Parser(object):
    def __init__(self, filename: str):
        self.filename = filename
        self.in_spectrum = False
        self.re_expr = create_regex_mapper()
        self.spectra = []
        self.out_spectra = []
        self.spec = Spectrum()
        self.curr_spec_bin_type = -1


    def parse_file(self):
        with open(self.filename) as f_d:
            print(f"Parsing file: {self.filename}...")
            for line in f_d.readlines():
                self.process_line(line)

        print(f"Parsing complete!\nTotal Spectra: {len(self.spectra)}")
        print("Processing...")
        self.bulk_process()
        self.post_process()
        print("Complete!")


    def bulk_process(self):
        process_pool = []
        data_pool = list(
            split_list(
                self.spectra,
                int(len(self.spectra)/4)
            )
        )

        for spectra_list in data_pool:
            p = Thread(target=self.process_spectra, args=(spectra_list,))
            process_pool.append(p)
            p.start()

        for process in process_pool:
            process.join()


    def process_spectra(self, spectra):
        for pos, spectrum in enumerate(spectra):
            spectrum.process()
            self.out_spectra.append(spectrum)
            spectra.pop(pos)



    def post_process(self):
        ms1, ms2 = [], []
        for spectrum in self.out_spectra:
            if spectrum.ms_level == "1":
                ms1.append(spectrum)
            elif spectrum.ms_level == "2":
                ms2.append(spectrum)

        self.write_out_to_file(ms1, ms2)


    def write_out_to_file(self, ms1, ms2):
        output = {
            "ms1": {},
            "ms2": {}
        }

        ms1_out, ms2_out = output["ms1"], output["ms2"]

        for pos, spec in enumerate(ms1):
            ms1_out[f"spectrum_{pos+1}"] = spec.serialized

        for pos, spec in enumerate(ms2):
            ms2_out[f"spectrum_{pos+1}"] = spec.serialized

        write_json(output, self.filename.replace(".mzML", ".json"))


    def process_line(self, line: str):
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

if __name__ == "__main__":
    p = Parser(sys.argv[1])
    p.parse_file()