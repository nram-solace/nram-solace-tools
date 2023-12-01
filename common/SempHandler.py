
##############################################################################
# SempHandler
#   Simmplified SEMPv2 protocol handler
#   Supports GET, POST, PATCH, PUT, DELETE
#   This has no paging support
#
# Ramesh Natarajan (nram@nram.dev)
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

sys.path.insert(0, os.path.abspath("."))
from common import JsonHandler

pp = pprint.PrettyPrinter(indent=4)
Verbose = 0
Cfg = {}
json_h = JsonHandler.JsonHandler()


class SempHandler:
    """ Solace SEMPv2 Parser implementation """
    
    def __init__(self, cfg, vpn="default", outdir = "output/default", verbose = 0):
        global Verbose, Cfg
        Verbose = verbose
        Cfg = cfg
        self.vpn = vpn
        self.out_dir = outdir


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
                data=None,
                verify=False)
        else:
            resp = getattr(requests, verb)(url, 
                headers=hdrs,
                auth=auth,
                data=None,
                verify=False)
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
            data=(json.dumps(json_data) if json_data != None else None),
            verify=False)
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
            data=(json.dumps(json_data) if json_data != None else None),
            verify=False)
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
            data=(json.dumps(json_data) if json_data != None else None),
            verify=False)
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
    
    #-------------------------------------------------------------
    # Higer order functions for get
    #-------------------------------------------------------------

    def get_vpn_config_json (self, url):
        """ get vpn config json """
        return self.get_config_json(url)

    def get_config_json (self, url, collections=False, paging=True):
        """ get vpn object config json """
        if Verbose > 2:
            print ('Entering {}::{} url = {}'.format(__class__.__name__, inspect.stack()[0][3], url))
        verb='get'

        sys_cfg = Cfg['SysCfg']
        page_size = sys_cfg["semp"]["pageSize"]
        no_paging = sys_cfg["semp"]["noPaging"]

        u_url = unquote(url)
        if collections:
            if int(page_size) == 0:
                paging = False
            # some elements throw 400 not supported if page count is sent
            if os.path.split(url)[1] in no_paging:
                paging = False
                if Verbose:
                    print ("Skipping paging for element {}".format(os.path.split(u_url)[1]))
            if paging :
                if Verbose:
                    print("   Get URL {} [{}] (*)".format(u_url, page_size))
                params = {'count':page_size}
                resp = self.http_get(url, params)
            else:
                if Verbose:
                    print ("   Get URL {} (*)".format(u_url))
                resp = self.http_get(url)
        else:
            # No paging for non-collection objects
            if Verbose:
                print("   Get URL {}".format(u_url))
            resp = self.http_get(url) 

        if Verbose > 2:
            print("Get: req.json()")
            pp.pprint(resp.json())
        if (resp.status_code != 200):
            print(f'**** Get URL {u_url} failed ****')
            if Verbose:
                print(resp.text)
            return resp.json()

            #raise RuntimeError
        else:
            return resp.json()

    def process_page_links (self, json_data):
        """ given json data, traverse thur all links in meta section 
            calls itself recursively  
        """
        if Verbose > 2:
            print ("Entering {}::{}".format( __class__.__name__, inspect.stack()[0][3]))
        if Verbose > 2:
            pp.pprint (json_data)

        if 'links' not in json_data:
            if Verbose:
                print ("No Links")
            return

        if type(json_data['links']) is list:
            for link_list in json_data['links']:
                link_keys = list(link_list.keys())
                #print ("   got {:d} link-lists: {:s}". format(len(lkeys), lkeys))
                if 'uri' in link_keys:
                    link_keys.remove('uri') 
                if len(link_keys) == 0 :
                    if Verbose > 2:
                        print ("No non-uri links in list")
                    return       
                #print ("   processing {:d} links: {:s}".format(len(lkeys), lkeys))
                for l in link_keys:
                    lurl = link_list[l]
                    link_data = self.get_link_data (lurl, True)
                    self.process_page_links(link_data)
        else:
            link_keys = list(json_data['links'].keys())
            #print ("   got {:d} links: {:s}". format(len(lkeys), lkeys))
            if 'uri' in link_keys:
                link_keys.remove('uri') 
            if len(link_keys) == 0 :
                if Verbose > 2:
                    print ("No non-uri links in non-list")
                return       
            #print ("   processing {:d} links: {:s}".format(len(lkeys), lkeys))
            for link_key in link_keys:
                link_url = json_data['links'][link_key]
                link_data = self.get_link_data (link_url, True)
                self.process_page_links (link_data)

    def get_link_data (self, url, collection, paging=True, follow_links=True):
        """ process one link url, calls get_config_json() & save_config_json """

        if Verbose > 2:
            print ("Entering {}::{} url = {}, collection = {}, links = {}".format( __class__.__name__, inspect.stack()[0][3], url, collection, follow_links))
        #ph,obj = os.path.split(url)

        #path=url[url.find('/msgVpns/')+8:]
        #if path.rfind('?')>0:
        #    path=path[:path.rfind('?')]
        #_,obj = os.path.split(path)
        #path=urllib.parse.unquote(path)

        p = url.partition(self.vpn)
        path=p[2]
        if path.rfind('?')>0:
            path=path[:path.rfind('?')]
        _,obj = os.path.split(path)
        #print (f'p: {p}')
        #print (f'old url: {url} path: {path} obj: {obj}')

        if Verbose > 1:
            print ("Processing link {}".format(url))  
        json_data = self.get_config_json (url, collection, paging)

        # Write data to file
        fname = json_h.get_unique_fname(path, obj)
        if Verbose > 2:
            print ('fname: {} path: {} outdir: {}'.format(fname, path, self.out_dir))
        outfile = '{}/{}/{}'.format(self.out_dir,path,fname)

        if Verbose > 1:
            print ("Save json to file: {}".format (outfile))
        json_h.save_config_json (outfile, json_data )

        # Process meta - look for cursor/paging
        meta_data = json_data['meta']
        if 'paging' in meta_data:
            if Verbose > 2:
                print  ("paging : {}".format(meta_data['paging']))
            next_page_uri = meta_data['paging']['nextPageUri']
            if Verbose > 1:
                print ("Processig Next Page URI : %s", unquote(next_page_uri))
            # process nextPageUri - recursively
            next_page_data = self.get_link_data (next_page_uri, False, False, follow_links) # don't use collection for nextPage
                                                                        # don't add page count either. Its part of nextPage URL already
            # for next-page-uri, call parent process_page_links() *** deep recursion ***
            self.process_page_links (next_page_data)
            #why wouldn't you follow links ???
            #if follow_links:
            #    if Verbose > 1:
            #        print ('following links')
            #    self.process_page_links (json_data)
            #else:
            #    print ('follow-links is off. Not following the link')
        else:
            if Verbose > 1 :
                print ('No paging in meta-data')
        return json_data