# Move or Copy Messages

 Copy/Move messages between Solace Queues

 Use --copy-only to copy messages (leave messages in source queue)
 Default is to move messages (delete from source queue)
## Note:
-  Max Page size is 100 (SEMP limitation?). Can't move more than 100 messages in one run

# Running

```
python3 move-queue-msgs.py --config config/sample-config.json -v           
 
move-queue-msgs-1.0 Starting
 
Reading system config config/system.json
Moving Msgs from Queue DMQ/TestQ -> TestQ in VPN TestVPN
copy_or_move_msgs: vpn: TestVPN src_q: DMQ/TestQ dest_q: TestQ
Moving 1 messages from DMQ/TestQ -> TestQ
- Moving msg 1 of 1 (Msg Id: 2421, ID: rmid1:25642-a51831bc04e-00000000-00000975)
   Copy message rmid1:25642-a51831bc04e-00000000-00000975 to TestQ
   * Delete message 2421 from DMQ/TestQ
```