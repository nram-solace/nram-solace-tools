#/usr/bin/python3
#
# apply-vpn-config
# ---------------------------------------------------------------------
#   create vpn from json config files 
#   The script takes a vpn config directory created from get-vpn-config as input
#       and creates a vpn on the target router
#  The script can also be used to patch (modify) an existing vpn. 
#       Patch is experimental and not fully tested
#       Patch must pass list of items to patch (eg: queues, aclProfiles, clientProfiles etc)
#  The script can NOT be used to delete an existing vpn 
#
#  The script is designed to be idempotent.
#  It can be run multiple times on the same vpn config directory
#  It will create the vpn and objects if it does not exist
#  In patch mode, it will modify the vpn and objects if they exist
#
# The script can be run in 2 modes
#   - post (default) : create vpn and all objects
#   - patch : modify vpn and objects
#
# The script is tested against the following:
#   - Solace PubSub+ Docker 10.0, 9.12
#   - Solace PubSub+ Cloud 10.0 
#   - Python 3.7.6
#
# ---------------------------------------------------------------------
# Ramesh Natarajan (nram), Solace PSG
# nram@nram.dev

import sys, os
import argparse
import pprint
import json
import requests
import inspect
import urllib
import pathlib


from urllib.parse import unquote
# supress InsecureRequestWarning
#urllib.disable_warnings()
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


me = "create-vpn"
ver = "1.1.0"

# Globals 
SysCfg = {} # system / internal cfg
TargetVpnName = ''
Cfg = {}    # conifg dict read from user input
Verbose = 0  
pp = pprint.PrettyPrinter(indent=4)
Patching = False # patching (modify) or post (create), default is post (create)
Deleting = False
Operation = "Creating"
Items = [] # items to post / patch. Eg: "aclProfile,clientProfile"
           # this is required for patch 
           # optional for post. If missing whole vpn is created. 


#--------------------------------------------------------------------
# Main
#
class Main :

    def __init__(self, argv):
        if Verbose :
            print ('Entering {}::{} argv: {}'.format(__class__.__name__, inspect.stack()[0][3], argv))
        #self.argv = argv
        self.vpn_delta = {} # this is where all vpn diffs go
        self.main()

    def main(self):        
        global Cfg, SysCfg, VerCfg 
        global Verbose
        global TargetVpnName

        global Patching, Deleting, Items

        p = argparse.ArgumentParser()
        p.add_argument('-c', '--configfile', dest="config_file", required=True, help='config json file') 
        p.add_argument('-s', '--srcdatadir', dest="src_data_dir", required=True, help='Source VPN data dir (for post and patch)') 
        #p.add_argument('-f', '--srcdatafile', dest="src_data_file", required=True, help='Source VPN data file (for delete)') 

        p.add_argument('-t', '--targetvpn', dest="target_vpn", required=True, help='Target VPN name') 
        p.add_argument('--patch', dest="patching", required=False, action='store_true', help='Patch (modify) existing vpn objects')
        p.add_argument('--delete', dest="deleting", required=False, action='store_true', help='Delete existing vpn objects')

        p.add_argument('--items', dest="items", required=False,
                       help='Comma separated list of items to post / patch. Eg: "aclProfile,clientProfile"')
        p.add_argument( '--verbose', '-v', action="count",  required=False, default=0,
                    help='Turn Verbose. Use -vvv to be very verbose')
        r = p.parse_args()

        if (r.patching):
            Patching = True
            Operation = "Patching"
        if (r.deleting):
            #if not r.src_data_file:
            #    print ('Delete requires src data file. Exiting')
            #    exit(1)
            Deleting = True
            Operation = "Deleting"
        if Patching and Deleting:
            print ('Patching and Deleting are mutually exclusive. Exiting')
            exit(1)

        if (r.items):
            Items = r.items.split(',')

        print ('\n{}-{} Starting\n'.format(me,ver))
        Verbose = r.verbose

        # 
        # reading config files
        #
        print ("Reading user config {}".format(r.config_file))
        json_h = JsonHandler()
        Cfg = json_h.read_json_file(r.config_file)

        if Verbose > 2:
            print ('CONFIG'); pp.pprint (Cfg)

        # Read  system config files
        syscfg_file = Cfg["internal"]["systemConfig"]
        print ("\nReading system config: {}".format(syscfg_file))
        system_config_all = json_h.read_json_file (syscfg_file)
        if Verbose > 2:
            print ('\nSYSTEM CONFIG'); pp.pprint (system_config_all)
        SysCfg = system_config_all # system_config_all["system"]


        #--------------------------------------------------------------------
        # read vpn json configs
        #
        vpn_json_file = "{}/vpn.json". format(r.src_data_dir)
        print ("\nReading VPN config: {}".format(vpn_json_file))
        json_data, links, next_page_uri = json_h.read_json_data (vpn_json_file)
        src_vpn_name = json_data['msgVpnName']
        if Verbose:
            print (f'Read config for VPN {src_vpn_name}')

        TargetVpnName = r.target_vpn 
        
        print ('Creating VPN {}'.format(TargetVpnName))
        url="{}/{}".format(Cfg["router"]["sempUrl"],SysCfg["semp"]["vpnConfigUrl"])


        # Intializie semp handler and call it with vpn data
        #  this will recursively call itself for child objects and links
        semp_p = SempParser(json_h)
        semp_p.semp_apply(url, TargetVpnName, r.src_data_dir, json_data, links, next_page_uri)

        print ('\n ### {} objects for VPN {} successfully complete on {}.\n'.format(Operation, TargetVpnName, Cfg["router"]["sempUrl"]))

