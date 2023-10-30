# get-vpn-config.py 
#
# Traverse Solace Message VPN configs with SEMPv2 REST post recursively
# Store output JSONs in a dir tree
# Usage:
#   python3 get-vpn-config.py --config localhost.json
# 
# TODO:
#   - JNDI Connection factories starting with fail. Skip for now. (see system.json)
#
# History:
#   - stop looking for json files on leaf path(eg: queue/<q>/subscrions)
#   - fixing bug with recursive obj lookup
#   - added single json with all vpn objects.
#   - removed next-page-url in the output.
#   - support for multiple vpn get
#   - skip if json file exists
#   - Initial working version
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

    
me = "get-vpn-config"
ver = '1.1'

# Globals
Cfg = {}    # global handy config dict
Verbose = 0  
pp = pprint.PrettyPrinter(indent=4)

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

    json_h = JsonHandler()

    Cfg = json_h.read_json_file(r.config_file)
    if Verbose > 2:
        print ('CONFIG', json.dumps(Cfg, indent=4))

    sys_cfg_file = Cfg["internal"]["systemConfig"]
    print ("Reading system config {}".format(sys_cfg_file))

    system_config_all = json_h.read_json_file (sys_cfg_file)
    if Verbose > 2:
        print ('SYSTEM CONFIG'); pp.pprint (system_config_all)
    sys_cfg = system_config_all # system_config_all["system"]

    Cfg['SysCfg'] = sys_cfg.copy() # store system cfg in the global Cfg dict

    cfg_p = ConfigParser(json_h)

    for vpn_name in Cfg["vpn"]["msgVpnNames"]:
        print ("\nGet VPN Config for {}".format(vpn_name))
        vpn_json_file = get_vpn_data(vpn_name)

        # get vpn data first
        print ('Parse VPN JSON Configs for {} ({})'. format(vpn_name, vpn_json_file))
        vpn_json_data = json_h.read_json_data (vpn_json_file)
        vpn_cfg = cfg_p.cfg_parse(vpn_name, os.path.dirname(vpn_json_file), vpn_json_data)

        # save cfg to file
        print ('Save VPN all config json')
        vpn_allcfg_out_file = "{}/{}-all.json". format(os.path.dirname(vpn_json_file), vpn_name)
        json_h.save_json_file(vpn_allcfg_out_file, vpn_cfg)


def get_vpn_data(vpn):
    """ process vpn recursively """
    if Verbose > 2:
         print ('Entering {}::{} vpn = {}'.format(__name__, inspect.stack()[0][3], vpn))

    rtr_cfg = Cfg["router"]
    sys_cfg = Cfg["SysCfg"]
    if Verbose > 2:
        print ('--- ROUTER :\n', json.dumps(rtr_cfg))
        print ('--- SYSCFG :\n', json.dumps(sys_cfg))

    url = "{}/{}/{}".format(rtr_cfg["sempUrl"], sys_cfg["semp"]["vpnConfigUrl"], vpn)
    out_dir = "{}/{}/{}".format(sys_cfg["system"]["outputDir"], rtr_cfg["label"], vpn)

    json_h = JsonHandler()
    semp_h = SempHandler(vpn, out_dir)
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

class SempHandler:
    """ Solace SEMPv2 Parser implementation """

    def __init__(self, vpn, out_dir):
        if Verbose > 2:
            print ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        self.out_dir = out_dir
        self.vpn = vpn

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
                print("   Get URL {} [{}] (*)".format(u_url, page_size))
                params = {'count':page_size}
                resp = self.http_get(url, params)
            else:
                print ("   Get URL {} (*)".format(u_url))
                resp = self.http_get(url)
        else:
            # No paging for non-collection objects
            print("   Get URL {}".format(u_url))
            resp = self.http_get(url) 

        if Verbose > 2:
            print("Get: req.json()")
            pp.pprint(resp.json())
        if (resp.status_code != 200):
            print(resp.text)
            raise RuntimeError
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
        json_h = JsonHandler()
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
        if Verbose:
            print ('http_get returned: {}'.format(resp))
        return resp

