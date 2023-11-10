# Get VPN Config
[get-vpn-config.py](/scripts/get-vpn-config.py)

This script captures Solace Message-VPN config recursively and saves them locally. This is useful for taking config backup or for cloning it on a dabcerent broker or as dabcerent message VPN.

## Running
``` shell
▶ python3 scripts/get-vpn-config.py --config config/sample-config-local.yaml

get-vpn-config-2.0.0 Starting

Reading user config file  : config/sample-config-local.yaml
Reading system config file: config/system.yaml

Get VPN Config for TestVPN
   - Skiping output/json/localhost/TestVPN/vpn.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/aclProfiles.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/#acl-profile/clientConnectExceptions/clientConnectExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/#acl-profile/publishExceptions/publishExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/#acl-profile/publishTopicExceptions/publishTopicExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/#acl-profile/subscribeExceptions/subscribeExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/#acl-profile/subscribeShareNameExceptions/subscribeShareNameExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/#acl-profile/subscribeTopicExceptions/subscribeTopicExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/default/clientConnectExceptions/clientConnectExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/default/publishExceptions/publishExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/default/publishTopicExceptions/publishTopicExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/default/subscribeExceptions/subscribeExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/default/subscribeShareNameExceptions/subscribeShareNameExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//aclProfiles/default/subscribeTopicExceptions/subscribeTopicExceptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//authenticationOauthProfiles/authenticationOauthProfiles.json (file exists)
   - Skiping output/json/localhost/TestVPN//authenticationOauthProviders/authenticationOauthProviders.json (file exists)
   - Skiping output/json/localhost/TestVPN//authorizationGroups/authorizationGroups.json (file exists)
   - Skiping output/json/localhost/TestVPN//bridges/bridges.json (file exists)
   - Skiping output/json/localhost/TestVPN//certMatchingRules/certMatchingRules.json (file exists)
   - Skiping output/json/localhost/TestVPN//clientProfiles/clientProfiles.json (file exists)
   - Skiping output/json/localhost/TestVPN//clientUsernames/clientUsernames.json (file exists)
**** Get URL http://localhost:8080/SEMP/v2/config/msgVpns/TestVPN/clientUsernames/#client-username/attributes failed ****
   - Skiping output/json/localhost/TestVPN//clientUsernames/#client-username/attributes/attributes.json (file exists)
   - Skiping output/json/localhost/TestVPN//clientUsernames/default/attributes/attributes.json (file exists)
   - Skiping output/json/localhost/TestVPN//clientUsernames/testuser/attributes/attributes.json (file exists)
   - Skiping output/json/localhost/TestVPN//distributedCaches/distributedCaches.json (file exists)
   - Skiping output/json/localhost/TestVPN//dmrBridges/dmrBridges.json (file exists)
   - Skiping output/json/localhost/TestVPN//jndiConnectionFactories/jndiConnectionFactories.json (file exists)
   - Skiping output/json/localhost/TestVPN//jndiQueues/jndiQueues.json (file exists)
   - Skiping output/json/localhost/TestVPN//jndiTopics/jndiTopics.json (file exists)
   - Skiping output/json/localhost/TestVPN//kafkaReceivers/kafkaReceivers.json (file exists)
   - Skiping output/json/localhost/TestVPN//kafkaSenders/kafkaSenders.json (file exists)
   - Skiping output/json/localhost/TestVPN//mqttRetainCaches/mqttRetainCaches.json (file exists)
   - Skiping output/json/localhost/TestVPN//mqttSessions/mqttSessions.json (file exists)
   - Skiping output/json/localhost/TestVPN//proxies/proxies.json (file exists)
   - Skiping output/json/localhost/TestVPN//queueTemplates/queueTemplates.json (file exists)
   - Skiping output/json/localhost/TestVPN//queues/queues.json (file exists)
   - Skiping output/json/localhost/TestVPN//queues/TestQ/subscriptions/subscriptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//queues/TestQ2/subscriptions/subscriptions.json (file exists)
   - Skiping output/json/localhost/TestVPN//replayLogs/replayLogs.json (file exists)
   - Skiping output/json/localhost/TestVPN//replicatedTopics/replicatedTopics.json (file exists)
   - Skiping output/json/localhost/TestVPN//restDeliveryPoints/restDeliveryPoints.json (file exists)
   - Skiping output/json/localhost/TestVPN//sequencedTopics/sequencedTopics.json (file exists)
   - Skiping output/json/localhost/TestVPN//telemetryProfiles/telemetryProfiles.json (file exists)
   - Skiping output/json/localhost/TestVPN//topicEndpointTemplates/topicEndpointTemplates.json (file exists)
   - Skiping output/json/localhost/TestVPN//topicEndpoints/topicEndpoints.json (file exists)
Parse VPN JSON Configs for TestVPN (output/json/localhost/TestVPN/vpn.json)
Save VPN all config json
   Overwriting output/json/localhost/TestVPN/TestVPN-all.json

Get VPN Config for ProdVPN
   - Skiping output/json/localhost/ProdVPN/vpn.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/aclProfiles-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/#acl-profile/clientConnectExceptions/clientConnectExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/#acl-profile/publishExceptions/publishExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/#acl-profile/publishTopicExceptions/publishTopicExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/#acl-profile/subscribeExceptions/subscribeExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/#acl-profile/subscribeShareNameExceptions/subscribeShareNameExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/#acl-profile/subscribeTopicExceptions/subscribeTopicExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/default/clientConnectExceptions/clientConnectExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/default/publishExceptions/publishExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/default/publishTopicExceptions/publishTopicExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/default/subscribeExceptions/subscribeExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/default/subscribeShareNameExceptions/subscribeShareNameExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//aclProfiles/default/subscribeTopicExceptions/subscribeTopicExceptions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//authenticationOauthProfiles/authenticationOauthProfiles-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//authenticationOauthProviders/authenticationOauthProviders-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//authorizationGroups/authorizationGroups-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//bridges/bridges-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//certMatchingRules/certMatchingRules-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//clientProfiles/clientProfiles-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//clientUsernames/clientUsernames-1.json (file exists)
**** Get URL http://localhost:8080/SEMP/v2/config/msgVpns/ProdVPN/clientUsernames/#client-username/attributes failed ****
   - Skiping output/json/localhost/ProdVPN//clientUsernames/#client-username/attributes/attributes-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//clientUsernames/default/attributes/attributes-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//distributedCaches/distributedCaches-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//dmrBridges/dmrBridges-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//jndiConnectionFactories/jndiConnectionFactories-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//jndiQueues/jndiQueues-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//jndiTopics/jndiTopics-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//kafkaReceivers/kafkaReceivers-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//kafkaSenders/kafkaSenders-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//mqttRetainCaches/mqttRetainCaches-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//mqttSessions/mqttSessions-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//proxies/proxies-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//queueTemplates/queueTemplates-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//queues/queues-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//queues/MyQ/subscriptions/subscriptions.json (file exists)
   - Skiping output/json/localhost/ProdVPN//queues/XYZ/subscriptions/subscriptions.json (file exists)
   - Skiping output/json/localhost/ProdVPN//replayLogs/replayLogs-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//replicatedTopics/replicatedTopics-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//restDeliveryPoints/restDeliveryPoints-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//sequencedTopics/sequencedTopics-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//telemetryProfiles/telemetryProfiles-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//topicEndpointTemplates/topicEndpointTemplates-1.json (file exists)
   - Skiping output/json/localhost/ProdVPN//topicEndpoints/topicEndpoints-1.json (file exists)
Parse VPN JSON Configs for ProdVPN (output/json/localhost/ProdVPN/vpn.json)
Save VPN all config json
   Overwriting output/json/localhost/ProdVPN/ProdVPN-all.json

get-vpn-config Done
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