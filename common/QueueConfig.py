#####################################################################
# QueueConfig
# Implement Queue provisioning functions
#
# Ramesh Natarajan 
# Solace PSG
#####################################################################

import sys, os
import json
from urllib.parse import unquote, quote
import pprint

# Globals
pp = pprint.PrettyPrinter(indent=4)
Verbose = 0

class Queues():

    def __init__(self, semp_h, cfg, input_df, verbose = 0):
        global Verbose
        Verbose = verbose
        self.semp_h = semp_h
        self.cfg = cfg
        self.input_df = input_df
    #--------------------------------------------------------------------
    # get_topic_list
    # Get list of topics from SEMP response
    #--------------------------------------------------------------------
    def get_topic_list (self, resp):

        resp_json = json.loads(resp.text)
        topic_list = []
        if 'data' in resp_json:
            for sub in resp_json['data']:
                topic_list.append(sub['subscriptionTopic'])
        return topic_list

    #--------------------------------------------------------------------
    # create_or_update_queues
    # Create Queues with http post
    # If queue exists (http_post retunred ALREADY_EXISTS)
    #    disable it
    #    update using http_patch and enable it
    #  Add topic subscriptions list to queue
    #  In patch mode, remove existing subscriptions and reapply new
    #--------------------------------------------------------------------
    def create_or_update_queue (self, patch_it):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['SysCfg']
        input_df = self.input_df
        print ('Creating Queues in VPN: {} on router: {}'.format(cfg['vpn']['msgVpnNames'][0], cfg['router']['sempUrl']))

        # Loop through each row and generate obj for SEMP Req
        msg_vpn_name = cfg['vpn']['msgVpnNames'][0]
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        num_queues = len(input_df.index)
        n = 0

        queue_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['templates']['queue']:
            queue_props.append(k)
        # add required tags
        queue_props.append('queueName')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', queue_props)    
        
        for index, qdata in input_df.iterrows():
            n = n + 1
            #print ('data read', d)
            #print (f"VPN name: [{d['msgVpnName']}]")
            data={}
            data=cfg['templates']['queue'].copy()
            #data['messageVpn'] = msg_vpn_name
            queue = qdata['queueName'].strip()
            for prop in queue_props:
                if prop in qdata:
                    if isinstance(qdata[prop], str) and qdata[prop].strip() != "":
                        data[prop] = qdata[prop].strip()
                    #else:
                    #    data[prop] = qdata[prop]
            # enable queues
            data['egressEnabled'] = True
            data['ingressEnabled'] = True
            #if Verbose > 2:
            #    print ('data enhanced'); pp.pprint(data)
            # remove subscriptionTopic
            sub_topic_saved = data['subscriptionTopic']
            data.pop('subscriptionTopic', None)
            ###################################################
            # post to router - create queue
            #
            print (f"\n{n:2}/{num_queues:3} ) Creating queue: <{queue}>")
            resp = semp_h.http_post (semp_queue_config_url, data)
            if patch_it and resp == 'ALREADY_EXISTS':
                #---------------------------------------------------
                # If Queue exists, patch it
                #
                print (f'   + Queue {queue} exists. Disable and patch it')
                # disable queue first
                data0 = {}
                data0['queueName'] = queue
                data0['msgVpnName'] = msg_vpn_name
                data0['egressEnabled'] = False
                #data0['ingressEnabled'] = False
                semp_h.http_patch (f"{semp_queue_config_url}/{queue}", data0)
                # Patch with new values and enable
                semp_h.http_patch (f"{semp_queue_config_url}/{queue}", data)

            if patch_it:
                # remove subscriptions first
                print ('   = Reapply subscriptions (PATCH)')
                semp_queue_sub_config_url = f"{semp_config_url}/{msg_vpn_name}/queues/{queue}/subscriptions"
                resp = semp_h.http_get(semp_queue_sub_config_url)
                for topic in self.get_topic_list (resp):
                    print (f'   - Deleting subscription topic: [{topic}]')
                    semp_queue_sub_delete_url = f"{semp_config_url}/{msg_vpn_name}/queues/{queue}/subscriptions/{quote(topic, safe='')}"
                    semp_h.http_delete (semp_queue_sub_delete_url)
            # now add subscription topics
            for topics in sub_topic_saved.split(':'):
                topic = topics.strip()
                if topic != "":
                    data = {}
                    data['msgVpnName'] = msg_vpn_name
                    data['queueName'] = queue
                    data['subscriptionTopic'] = topic
                    print (f'   + Adding subscription topic: [{topic}]')
                    semp_queue_sub_config_url = f"{semp_config_url}/{msg_vpn_name}/queues/{queue}/subscriptions"
                    semp_h.http_post (semp_queue_sub_config_url, data)


    #--------------------------------------------------------------------
    # create_or_update_dmqueue
    # Special handling or DMQ. 
    # Get list of deadMsgQueue from input file and create them 
    # All of them are created with same properties (cfg['templates']['dmqueue'])
    # No subscriptions are supported for DMQ. 
    # If you really want a DMQ with override properties / subscriptions, 
    # then provision it as a regular queue
    #--------------------------------------------------------------------
    def create_or_update_dmqueue (self, patch_it):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['SysCfg']
        input_df = self.input_df
        print ('Creating DMQueues in VPN: {} on router: {}'.format(cfg['vpn']['msgVpnNames'][0], cfg['router']['sempUrl']))

        # Loop through each row and generate obj for SEMP Req
        msg_vpn_name = cfg['vpn']['msgVpnNames'][0]
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        num_queues = len(input_df.index)
        n = 0

        queue_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['templates']['dmqueue']:
            queue_props.append(k)
        # add required tags
        queue_props.append('deadMsgQueue')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', queue_props)    
        
        for index, qdata in input_df.iterrows():
            n = n + 1
            #print ('data read', d)
            #print (f"VPN name: [{d['msgVpnName']}]")
            data={}
            data=cfg['templates']['dmqueue'].copy()
            #data['messageVpn'] = msg_vpn_name
            queue = qdata['queueName'].strip()

            # enable queues
            data['egressEnabled'] = True
            data['ingressEnabled'] = True
            data['msgVpnName'] = msg_vpn_name
            data['queueName'] = queue
            data.pop('subscriptionTopic', None)

            ###################################################
            # post to router - create queue
            #
            print (f"\n{n:2}/{num_queues:3} ) Creating queue: <{queue}>")
            resp = semp_h.http_post (semp_queue_config_url, data)
            if patch_it and resp == 'ALREADY_EXISTS':
                #---------------------------------------------------
                # If Queue exists, patch it
                #
                print (f'   + Queue {queue} exists. Disable and patch it')

                # Patch with new values and enable
                semp_h.http_patch (f"{semp_queue_config_url}/{queue}", data)