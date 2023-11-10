# create-queues.py
#
# This program creates new or update existing queues on a Solace PubSub+ broker using SEMPv2
# While updating, exisitng Queue will be temporarliy disabled, updated and enabled.
# All config and inputs are read from files for batch processing
#
# Requirements:
#  Python 3
#  Modules: pandas, json, yaml
#
# Required input files:
# Config Yaml file:
#   This file has Solace PubSub+ broker access info, default values for queues, etc.
#   See config/sample-config.yaml
# Input CSV file:
#   This file has list of queue names and properties that should be overwritten.
#   See input/sample-queues.csv
#   Properties will  be taken from the input CSV file if present 
#   Otherwise, default values from config file will be used
#   Otherwise, Solace default values will be used
#
# Running:
# Create queues:
#   python3 create-queues.py --config config/nram-local-config.yaml  --input input/nram-test-queues.csv
# Create new or update existing queues: Use --patch option
#   python3 create-queues.py --config private/nram/nram-dev1.yaml  --input private/abc/abc-queues-tests1.csv --patch 
#
# Ramesh Nataraajan (nram@nram.dev)
# Solace PSG

import sys, os
import argparse
import json, yaml
import pandas as pd
import pprint
from urllib.parse import unquote, quote

sys.path.insert(0, os.path.abspath("."))
from common import SempHandler
from common import JsonHandler
from common import QueueConfig 

pp = pprint.PrettyPrinter(indent=4)

me = "create-queues"
ver = '1.2'

# Globals
Verbose = 0
# Define the minimum required Python version
MIN_PYTHON_VERSION = (3, 6)


#--------------------------------------------------------------------
# read_config_yaml_file
# Read config yaml file and return config dict
#--------------------------------------------------------------------
def read_config_yaml_file(config_yaml_file):
    global Verbose

    print ('Reading config file: ', config_yaml_file)
    with open (config_yaml_file) as cfg:
        cfg = yaml.safe_load(cfg)

    
    if Verbose > 2:
        print ('USER CONFIG')
        print (json.dumps(cfg, indent=2))

    return cfg

#--------------------------------------------------------------------
# read_input_csv_file
# Read input csv file and return as pandas dataframe
#--------------------------------------------------------------------
def read_input_csv_file (input_csv_file):
    print ('Reading input file: ', input_csv_file)
    df = pd.read_csv(input_csv_file)
    # Strip leading and trailing spaces from column names
    df.rename(columns=lambda x: x.strip(), inplace=True)
    return df



def main(argv):
    """ program entry drop point """

    # parse command line arguments
    p = argparse.ArgumentParser()
    p.add_argument('--config', dest="config_file", required=True, 
                   help='system and profile config yaml file') 
    p.add_argument('--input', dest="input_file", required=True, 
                   help='user input csv file') 
    p.add_argument('--patch', dest="patch_it", action='store_true', required=False, default=False, 
                   help='user input csv file') 
    p.add_argument( '--verbose', '-v', action="count",  required=False, default=0,
                help='Verbose output. use -vvv for tracing')
    r = p.parse_args()

    print ('\n{}-{} Starting\n'.format(me,ver))

    Verbose = r.verbose

    # read config and input files
    cfg = read_config_yaml_file(r.config_file)
    input_df = read_input_csv_file(r.input_file)

    # create semp handler -- see common/SimpleSempHandler.py
    semp_h = SempHandler.SimpleSempHandler(cfg, Verbose)

    queues = QueueConfig.Queues(semp_h, cfg, input_df, Verbose)

    # create / update queues
    queues.create_or_update_queue   ( r.patch_it)
    queues.create_or_update_dmqueue ( r.patch_it)

# Program entry point
if __name__ == "__main__":
    """ program entry point - must be  below main() """
    # Check if the current Python version meets the requirement
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"This script requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or later.")
        print(f"Your Python version is {sys.version_info.major}.{sys.version_info.minor}.")
        sys.exit(1)  # Exit the script with a non-zero status code

    main(sys.argv[1:])