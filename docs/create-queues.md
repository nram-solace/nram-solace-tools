# Create Queues

This program creates new or update existing queues on a Solace PubSub+ broker using SEMPv2
While updating, exisitng Queue will be temporarliy disabled, updated and enabled.

All config and inputs are read from files for batch processing
## Requirements
```
 Python 3
 Modules: pandas, json, yaml
```
## Required input files:
```
Config Yaml file:
  This file has Solace PubSub+ broker access info, default values for queues, etc.
  See config/sample-config.yaml
Input CSV file:
  This file has list of queue names and properties that should be overwritten.
  See input/sample-queues.csv
  Properties will  be taken from the input CSV file if present 
  Otherwise, default values from config file will be used
  Otherwise, Solace default values will be used
```

## Running

```
Create queues:
  python3 create-queues.py --config config/nram-local-config.yaml  --input input/nram-test-queues.csv
Create new or update existing queues: Use --patch option
  python3 create-queues.py --config private/nram/nram-dev1.yaml  --input private/MyProject/my-queues-tests1.csv --patch
```