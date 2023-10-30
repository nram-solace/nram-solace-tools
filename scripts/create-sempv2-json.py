#!/usr/bin/python
################################################################################
# create-sempv2-json.py
#   Script to generate Solace VPN and other config JSON files based on inputs
#   and templates. 
#
# Ramesh Natarajan (nram), Solace PSG
# nram@nram.dev
################################################################################


import argparse
import os, glob
import json
from datetime import datetime


#-----------------------------------------------------------------------------
#   MAIN
#-----------------------------------------------------------------------------
# Parse args
p = argparse.ArgumentParser(description='Create Solace Config JSON Files',
                            formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--vpn', action="store",  required=True, help='VPN Name')
p.add_argument('--dir', action="store",  required=True, help='Directory with input files')
p.add_argument('--profile', action="store",  required=True, help='Profile name')
p.add_argument('--delete', action='store_true', default=False, required=False, help='delete objects')
p.add_argument( '--verbose', '-v', action="count",  required=False, default=0,
                help='Turn Verbose. Use -vvv to be very verbose')
r = p.parse_args()


d_fields = {}
d_inputs = {}

# collect all input files
if r.verbose > 0:
    print ('Arguments:\n\tVPN: {}\n\Profile: {}\n\tDir: {}'.format(r.vpn, r.profile, r.dir))

if not os.path.exists(r.dir):
    print ("Input dir {} not found".format(r.dir))
    exit(2)

adir='create'
if r.delete:
    adir='delete'
# Open Tier config files
profile_file = 'config/{}.json'.format(r.profile)
print ('Opening {} Profile file: {}'.format(r.profile, profile_file))
with open(profile_file, 'r') as profile_fd:
    profile_json = json.load(profile_fd)
    if r.verbose > 2:
        print (json.dumps(profile_json, indent=3))

# read input CSV files into a dictionary of arrays (d_inputs)
# separate title into d_fields
print ('Opening input files from: {}'.format(r.dir))
files=glob.glob('{}/*.csv'.format(r.dir))
if r.verbose > 2:
    print ('files:', files)
for file in files:
    fname = os.path.splitext(os.path.basename(file))[0]
    if r.verbose > 0:
        print ('\tOpening file {}'.format(file))
    with open(file, 'r') as fd:
        d_fields[fname] = fd.readline().strip()
        d_inputs[fname] = fd.readlines()
# add vpn object -- its read in from arg
d_fields['vpn'] = 'msgVpnName'
#d_inputs['vpn'] = [r.vpn]


request_object = {}
request_object["method"] = "GET"
meta_object = {}
meta_object["request"] = request_object

# Loop thru the objects (acl_profile, client_profile, queues, ...)

for vpnobj in d_inputs.keys():
    json_data_array = []
    links_data_array = []

    # Read corresponding template json file
    is_queues = False
    is_subsctiptions = False
    is_jndj_queues = False
    if vpnobj == 'queues':
        is_queues = True
    if vpnobj == 'subscriptions':
        is_subsctiptions = True
    if vpnobj == 'jndiQueues':
        is_jndj_queues = True
    print ('Generating {} configs'.format(vpnobj))
    template_file = 'templates/{}/{}.json'.format(adir, vpnobj)
    if r.verbose > 0:
        print ('\tOpening template file: {}'.format(template_file))
    with open(template_file, 'r') as template_fd:
        json_data = json.load(template_fd)
    if r.verbose > 2:
        print ('--- Data read')
        print (json.dumps(json_data))

    # replace passed in & read in values
    json_data["msgVpnName"] = r.vpn

    l_fields = d_fields[vpnobj].split(',')
    if r.verbose > 2:
        print ('title', d_fields[vpnobj])
        print ('title list', l_fields)
    output_dir = "output/{}/{}".format(r.vpn, vpnobj)
    # If output dir doesn't exist, create it
    if not os.path.exists(output_dir):
        print ("Creating output dir: {}". format(output_dir))
        os.makedirs(output_dir, 0o755);
        #os.makedirs(output_dir, "0755");
    for l in d_inputs[vpnobj]:
        l = l.strip()
        # skip empty and comment lines
        if len(l) <= 1 or l.startswith('#'):
            continue
        l_values =  l.split(',')
        if is_queues or is_jndj_queues:
            queue_name = l_values[0]
        if r.verbose > 0:
            print ("\tCreating Config for {}: {}".format(vpnobj, l_values[0]))
        if r.verbose > 2:
            print('values list', l_values, len(l))

        # replace field value (eg: queueName) with value read in (eg: myqueue1)
        # multiple substitions used only for client_user now -- username, acl_profile, client_profile
        n = 0
        while n < len(l_fields):
            json_data[l_fields[n]] = l_values[n]
            n = n + 1

        if vpnobj in profile_json.keys():
            vpnobj_values = profile_json[vpnobj]
            for k, v in vpnobj_values.items():
                if (r.verbose > 0):
                    print ('\t   Set {}.{} => {}'.format(vpnobj, k, v))
                json_data[k] = v
        if r.verbose > 2:
            print ('--- Data modified')
            print (json.dumps(json_data, indent=3))

        # Write output json file
        if is_queues:
            if (r.verbose > 0):
                print ('\tSkip file per queue {}'.format(l_values[0]))
        elif is_subsctiptions:
            # skip if subscription topic is empty
            if len(json_data['subscriptionTopic']) <= 1:
                print ('\tSkip empty subscription for {}'.format(l_values[0]))
                continue
            final_json_object = {}
            final_json_object["data"] = json_data
            final_json_object["meta"] = meta_object

            output_dir_sub = "output/{}/queues/{}/subscriptions".format(r.vpn, l_values[0])
            if not os.path.exists(output_dir_sub):
                os.makedirs(output_dir_sub, 0o755);
            output_file = "{}/subscriptions.json".format(output_dir_sub)
            print ("\tCreating {}".format(output_file))
            with open(output_file, "w") as output_fd:
                json.dump(final_json_object, output_fd, indent=3)
        else:
            final_json_object = {}
            final_json_object["data"] = json_data
            final_json_object["meta"] = meta_object
            output_file = "{}/{}.json".format(output_dir, l_values[0])
            print ("\tCreating {}".format(output_file))
            with open(output_file, "w") as output_fd:
                json.dump(final_json_object, output_fd, indent=3)
        # add json_data to json_data_array
        json_data_array.append(json_data.copy())

        # add link data
        link_data = {}
        if is_queues:
            link_data["subscriptionsUri"] = "http://solace:8080/SEMP/v2/config/msgVpns/{}/{}/{}/subscriptions".format(r.vpn, vpnobj, queue_name)
        links_data_array.append(link_data.copy())

    if is_queues :
        final_json_object = {}
        final_json_object["data"] = json_data_array
        final_json_object["links"] = links_data_array
        final_json_object["meta"] = meta_object
        # Write output json file
        output_dir_q = "output/{}/queues".format(r.vpn, l_values[0])
        if not os.path.exists(output_dir_q):
            os.makedirs(output_dir_q, 0o755);
        ts = datetime.now().strftime("%m%d-%H%M%S")

        output_file = "{}/queues-{}.json".format(output_dir_q, ts)
        print ("\tCreating {}".format(output_file))
        with open(output_file, "w") as output_fd:
            json.dump(final_json_object, output_fd, indent=3)

    if is_jndj_queues :
        final_json_object = {}
        final_json_object["data"] = json_data_array
        final_json_object["links"] = links_data_array
        final_json_object["meta"] = meta_object
        # Write output json file
        output_dir_q = "output/{}/jndiQueues".format(r.vpn, l_values[0])
        if not os.path.exists(output_dir_q):
            os.makedirs(output_dir_q, 0o755);
        ts = datetime.now().strftime("%m%d-%H%M%S")

        output_file = "{}/jndiQueues-{}.json".format(output_dir_q, ts)
        print ("\tCreating {}".format(output_file))
        with open(output_file, "w") as output_fd:
            json.dump(final_json_object, output_fd, indent=3)
