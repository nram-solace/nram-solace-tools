# Get VPN Config
This script captures Solace Message-VPN config recursively and saves them locally. This is useful for taking config backup or for cloning it on a dabcerent broker or as dabcerent message VPN.

## Running
``` shell
▶ python3 get-vpn-config.py --config private/abc_dev.json 
get-vpn-config-1.1 Starting

Reading system config config/system.json

Get VPN Config for abc_dev
   Get URL https://mr-connection-x1.messaging.solace.cloud:943/SEMP/v2/config/msgVpns/abc_dev
   > Writing to output/json/ABC/abc_dev/vpn.json
   Get URL https://mr-connection-x1.messaging.solace.cloud:943/SEMP/v2/config/msgVpns/abc_dev/aclProfiles [10] (*)
   > Writing to output/json/ABC/abc_dev//aclProfiles/aclProfiles.json
...
parse_links:Processing object: topicEndpoints (ABC_DEV/POC/Manual/Topic) Link: https://mr-connection-x1.messaging.solace.cloud:943/SEMP/v2/config/msgVpns/abc_dev/topicEndpoints/ABC_DEV/POC/Manual/Topic
parse_links:Processing object: topicEndpoints (Topic_EndPoint) Link: https://mr-connection-x1.messaging.solace.cloud:943/SEMP/v2/config/msgVpns/abc_dev/topicEndpoints/Topic_EndPoint
parse_links:Processing object: topicEndpoints (Topic_POC) Link: https://mr-connection-x1.messaging.solace.cloud:943/SEMP/v2/config/msgVpns/abc_dev/topicEndpoints/Topic_POC
parse_links:Processing object: msgVpns (abc_dev) Link: https://mr-connection-x1.messaging.solace.cloud:943/SEMP/v2/config/msgVpns/abc_dev
Save VPN all config json
   Writing to output/json/ABC/abc_dev/abc_dev-all.json

```

### Verify JSON files are created locally

```
	? ls output/json/nram_poc/nram-poc-vpn
	aclProfiles                  certMatchingRules            jndiConnectionFactories      nram-poc-vpn-all.json        restDeliveryPoints
	authenticationOauthProfiles  clientProfiles               jndiQueues                   queueTemplates               sequencedTopics
	authenticationOauthProviders clientUsernames              jndiTopics                   queues                       topicEndpointTemplates
	authorizationGroups          distributedCaches            mqttRetainCaches             replayLogs                   topicEndpoints
	bridges                      dmrBridges                   mqttSessions                 replicatedTopics             vpn.json

	ABC/Tools/abc-sempv2-tools  master ?                                                                                                                                                   17m ? ?
	? ls output/json/nram_poc/nram-poc-vpn/queues
	MQ.IN                             Q.DEV.QUEUE.1                     Q.TEST                            TestQ                             nram-poc-vpn_nram-dev1-ohio_Queue
	MQ.OUT                            Q.DEV.QUEUE.2                     Q.TO.MQ.NRAM                      TestQ-FromAWS                     queues.json
```