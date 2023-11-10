##############################################################################
# YamlHalder.py
#   Common class for YAML Handling functions
#
# Ramesh Natarajan (nram@nram.dev)
##############################################################################

import sys, os
import yaml
import json
import pprint
import inspect
#import pathlib

pp = pprint.PrettyPrinter(indent=4)
Verbose = 0
class YamlHandler():
    """ YAML handling functions """

    def __init__(self, verbose=0):
        global Verbose
        Verbose = verbose
        if Verbose > 2:
                print ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))

    #--------------------------------------------------------------------
    # read_config_yaml_file
    # Read config yaml file and return config dict
    #--------------------------------------------------------------------
    def read_config_file(self, config_yaml_file):
        if Verbose:
            print ('Reading config file: ', config_yaml_file)
        with open (config_yaml_file) as cfg:
            cfg = yaml.safe_load(cfg)

        
        if Verbose > 2:
            print ('USER CONFIG')
            print (json.dumps(cfg, indent=2))

        return cfg