class JsonHandler():
    """ JSON handling functions """

    # class /static vars
    ObjMap = {} # static map used to get unique file-names

    def __init__(self):
        if Verbose > 2:
                print ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))

    def save_config_json (self,outfile, json_data):
        """ save config json to file """

        outfile = unquote(outfile)
        if Verbose > 2:
            print ("Entering {}::{}  file: {}". format (__class__.__name__, inspect.stack()[0][3], outfile))
        if os.path.exists(outfile):
            print ("   - Skiping {} (file exists)".format( outfile))
            return
        path,fname = os.path.split(outfile)
        if not os.path.exists(path):
            if Verbose > 2:
                print ('outfile: {} path: {} fname: {}'. format(outfile, path, fname))
                print ("makedir: {}".format(path))
            os.makedirs(path)
        print ("   > Writing to {}".format(outfile))
        with open(outfile, 'w') as fp:
            json.dump(json_data, fp, indent=4, sort_keys=True)

    def get_unique_fname (self,path,obj):
        """ helper fn to get a unique file name (eg: queue-1.json, queue-2.json) """   

        #obj1=urllib.parse.unquote(obj)
        obj1=unquote(obj)
        key=path+"/"+obj1
        if key not in JsonHandler.ObjMap:
            JsonHandler.ObjMap[key] = 0
            return "{}.json".format(obj1)
        JsonHandler.ObjMap[key] = JsonHandler.ObjMap[key]+1
        return ("{}-{}.json".format(obj1,JsonHandler.ObjMap[key]))

    def read_json_file(self,file):
        """ read json file and return data """

        if Verbose > 2 :
            print ("Entering {}::{}  file: {}".format(__class__.__name__, inspect.stack()[0][3], file))
        with open(file, "r") as fp:
            data = json.load(fp)
        return data

    def read_json_data (self, json_file) :
        """ parse json data & return parts """

        if Verbose > 2:
            print ("Entering {}::{} JSON file: {} ({})".format (__class__.__name__, inspect.stack()[0][3], json_file, type(json_file)))
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

        # no need to save next-page-url since all data is being appended
        #next_pg = None
        meta_data = json_payload['meta']
        if 'paging' in meta_data:
            next_page_uri = meta_data['paging']['nextPageUri']
        obj = {}
        obj['data'] = json_data
        obj['links'] = links
        #obj['next_pg'] = next_pg
        if Verbose > 2:
            print ('read_json_data: Object:\n'); pp.pprint(obj)
        return obj

    def save_json_file (self,outfile, json_data):
        """ save  json to file """

        outfile = unquote(outfile)
        if Verbose > 2:
            print ("Entering {}::{}  file: {}". format (__class__.__name__, inspect.stack()[0][3], outfile))
        if os.path.exists(outfile):
            print ("   Overwriting {}".format( outfile))
        else:
            print ("   Writing to {}".format(outfile))
        with open(outfile, 'w') as fp:
            json.dump(json_data, fp, indent=4, sort_keys=True)

class ConfigParser:
    """ Solace Config Parser implementation """

    def __init__(self, _json_h):
        if Verbose > 2:
            print ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        self.json_h = _json_h

    def cfg_parse (self, obj, path, cfg) :
        """ parse cfg recursively """

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
            print ('parse_links:Processing object: {} ({}) Link: {}'.format(obj, obj_type, link))

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
                print ('   Reading file {} ({})'.format(json_file, obj))
                this_obj = self.json_h.read_json_data(json_file)

                # add this object to base object
                if Verbose > 2:
                    print('cfg keys: ', cfg.keys())
                    #print ('JSON:'); pp.pprint(cfg)
                if obj_type in cfg:
                    print ('   + Adding {} {} to config'.format(obj, obj_type))
                    #pp.pprint(cfg[obj])
                    for d in this_obj['data']:
                        cfg[obj_type]['data'].append(d)
                    #for l in this_obj['links']:
                    #    cfg[obj_type]['links'].append(l)
                else:
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

if __name__ == "__main__":
    """ program entry point - must be  below main() """

    main(sys.argv[1:])
