# MzML Ripper

This package parses a single MzML or multiple MzML files and extracts data into JSON format for that file.
Extracts the following information:

* MS1 Information
* MS2 Information
* For each spectrum in MS1/2:
    * Masses and Intensities
    * Parent of that spectrum
    * Retention time of that spectrum
    * List of masses

## Installation

You can either clone the repo and run the installation script:
```
git clone http://datalore.chem.gla.ac.uk/Origins/mzmlripper.git

python setup.py install --user

```

Or download directly from Pip:
```
pip install git+http://datalore.chem.gla.ac.uk/Origins/mzmlripper.git --user

```

## Usage

Import the extractor and give it a file/directory and an output directory for the JSON files

```python
import mzmlripper.extractor as mzml

# Running on a single file
# Give a mzML filename and an output directory
data = mzml.process_single_file("filename.mzML", "json_output/")

# Running on multiple files
# Give a directory containing mzMLs and a directory for output
mzml.process_multiple_files("mzml_dir/", "json_output/")

```

## Output
The file output is in the following format:

```json
{
    "ms1": {
        "sppectrum_1": {
            "95.3423": 160,
            "96.8473": 322,
            "110.8476": 640253,
            ...
            "parent": "",
            "retention_time": "0.9685"
            "mass_list": [
                95.3423,
                96.8473,
                110.8476
                ...
            ]
        },
        "spectrum_2": {
            ...
        },
        ...
    },
    "ms2": {
        "spectrum_1": {
            "101.2356": 4552,
            "102.5398": 12369,
            "102.9856": 845,
            ...
            "parent": "235.6523",
            "retention_time": "1.1203",
            "mass_list": [
                101.2356,
                102.5398,
                102.9856,
                ...
            ]
        },
        "spectrum_2": {
            ...
        },
        ...
    }
}