# MzML Ripper

This package parses MzML files and extracts data into JSON format for easier processing.


Extracts the following information:

* MS1 Information
* MS2 Information
* MS3 Information
* MS4 Information


* For each spectrum in MS1/2/3/4:
    * Masses and Intensities
    * Parent of that spectrum
    * Retention time of that spectrum
    * List of masses

---

## Installation

Mzmlripper is available through Pip (Python Package Index):
```
pip install mzmlripper --user
```

Source code will be made available in due course.

### Dependencies
If you want to use the (optional) SPectraL hASHing functions (see https://splash.fiehnlab.ucdavis.edu/ for more details), 
you may want to install pySPLASH with the following commands:
```
git clone git://github.com/berlinguyinca/spectra-hash.git
cd spectra-hash/python
python setup.py install

```

---

## Usage

Import the extractor and give it a file/directory and an output directory for the JSON files

```python
# Import module
import mzmlripper.extractor as ripper

# Process an mzML file
ripper_data = ripper.process_mzml_file(mzml_filename, target_directory)

# Using the pySPLASH functions
import mzmlripper.splash_helpers as spl

# Add splash to each ripper function
splashed_ripper_data = spl.splash_ripper_dict(ripper_data)

```

---

## Output

### Standard Output

The file output is in the following format:

```json
{
    "ms1": {
        "spectrum_1": {
            "95.3423": 160,
            "96.8473": 322,
            "110.8476": 640253,
            ...
            "parent": "",
            "retention_time": "0.9685",
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
    },
    "ms3": {
        "spectrum_1": {
            "67.3434": 142,
            "69.8364": 1325,
            "72.9746": 3320,
            ...
            "parent": "102.2365",
            "retention_time": "1.0253",
            "mass_list": [
                67.3434,
                69.8364,
                72.9746,
                ...
            ]
        },
        "spectrum_2": {
            ...
        },
        ...
    },
    "ms4": {
        "spectrum_1": {
            "45.2036": 1234,
            "46.3210": 8853,
            "49.3205": 12342,
            ...
            "parent": "115.3256",
            "retention_time": "2.0365",
            "mass_list": [
                45.2036,
                46.3120,
                49.3205,
                ...
            ]
        },
        "spectrum_2": {
            ...
        },
        ...
    }
}
```
### Relative Intensity Output

The example above shows standard output of mzmlripper, with absolute intensity values of
individual ions. However, there is also an option for displaying relative intensity values
of ions in spectra:

```
# Process an mzML file with final output showing relative intensities
ripper_data = ripper.process_mzml_file(mzml_filename, target_directory, relative=True)
```
This will result in output of a very similar format to the standard output, with two differences:

1. Intensity values are relative, with the most intense peak being set to 100 %
2. The base peak (most intense peak) is recorded in each spectrum, along with its absolute intensity. This enables the original, absolute intensity values of all peaks to be calculated later if required.

Here is the above example converted to relative intensity spectra:

```json
{
    "ms1": {
        "spectrum_1": {
            "95.3423": 0.0250,
            "96.8473": 0.0503,
            "110.8476": 100,
            ...
            "parent": "",
            "base_peak": [110.8476, 640253],
            "retention_time": "0.9685",
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
            "101.2356": 36.8017,
            "102.5398": 100,
            "102.9856": 6.8316,
            ...
            "parent": "235.6523",
            "base_peak": [102.5398, 12369],
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
    },
    ...
}

```


---


## Authors

All software was written as part of the [Cronin Lab 2019](http://www.chem.gla.ac.uk/cronin/)

* [Graham Keenan](mailto:Graham.Keenan@glasgow.ac.uk)
* [Dr. David Doran](mailto:d.doran.1@research.gla.ac.uk)
* [Dr. Cole Mathis](mailto:Cole.Mathis@glasgow.ac.uk)

---

## Contributions

* [Dr. Emma Carrick](mailto:Emma.Carrick@glasgow.ac.uk)


---

## License

[![MIT](https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/MIT_logo.svg/220px-MIT_logo.svg.png)](https://opensource.org/licenses/MIT)
