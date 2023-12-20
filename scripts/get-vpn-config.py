# get-vpn-config.py 
#
# Traverse Solace Message VPN configs with SEMPv2 REST post recursively
# Store output JSONs in a dir tree
# Usage:
#   python3 get-vpn-config.py --config config/sample-config-local.yaml [-v]
# 
# Ramesh Natarajan (nram), Solace PSG
# nram@nram.dev

import sys, os
import argparse
import pprint
import json
import requests
import inspect
import shutil
import urllib
import pathlib
from requests.auth import HTTPBasicAuth
from zipfile import ZipFile
# from os.path import basename
from datetime import datetime
from urllib.parse import unquote # for Python 3.7

sys.path.insert(0, os.path.abspath("."))
from common import JsonHandler
from common import ConfigParser
from common import SempHandler
from common import YamlHandler

    
me = "get-vpn-config"
ver = '2.0.0'

# Globals
Cfg = {}    # global handy config dict
Verbose = 0  
pp = pprint.PrettyPrinter(indent=4)

json_h = JsonHandler.JsonHandler()
yaml_h = YamlHandler.YamlHandler()

def main(argv):
    """ program entry drop point """
    global Cfg, Verbose

    p = argparse.ArgumentParser()
    p.add_argument('--config', dest="config_file", required=True, help='config json file') 
    p.add_argument( '--verbose', '-v', action="count",  required=False, default=0,
                help='Verbose output. use -vvv for tracing')
    r = p.parse_args()

    print ('\n{}-{} Starting\n'.format(me,ver))

    Verbose = r.verbose


    print ("Reading user config file  : {}".format(r.config_file))
    Cfg = yaml_h.read_config_file(r.config_file)
    if Verbose > 2:
        print ('CONFIG', json.dumps(Cfg, indent=4))

    sys_cfg_file = Cfg["internal"]["systemConfig"]
    print ("Reading system config file: {}".format(sys_cfg_file))

    system_config_all = yaml_h.read_config_file (sys_cfg_file)
    if Verbose > 2:
        print ('SYSTEM CONFIG'); pp.pprint (system_config_all)

    Cfg['system'] = system_config_all.copy() # store system cfg in the global Cfg dict

    cfg_p = ConfigParser.ConfigParser(Cfg)

    for vpn_name in Cfg["vpn"]["msgVpnNames"]:
        print ("\nGet VPN Config for {}".format(vpn_name))
        vpn_json_file = get_vpn_data(vpn_name)

        vpn_json_data = json_h.read_json_file (vpn_json_file)
        if 'data' not in vpn_json_data:
            print ('**** No data element. Skipping invalid json file: {} ****'.format(vpn_json_file))
            continue

        # get vpn data first
        print ('Parse VPN JSON Configs for {} ({})'. format(vpn_name, vpn_json_file))
        vpn_json_data = json_h.read_json_data (vpn_json_file)

        vpn_cfg = cfg_p.cfg_parse(vpn_name, os.path.dirname(vpn_json_file), vpn_json_data)

        # save cfg to file
        print ('Save VPN all config json')
        vpn_allcfg_out_file = "{}/{}-all.json". format(os.path.dirname(vpn_json_file), vpn_name)
        json_h.save_json_file(vpn_allcfg_out_file, vpn_cfg)

    print ('\n{} Done\n'.format(me))


def get_vpn_data(vpn):
    """ process vpn recursively """
    if Verbose > 2:
         print ('Entering {}::{} vpn = {}'.format(__name__, inspect.stack()[0][3], vpn))

    rtr_cfg = Cfg["router"]
    sys_cfg = Cfg["system"]
    if Verbose > 2:
        print ('--- ROUTER :\n', json.dumps(rtr_cfg))
        print ('--- SYSCFG :\n', json.dumps(sys_cfg))

    url = "{}/{}/{}".format(rtr_cfg["sempUrl"], sys_cfg["semp"]["vpnConfigUrl"], vpn)
    out_dir = "{}/{}/{}".format(sys_cfg["system"]["outputDir"], rtr_cfg["label"], vpn)

    semp_h = SempHandler.SempHandler(Cfg, vpn, out_dir)
    vpn_data = semp_h.get_vpn_config_json (url)
    if Verbose > 2:
        print ('VPN ', pp.pprint(vpn_data))

    if Verbose:
        print ("Output dir: {}".format(out_dir))
    outfile = '{}/vpn.json'.format(out_dir)
    json_h.save_config_json(outfile, vpn_data)

    # start from vpn links and traverse recursivey from there
    semp_h.process_page_links(vpn_data)

    return outfile



if __name__ == "__main__":
    """ program entry point - must be  below main() """

    main(sys.argv[1:])
