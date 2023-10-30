# Apply VPN Config

This script takes VPN config captured by [get-vpn-config](../docs/get-vpn-config.md) and clones them on a dMyerent Solace PubSub+ broker or on the same broker with dMyerent name. During clone, some objects can be optionally skipped. For e.g. while cloning UAT message-vpn to Production, all queues starting "test" can be configured to skipped.

## Running
```
▶ python3 apply-vpn-config.py --configfile private/my_qa.json --srcdatadir output/json/MyProject/my_dev/ --targetvpn my_qa | tee apply.out

create-vpn-1.1.0 Starting

Reading user config private/my_qa.json

Reading system config: config/system.json

Reading VPN config: output/json/MyProject/my_dev//vpn.json
Creating VPN my_qa
   - Skipping object:  msgVpns - User skipped
   * Skipped by user in config (ignored)

...

 ### VPN [my_qa] successfully created or updated on <https://mr-connection-1.messaging.solace.cloud:943>.
 
```