#-----------------------------------------------------------------------
# Object to convert custom json to python object
# Used in returning prematurely from semp_apply
# This mimics the json object structure in HTTP response
class RespObject:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, dict):
                setattr(self, key, RespObject(**value))
            else:
                setattr(self, key, value)

#--------------------------------------------------------------------------
# SEMP Parser implementation
#
class SempParser:
    """ Solace SEMPv2 Parser implementation """

    def __init__(self, _json_h):
        if Verbose :
            print ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        self.json_h = _json_h

    #--------------------------------------------------------------------
    # semp_apply
    #   process semp post from top level (vpn.json)
    #   and calls itself recursively for child objects and links
    #
    def semp_apply (self, url, obj, path, json_data=None, links=None, next_page_uri=None) :
        """ post semp to broker - mostly calls other helper functions """

        if Verbose :
            print ("{}::{} url = {} obj = {} path = {}".format( __class__.__name__, inspect.stack()[0][3], url, obj, path))

        if type(json_data) is list:
            if Verbose > 2:
                print ('json_data is list')
            for json_data_e in json_data:
                resp = self.apply_json(url, json_data_e)
                if Verbose > 2:
                    print('semp_apply: list post returned {}'.format(resp.status_code))
                if (not (resp.status_code == 200 or resp.status_code == 100 )):
                    rs, rd = self.response_status(resp)                    
                    if rs in SysCfg['status']['statusOk'] :
                        print ('   * {} (ignored)'.format(rd,rd))
                    else :
                        print ('   *** ERROR {} ({}) ** exiting **'.format(rd,rs))
                        raise RuntimeError
        else:
            if Verbose > 2:
                print('semp_apply: json_data is obj')
            resp = self.apply_json(url, json_data)
            if Verbose > 2:
                print ('resp: ({}) {}'.format(type(resp), resp))
                print('semp_apply: obj post returned {}'.format(resp.status_code))
            if (not (resp.status_code == 200 or resp.status_code == 100 )):
                    rs, rd = self.response_status(resp)                    
                    if rs in SysCfg['status']['statusOk'] :
                        print ('   * {} (ignored)'.format(rd,rd))
                    else :
                        print ('   *** ERROR {} ({}) ** exiting **'.format(rd,rs))
                        raise RuntimeError

        # We are done posting with json_data
        # loop thru link and Post recursively
        if links:
            if Verbose > 2:
                print("semp_apply: Processing Links {}".format(links))
            if type(links) is list:
                for link in links:
                    self.apply_links (url, obj,path, link)
            else:
                self.apply_links (url, obj, path, links)

        if Verbose > 2:
            print ('semp_apply: response {} ({}): '.format (resp, type(resp)))
            #print ('semp_apply: response json: ', resp.json())
        return resp

    #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # apply_json:
    #   post / patch to semp url - uses http_post / http_patch below
    #
    def apply_json (self, url, json_data):
        """ just do it """

        if Verbose :
            print ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))

        # check if object needs to be skipped
        _,obj1 = os.path.split(url)
        if obj1 in SysCfg['skipObjects']:
            print ('   - Skipping object:  {} - User skipped'.format(obj1))
            resp = requests.models.Response()
            resp.status_code = SysCfg['status']['statusSkip']   
            return resp
        
        # check if obj should be ignored
        my_keys = set(json_data.keys())
        ignore_keys = SysCfg['skipTags'].keys()
        s = my_keys.intersection(ignore_keys)
        # debug
        #print ('my_keys = ', my_keys)
        #print ('ignore_keys = ', ignore_keys)
        #print ('s = ', s)

        if (len(s) > 0):
            t = s.pop()
            v = json_data[t]
            if v in SysCfg ['skipTags'][t] :
                print ('   - Skipping {} : {}'.format(t,v))
                resp = requests.models.Response()
                resp.status_code = SysCfg['status']['statusSkip']   
                #rs = f'{t} : {v} being skipped. See ignore_list'
                #resp.text =  rs # can't set text
                #print ('skip returning :', resp)
                return resp
            print ('   + Processing {} : {}'.format(t,v))


        # update vpn-name if different
        if json_data['msgVpnName'] != TargetVpnName :
            src_vpn = json_data['msgVpnName']
            if Verbose:
                print ('Target VPN Name {} differs from {}'.format(TargetVpnName,src_vpn))
            ps = '/{}/'.format(src_vpn)
            p = url.partition(ps)
            if Verbose > 2: 
                print ('url: ', url)
                print ('ps : ', ps)                
                print ('p  : ', p)

            if p[1] == ps:
                url = '{}/{}/{}'.format(p[0],TargetVpnName,p[2])
                print ('Target url (1): {}'.format(url))
            json_data['msgVpnName'] = TargetVpnName

            #print ('------------ JSON to post ----------------'); pp.pprint(json_data)
            #_,urlp = os.path.split(url)
            #print ('URL ', url, urlp)

        # Handle deletion
        if Deleting:
            # patch needs object name (eg: queueus/queue1)
            _,vpn_obj = os.path.split(url)
            if vpn_obj in Items:
                patch_url = '{}/{}'.format(url, v)
                if Verbose:
                    print ('Deletion for {}, URL: {}'.format(vpn_obj, patch_url))
                return self.http_delete(patch_url)
            else:
                print ('Deletion not enabled for {}'.format(vpn_obj))
                if vpn_obj in SysCfg['skipObjects']:
                    print ('   - Skipping object:  {} - Not enabled for Patch'.format(vpn_obj))
                    resp = SysCfg['status']['123']
                    return RespObject (**resp)
                    #return SysCfg['status']['123']
                    #return json.dumps(SysCfg['status']['123'], indent=4, sort_keys=True)

        # Check if patching instead of post
        if Patching:
            # patch needs object name (eg: queueus/queue1)
            _,vpn_obj = os.path.split(url)
            if vpn_obj in Items:
                patch_url = '{}/{}'.format(url, v)
                if Verbose:
                    print ('Patching for {}, URL: {}'.format(vpn_obj, patch_url))
                return self.http_patch(patch_url, json_data)
            else:
                print ('Patching not enabled for {}'.format(vpn_obj))
                if vpn_obj in SysCfg['skipObjects']:
                    print ('   - Skipping object:  {} - Not enabled for Patch'.format(vpn_obj))
                    resp = SysCfg['status']['123']
                    return RespObject (**resp)
                    #return SysCfg['status']['123']
                    #return json.dumps(SysCfg['status']['123'], indent=4, sort_keys=True)

        # Check if posting subset of items
        if Items:
            # check if object is in Items list
            _,vpn_obj = os.path.split(url)
            if vpn_obj in Items:
                if Verbose:
                    print ('Posting for {}, URL: {}'.format(vpn_obj, url))
                return self.http_post(url, json_data)
            else:
                print ('   - Skipping object:  {} - Not included in user arg'.format(vpn_obj))
                resp = SysCfg['status']['123']
                return RespObject (**resp)
        else:
            # process whole VPN
            if Verbose:
                print ('Posting all objects, URL: {}'.format(url))
            return self.http_post (url, json_data)
            #return self.http_post_or_patch (url, json_data)

    #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # http_post_or_patch
    #  post / patch to semp url - uses http_post / http_patch below
    #  Status: NOT COMPLETE. NOT USE
    def http_post_or_patch (self, url, json_data):
        # get object name (eg: queueus/queue1)
        _,vpn_obj = os.path.split(url)
        # special treatment for msgVpn object. add vpn name to url
        if vpn_obj == 'msgVpns':
            url = '{}/{}'.format(url, TargetVpnName)
        if Verbose:
            print ('http_post_or_patch: vpn_obj = {}'.format(vpn_obj))
        resp = self.http_get(url)
        print ('http_post_or_patch: get_r = {}'.format(resp))
        if resp.status_code == 200:
            # object exists, patch it
            if Verbose:
                print ('http_post_or_patch: patching object {}'.format(vpn_obj))
            return self.http_patch(url, json_data)
        else:
            # object does not exist, post it
            if Verbose:
                print ('http_post_or_patch: posting object {}'.format(vpn_obj))
            return self.http_post(url, json_data)

    #-------------------------------------------------------------  
    # http_get
    #
    def http_get(self, url):
        if Verbose :
            print ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        if Verbose > 2:
            print (f'get url: {url}')
        verb = 'get'
        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        resp = requests.get (url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass))
        if Verbose:
            print ('http_get returning : {}'.format(resp))
        return resp

    #-------------------------------------------------------------  
    # http_post
    #
    def http_post(self, url, json_data):
        if Verbose :
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
        if Verbose:
            print ('http_post returning : {}'.format(resp))
        return resp
    
    #-------------------------------------------------------------
    # http_patch
    #
    def http_patch (self, url, json_data):
        if Verbose :
            print ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        if Verbose > 2:
            print ('posting json-data:\n', json.dumps(json_data, indent=4, sort_keys=True))
        ignore_status = ['INVALID_PATH']


        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        
        if Verbose:
            print("   PATCH URL {} ({})".format(unquote(url), semp_user))
   
        resp = requests.patch(url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass),
            data=(json.dumps(json_data) if json_data != None else None),
            verify=False)
        if Verbose:
            print ('http_patch returning : {}'.format(resp))
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
    # http_delete
    #
    def http_delete (self, url):
        if Verbose :
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
    

    #------------------------------------------------------------
    # apply_links
    #   This calls semp_apply (recursively) for each link in the list
    #
    def apply_links (self, target_url, target_obj, src_path,links):
        """ post list of links to broker with corresponding json payload """

        if Verbose:
            print ("Entering {}::{}".format( __class__.__name__, inspect.stack()[0][3]))

        # target_url: http://localhost:8080/SEMP/v2/config/msgVpns/<target-vpn>/aclProfiles
        # target_obj: <target-object-name> 
        # src_path: ../out/json/localhost/<src-vpn>/aclProfiles
        if Verbose > 2:
            print (f" target_url: {target_url}\n target_obj: {target_obj}\n src_path: {src_path}")
            print ('LINKS:'); pp.pprint(links)

        json_h = JsonHandler()

        # links: http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/queues
        # http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/queues/sys-q1 
        # http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/aclProfiles/sys-acl1/clientConnectExceptions
        for _, src_link in links.items():
            if Verbose:
                print ('src link: {}'.format(src_link))
            # src_url_path: http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/, obj = queues
            # or  http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/aclProfiles/sys-acl1/ & clientConnectExceptions
            src_link_tails1,obj1 = os.path.split(src_link)
            if Verbose > 2:
                print (f'src_url_path: {src_link_tails1} src_obj: {obj1}')
            if obj1 in SysCfg['skipObjects']:
                print ('   - Skipping object:  {} - User skipped'.format(obj1))
                continue
            path="{}/{}".format(src_path, obj1)
            if Verbose > 2:
                print (f'looking for {path}/*.json (1)')

            #json_file = unquote("{}/{}.json".format(path, obj))
            url = "{}/{}/{}".format(target_url,target_obj,obj1)
            json_files = json_h.list_json_files (path, obj1) 
            
            # look for link-2 format 'http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/aclProfiles/sys-acl1/clientConnectException 
            if len(json_files) == 0 :
                if Verbose:
                    print (f"No {obj1} JSON files found in {path}. Try another level")
                # src_obj2 : sys-acl1
                src_link_tails2,obj2 = os.path.split(src_link_tails1)
                path="{}/{}/{}".format(src_path, obj2, obj1)
                json_files = json_h.list_json_files (path, obj1)
                print (f'looking for path: {path} obj1: {obj1}')

                if len(json_files) > 0 :
                    # obj_type : aclProfiles (src link: http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/aclProfiles/sys-acl1/clientConnectExceptions)
                    _,obj3 = os.path.split(src_link_tails2)
                    url = "{}/{}/{}".format(target_url, obj2, obj1)
                    #print (f'new url : {url}')

            for json_file in json_files:
                print ('\nReading JSON file  {}'.format(json_file))
                json_data, links, next_uri = self.json_h.read_json_data(json_file)
                if len(json_data) == 0 and len(links) == 0:
                    if Verbose:
                        print ('No data or links in {}'.format(json_file))
                    continue
                try:
                    self.semp_apply (url, target_obj, path, json_data, links, next_uri)
                except Exception as e:
                    print ()
                    print ('*******************************************************************************************')
                    #print (f'Exception: {e}')
                    print (f'   Failed to process {json_file}')
                    print ('*******************************************************************************************')
                    continue
            #else:
            #    log.info("No JSON file %s", json_file)
            
    def response_status(self, resp):
        """ parse out repsonse-status from json semp response """

        # check if the object is skipped by user
        status_cfg = SysCfg['status']
        c = status_cfg['statusSkip'] 
        if resp.status_code == c :
            return status_cfg[c]["status"], status_cfg[c]["description"]

        d = status_cfg['statusUnknown']
        rd = status_cfg[d]["status"]
        rs = status_cfg[d]["description"]
        resp_json = json.loads(resp.text)
        if 'meta' in resp_json:
            if 'error' in resp_json['meta']:
                if 'status' in resp_json['meta']['error'] :
                    rs =  resp_json['meta']['error']['status']
                if 'description' in resp_json['meta']['error'] :
                    rd =  resp_json['meta']['error']['description']
        return rs, rd


