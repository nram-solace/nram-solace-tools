###########################################################################################
# ConfigParser
#    Solace Config Parser implementation
#
# Ramesh Natarajan (nram@nram.dev)
###########################################################################################

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


Verbose = 0
Cfg = {}

class ConfigParser:
    """ Solace Config Parser implementation """

    def __init__(self, cfg, verbose = 0):
        global Verbose
        global Cfg
        Verbose = verbose
        Cfg = cfg
        if Verbose > 2:
            print ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        self.json_h = JsonHandler.JsonHandler()

    def cfg_parse (self, obj, path, cfg) :
        """ parse cfg recursively """

        if 'links' not in cfg:
            print ("No links to process in cfg")
            return cfg
        links = cfg['links']
        if Verbose > 2:
            print ("Entering {}::{} obj = {} path = {}".format( __class__.__name__, inspect.stack()[0][3], obj, path))

        if Verbose:
            print ('Processing object {} path: {}'. format(obj, path))
            print ('Number of links: {}'. format(len(links)))
        # loop thru link and parse recursively
        if links:
            if Verbose > 2:
                print("cfg_parse: Processing Links {}".format(links))
            if type(links) is list:
                for link in links:
                    self.parse_links ( obj,path, link, cfg)
            else:
                self.parse_links (obj, path, links, cfg)
        return cfg


    def parse_links (self, base_obj, base_path, links, cfg):
        """ parse list of links to broker with corresponding json payload """

        if Verbose > 2:
            print ("Entering {}::{} obj = {} path = {} ".format( __class__.__name__, inspect.stack()[0][3], base_obj, base_path))
        if Verbose > 2:
            print ('Processing Links'); pp.pprint(links)

        for _, link in links.items():
            #op, obj_type = os.path.split(link)
            a = link.split('/')
            obj_type = unquote(a[len(a)-1])
            obj = unquote(a[len(a)-2])
            link = unquote(link)
            #print ('parse_links:Processing object: {} ({}) Link: {}'.format(obj, obj_type, link))

            # base path: ../out/json/localhost/test-vpn
            # link: http://localhost:8080/SEMP/v2/config/msgVpns/test-vpn/aclProfiles/#acl-profile/clientConnectExceptions
            # obj_type: clientConnectExceptions
            # obj: #acl-profile (can also be "test-vpn" in top level see HACK below)

            sys_cfg = Cfg["SysCfg"]
            # TODO: This endsup looking for far too many json files that will never be found
            # some of them leading to invalid path. 
            # fix to prevent that -- need more tighter control.
            if obj in sys_cfg["semp"]['leafNode']:
                if Verbose:
                    print ('Leaf object {}. skip'.format(obj))
                return

            if Verbose:
                print ('Parsing object: {} {}'.format(obj, obj_type))
                print ('link: {} base_bath: {}'.format(link, base_path))

            #if obj in SysCfg['skipObjects']:
            #    print ('   - Skipping object:  {}'.format(obj))
            #    continue
            path="{}/{}".format(base_path, obj_type)

            #json_file = unquote("{}/{}.json".format(path, obj))
            if Verbose > 2:
                print ('<1> Looking for <{}*.json> files in {} obj: {} type: {}'.format(obj_type, path, obj, obj_type))
            try:
                json_files = list(pathlib.Path(path).glob('{}*.json'.format(obj_type)))

                # HACK - try one level below
                if len(json_files) == 0:
                    path="{}/{}/{}".format(base_path, obj, obj_type)
                    if Verbose > 2:
                        print ('<2> Looking for <{}*.json> files in {} obj: {} type: {}'.format(obj_type, path, obj, obj_type))

            # protect agains unparsable path
            except Exception as e:
                print ()
                print ("#################################################################################")
                print ('### Unable to read json files in {}'.format(path))
                print ('### Exception: {}'.format(e))
                print ("#################################################################################")
                return
            
            # files read .. process them
            json_files = list(pathlib.Path(path).glob('{}*.json'.format(obj_type)))

            if Verbose:
                print ('Found {} {}/*.json files in {}'.format (len(json_files), obj_type, path))
            if Verbose > 2:
                print ('List of json files :'); pp.pprint(json_files)
            
            for json_file in sorted(json_files):
                if Verbose:
                    print ('   Reading file {} ({})'.format(json_file, obj))
                this_obj = self.json_h.read_json_data(json_file)

                # add this object to base object
                if Verbose > 2:
                    print('cfg keys: ', cfg.keys())
                    #print ('JSON:'); pp.pprint(cfg)
                if obj_type in cfg:
                    if Verbose:
                        print ('   + Adding {} {} to config'.format(obj, obj_type))
                    #pp.pprint(cfg[obj])
                    for d in this_obj['data']:
                        cfg[obj_type]['data'].append(d)
                    #for l in this_obj['links']:
                    #    cfg[obj_type]['links'].append(l)
                else:
                    if Verbose:
                        print ('   > Creating {} {} in config'.format(obj, obj_type))
                    cfg[obj_type] = this_obj

                if Verbose > 2:
                    print('... This object'); pp.pprint(this_obj)
                    #print('--- cfg: '); pp.pprint(cfg)

                if len(this_obj['data']) == 0 and len(this_obj['links']) == 0:
                    if Verbose:
                        print ('No data or links in {}'.format(json_file))
                    continue
                self.cfg_parse (base_obj, path, this_obj)
            #else:
            #    log.info("No JSON file %s", json_file)