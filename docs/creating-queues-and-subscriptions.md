# Creating Queues and Subscriptions on existing VPN

This is a two step process. (three if you inlcude config createion)
* Pre step is to have [configs](/config/sample-local-config.yaml) and [input file](/config/sample-queues.csv) created that list the queues to be created
* In the first step, create required SEMP Json files to create Queues
* In the next step, apply these on the router to create the queues.

```
▶ python3 create-sempv2-json.py --vpn MyProject-xyz-dev --dir input/MyProject-xyz-dev --profile MyProject

▶ cp -pr output/MyProject-xyz-dev/queues/queues-0719-125115.json output/json/MyProject/MyProject-xyz-dev/queues

▶ python3 apply-vpn-config.py --configfile private/MyProject_dev.json --srcdatadir output/json/MyProject/MyProject-xyz-dev/ --targetvpn MyProject-xyz-dev  --items queues,subscriptions

...

Reading JSON file  output/json/MyProject/MyProject-xyz-dev/queues/queues-0719-125115.json
   + Processing queueName : abc.all.inv-adj.test.v1
   + Processing queueName : test.inventory_adjustment.canonical.test.v1
   + Processing queueName : abc.all.inv-hld and inv-sts and xx_prod_reversal.test.v1
   + Processing queueName : test.stock_movement.canonical.test.v1
   + Processing queueName : abc.all.inv-rcv.test.v1
   + Processing queueName : test.post_goods_receipt_for_purchase_orders.canonical.test.v1
   + Processing queueName : abc.all.master_rcpt_complete.test.v1
   + Processing queueName : test.post_goods_receipt_for_stock_transfer_orders.canonical.test.v1
   + Processing queueName : test.post_goods_receipt_for_customer_returns.canonical.test.v1
   + Processing queueName : abc.all.ship_load.test.v1
   + Processing queueName : test.shipment_confirmation.canonical.test.v1
   + Processing queueName : abc.all.trlr_change.test.v1
   + Processing queueName : test.trailer_check_in_and_out.canonical.test.v1
   + Processing queueName : abc.all.xx_shipment_process_status.test.v1
   + Processing queueName : abc.all.xx_appointment_time.test.v1
   + Processing queueName : test.picking_status_update.canonical.test.v1
   + Processing queueName : abc.all.xx_inventory_snapshot.test.v1
   + Processing queueName : test.inventory_snapshot.canonical.test.v1
   + Processing queueName : test.shipment_and_delivery_details.canonical.abc.v1
   + Processing queueName : test.xx_mnt-delivery_and_xx_mnt_traffic_plan.abc.1000.v1
   + Processing queueName : test.carrier_master.canonical.abc.v1
   + Processing queueName : test.xx_mnt-carrier-service.abc.1000.v1
   + Processing queueName : test.supplier_master.canonical.abc.v1
   + Processing queueName : test.xx_mnt-sup.abc.1000.v1
   + Processing queueName : test.customer_master.canonical.abc.v1
   + Processing queueName : test.xx_mnt-cus.abc.1000.v1
   + Processing queueName : test.product_master.canonical.abc.v1
   + Processing queueName : test.xx_part_management.abc.1000.v1
   + Processing queueName : test.xx_rcpt_management.abc.1000.v1
 
```