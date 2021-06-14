# Release 1.3.1

* Fixed issue with certain custom phrases would interfere with the parsing
  * Vendors may add in their own custom tags (e.g. `<userParam>`) that may contain values that the parser used so a list of banned phrases have been introduced to prevent this from happening
  * Replaced hard-coded values for tags such as `ms level` and `selected ion m/z` with their MzML MS tag equivalent (e.g. `MS:1000571`)

# Release 1.3.0

* Added ability to generate different classes of Chromatograms
  * Extracted Ion Chromatograms (EICs)
  * Base Peak Chromatograms (BPCs)
  * Total Ion Currents (TICs)

# Release 1.2.0

* Added ability to display spectra with relative intensities

## Release 1.2.1

* Fixed bug when writing out to file if the original `mzml` file is within a subdirectory

# Release 1.1.0

* Added in Spectral Hash (SPLASH) of spectra from the SPLASH API

# Release 1.0.0

* Initial Release
  * Parse mzML files to obtain spectra for each MS level (up to 4) and dumps them into JSON format