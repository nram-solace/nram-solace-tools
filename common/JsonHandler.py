##############################################################################
# JsonHandler
#   Common class for JSON Handling functions
#
# Ramesh Natarajan (nram@nram.dev)
##############################################################################

import sys, os
import json
import pprint
import inspect
#import pathlib
from urllib.parse import unquote

pp = pprint.PrettyPrinter(indent=4)
Verbose = 0
class JsonHandler():
    """ JSON handling functions """

    # class /static vars
    ObjMap = {} # static map used to get unique file-names

    def __init__(self, verbose=0):
        global Verbose
        Verbose = verbose
        if Verbose > 2:
                print ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))

    def save_config_json (self,outfile, json_data):
        global Verbose
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
        print ("   + Writing to {}".format(outfile))
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
        global Verbose

        if Verbose > 2 :
            print ("Entering {}::{}  file: {}".format(__class__.__name__, inspect.stack()[0][3], file))
        with open(file, "r") as fp:
            data = json.load(fp)
        return data

    def read_json_data (self, json_file) :
        """ parse json data & return parts """
        global Verbose

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
        global Verbose

        outfile = unquote(outfile)
        if Verbose > 2:
            print ("Entering {}::{}  file: {}". format (__class__.__name__, inspect.stack()[0][3], outfile))
        if os.path.exists(outfile):
            print ("   Overwriting {}".format( outfile))
        else:
            print ("   + Writing to {}".format(outfile))
        with open(outfile, 'w') as fp:
            json.dump(json_data, fp, indent=4, sort_keys=True)