#-------------------------------------------------------------------------
# JSON Hanlding
#
class JsonHandler():
    """ JSON handling functions """

    def __init__(self):
        if Verbose :
                print ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))

    # read_json_data
    #   read solace json data and return data, links and next-page-uri
    def read_json_data (self, json_file) :
        """ parse json data & return parts """

        if Verbose :
            print ("{}::{} JSON file: {} ({})".format (__class__.__name__, inspect.stack()[0][3], json_file, type(json_file)))
        #json_fname = "{}/{}".format(path, fname)
        # 2.7 doesn't handle PostfixPath to open(). Do an explicit cast
        if type(json_file) != "str":
            json_file = str(json_file)
        with open(json_file, "r") as fp:
            json_payload = json.load(fp)  
        json_data = json_payload['data']

        links = None
        if 'links' in json_payload:
            links = json_payload['links']

        next_page_uri = None
        meta_data = json_payload['meta']
        if 'paging' in meta_data:
            next_page_uri = meta_data['paging']['nextPageUri']
        if Verbose > 2:
            print ('JSON DATA:\n'); pp.pprint(json_data)
            print ('LINKS :\n'); pp.pprint(links)
            print ('NEXT_PAGE_URI:\n '); pp.pprint(next_page_uri)
        return (json_data, links, next_page_uri)

    # read_json_file
    #  read json file and return as Python dictionary
    def read_json_file(self, file):
        """ read json file and return data """

        if Verbose > 0 :
            print ("Entering {}::{}  file: {}".format(__class__.__name__, inspect.stack()[0][3], file))
        with open(file, "r") as fp:
            data = json.load(fp)
        return data

    # list_json_files:
    #   Look for json files in a path and retrurn list of files. 
    def list_json_files(self, path, obj):
        if Verbose > 2:
            print (f'list_json_files: Looking for {obj}*.json in {path}')
        json_files = list(pathlib.Path(path).glob(f'{obj}*.json'))
        if Verbose :
            print (f'Found {len(json_files)} {obj}*.json files in {path}')
        if Verbose > 2:
            pp.pprint(json_files)
        return json_files

#------------------------------------------------------------------
#  program entry point - must be  below main()
#
if __name__ == "__main__":
    Main(sys.argv[1:]) 