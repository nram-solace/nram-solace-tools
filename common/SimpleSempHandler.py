
##############################################################################
# SimpleSempHandler
#   Simmplified SEMPv2 protocol handler
#   Supports GET, POST, PATCH, PUT, DELETE
#   This has no paging support
#
# Ramesh Natarajan (nram@nram.dev)
# Solace PSG
##############################################################################

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

pp = pprint.PrettyPrinter(indent=4)

class SimpleSempHandler:
    """ Solace SEMPv2 Parser implementation """
    Verbose = 0
    Cfg = {}
    
    def __init__(self, cfg, verbose):
        global Verbose, Cfg
        Verbose = verbose
        Cfg = cfg


    #-------------------------------------------------------------  
    # http_get
    #  
    def http_get(self, url, params=None):
        if Verbose > 2:
            print ("Entering {}:{} url: {} params: {}".format( __class__.__name__, inspect.stack()[0][3], url, params))

        verb = 'get'
        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        hdrs = {"content-type": "application/json"}
        auth = HTTPBasicAuth(semp_user, semp_pass)
        if params:
            resp = getattr(requests, verb)(url, 
                headers=hdrs,
                auth=auth,
                params=params,
                data=None)
        else:
            resp = getattr(requests, verb)(url, 
                headers=hdrs,
                auth=auth,
                data=None)
        if Verbose > 2:
            print ('http_get returned: {}'.format(resp))

        return resp

    #-------------------------------------------------------------  
    # http_post
    #
    def http_post(self, url, json_data):
        if Verbose > 2:
            print ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        if Verbose > 2:
            print ('posting json-data:\n', json.dumps(json_data, indent=4, sort_keys=True))
        verb = 'post'
        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        resp = getattr(requests, verb)(url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass),
            data=(json.dumps(json_data) if json_data != None else None))
        if Verbose > 2:
            print ('http_post resp : {}'.format(resp))
            print ("     resp text :"); pp.pprint (json.loads(resp.text))
        json_resp = json.loads(resp.text)

        if json_resp['meta']['responseCode'] == 200:
            if Verbose:
                print (' http_post returned ', json_resp['meta']['responseCode'])
            return "OK"          
        else:
            print ("         http_post retunred {} ({})".format(json_resp['meta']['responseCode'],
                                            json_resp['meta']['error']['status']))
            if Verbose:
                print (json_resp['meta']['error']['description'])
            return json_resp['meta']['error']['status']

        #return resp
    
    #-------------------------------------------------------------  
    # http_patch
    #
    def http_patch (self, url, json_data):
        if Verbose > 2:
            print ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        if Verbose > 2:
            print ('patching json-data:\n', json.dumps(json_data, indent=4, sort_keys=True))
        verb = 'patch'
        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        resp = getattr(requests, verb)(url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass),
            data=(json.dumps(json_data) if json_data != None else None))
        if Verbose > 2:
            print ('http_patch resp : {}'.format(resp))
            print ("     resp text :"); pp.pprint (json.loads(resp.text))
        json_resp = json.loads(resp.text)

        if json_resp['meta']['responseCode'] == 200:
            if Verbose:
                print (' http_patch returned ', json_resp['meta']['responseCode'])            
        else:
            print ("         http_patch retunred {} ({}) : {}".format(json_resp['meta']['responseCode'],
                                                          json_resp['meta']['error']['status'],
                                                          json_resp['meta']['error']['description']))

        return resp
    
    #-------------------------------------------------------------  
    # http_put
    #
    def http_put(self, url, json_data):
        if Verbose > 2:
            print ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        if Verbose > 2:
            print ('posting json-data:\n', json.dumps(json_data, indent=4, sort_keys=True))
        verb = 'put'
        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        resp = getattr(requests, verb)(url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass),
            data=(json.dumps(json_data) if json_data != None else None))
        if Verbose > 2:
            print ('http_put returning : {}'.format(resp))
        return resp
    
    #-------------------------------------------------------------  
    # http_delete
    #
    def http_delete (self, url):
        if Verbose > 2:
            print ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        ignore_status = ['INVALID_PATH']


        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        
        if Verbose:
            print("   DELETE URL {} ({})".format(unquote(url), semp_user))
   
        resp = requests.delete(url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass),
            data=(None),
            verify=False)
        if Verbose:
            print ('http_delete returning : {}'.format(resp))
        if Verbose > 2:
            print('Response:\n%s',resp.json())
        if (resp.status_code != 200):
            print ('Non-200 Response text: {}'.format(resp.text))
            status = resp.json()['meta']['error']['status']
            desc = resp.json()['meta']['error']['description']

            if status in ignore_status:
                print (f'Ignoring non success status {status}')
        return resp