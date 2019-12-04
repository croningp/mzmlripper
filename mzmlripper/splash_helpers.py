"""Module for getting a SPectral hASH (SPLASH) from a spectra


.. moduleauthor:: Cole Mathis 2019
.. signature:: 
"""

import json
SLAPSH_API_URL = "https://splash.fiehnlab.ucdavis.edu/splash/it"

def _initSPLASHpackage():
    """ This function checks for the installation of the pySPLASH package. 
        If the package is installed it will use it to generate SPLASHS.
        If the pySPLASH package isn't installed it will give the user the option
        to exit and install pySPLASH (with instructions) or to proceed with the 
        SPLASH webAPI, which is slow.
    
    """
    # Initialize with the pySPLASH implementation
    implementation = "pySPLASH"
    try:
        # Try to import it
        from splash import Spectrum, SpectrumType, Splash
    except ImportError:
        # If you can't import give a warning and prompt the user to decide what to do
        print("pySPLASH not installed in local env!!! You've got two options:")
        print(
            "1) Proceed using the web API (this is really slow if you've got a large number of spectra to process)")
        print("2) Exit and install pySPLASH by following the instructions here 'https://github.com/berlinguyinca/spectra-hash/tree/master/python' ")

        response = None
        response = input(
            "Do you want to proceed with the slow web API? [Y/n]: ")
        if response == "Y":
            implementation = "webAPI"
            try:
                import requests
            except ImportError:
                raise ImportError("You need to install the 'requests' package to use the web API, do 'pip install requests' ")
        else:
            exit()
        
    return implementation

IMPLEMENTATION = _initSPLASHpackage()
if IMPLEMENTATION == "pySPLASH":
    from splash import Spectrum, SpectrumType, Splash
elif IMPLEMENTATION == "webAPI":
    import requests

def prepare_individual_spectra_for_splashAPI(spectra_dict, mslevel):
    """ This function takes a mzmlripper spectra and returns a dict
        formatted to be sent to https://splash.fiehnlab.ucdavis.edu/splash
        to return a SPLASH 
    """ 
    # This will be returned. See the link above for information on formatting
    spectra_json = {}
    ion_list = []  # This will be put in the spectra_json dict above

    # Get the masses from the ripper dictionary
    masses = spectra_dict["mass_list"]
    
    # Run through the masses to get intensities
    for mass in masses:
        # Get the intensity for this mass
        intensity = spectra_dict[f"{mass:.4f}"]
        # Add a dictionary that maps mass to the mass and intensity to the intensity
        ion_list.append({"mass": mass, "intensity": intensity})
    # Store the list of ion dicts as an element in the json
    spectra_json["ions"] = ion_list
    # Remind the SPLASH that this is MS data 
    spectra_json["type"] = "MS"
    #spectra_json["MS Level"] = mslevel

    # return the formatted data
    return spectra_json

def get_SPLASH_from_restAPI(spectra_json):
    """ This function will send a spectra_json to the SPLASH
        REST API. If the load is successful it will return the
        SPLASH. Otherwise it will raise an error. 
    """
    # Initialize the return
    splash_string = None
    # Make the request (note, we need to use 'post' not 'get'
    #  and we need to pass a json arg, not a params arg)
    response = requests.post(url = SLAPSH_API_URL, json = spectra_json)
    # Check the response code. 200 is success anything else is shit.
    if response.status_code == 200:
        #print('SPLASH!')
        splash_string = response.content.decode()
    else:
        raise Exception(
            "You done goofed!!!! \n The SPLASH API gave a bad response \n Check your json.")

    return splash_string


def prepare_individual_spectra_for_pySPLASH(spectra_dict, mslevel):
    """ This function takes a mzmlripper spectra and returns a list
        formatted to be sent to through the pySPLASH splash functions
        to return a SPLASH
    """
    ion_list = []  # This list will contain tuples of (mass, intensity)
    # Get the masses from the ripper dictionary
    masses = spectra_dict["mass_list"]

    # Run through the masses to get intensities
    for mass in masses:
        # Get the intensity for this mass
        intensity = spectra_dict[f"{mass:.4f}"]
        # Add a dictionary that maps mass to the mass and intensity to the intensity
        ion_list.append((mass, intensity))
    
    # return the formatted data
    return ion_list

def get_SPLASH_from_pySPLASH(ion_list):
    """ This function will generate a SPLASH key using pySPLASH installed in the local env  
    """
    # Initialize the return
    splash_string = None
    spectra= Spectrum(
        ion_list, SpectrumType.MS)
    splash_string = Splash().splash(spectra)
    return splash_string

def APIsplash_all_spectra(ripper_dict):
    """ This function will get a SPLASH for every spectra in a ripper dict
        This might be kind of slow since we're querying an API for all of them
        Consider selecting spectra in a smarter way 

        This returns the ripper dict except that each spectra will now have an associated 'splash' entry
    """

    # Iterate through all the mslevels
    all_mslevels = ripper_dict.keys()
    for mslevel in all_mslevels:
        # Iterate through all the spectra 
        all_spectra = ripper_dict[mslevel].keys()
        for spectra in all_spectra:
            # Grab the spectra
            this_spectra = ripper_dict[mslevel][spectra]
            # Convert that to the right format to SPLASH it
            spectra_json = prepare_individual_spectra_for_splashAPI(
                this_spectra, mslevel)
            # SPLASH it
            splash_string = get_SPLASH_from_restAPI(spectra_json)
            # Assign add this to the rippper dict
            this_spectra["splash"] = splash_string 
            ripper_dict[mslevel][spectra] = this_spectra

    return ripper_dict


def pySPLASH_all_spectra(ripper_dict):
    """ This function will get a SPLASH for every spectra in a ripper dict using pySPLASH
        This returns the ripper dict except that each spectra will now have an associated 'splash' entry
    """

    # Iterate through all the mslevels
    all_mslevels = ripper_dict.keys()
    for mslevel in all_mslevels:
        # Iterate through all the spectra
        all_spectra = ripper_dict[mslevel].keys()
        for spectra in all_spectra:
            # Grab the spectra
            this_spectra = ripper_dict[mslevel][spectra]
            # Convert that to the right format to SPLASH it
            spectra_json = prepare_individual_spectra_for_pySPLASH(
                this_spectra, mslevel)
            # SPLASH it
            splash_string = get_SPLASH_from_pySPLASH(spectra_json)
            # Assign add this to the rippper dict
            this_spectra["splash"] = splash_string
            ripper_dict[mslevel][spectra] = this_spectra

    return ripper_dict

def splash_ripper_dict(ripper_dict):
    """ This function will add a SPLASH to every spectra in a ripper dict 
        It will do this using one of two different methods depending on 
        which dependencies are installed. The webAPI method is glacially slow 
    """
    splashed_dict ={}
    if IMPLEMENTATION == "pySPLASH":
        splashed_dict = pySPLASH_all_spectra(ripper_dict)
    elif IMPLEMENTATION == "webAPI":
        splashed_dict = APIsplash_all_spectra(ripper_dict)
    return splashed_dict
