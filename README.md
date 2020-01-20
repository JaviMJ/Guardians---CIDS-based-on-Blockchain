# Guardians CIDS based on Blockchain

Guardians is a functional prototype of a collaborative intrusion detection system (CIDS), where all the nodes are connected to each other by a private Blockchain network. These nodes use the Blockchain network to exchange rules in a secure way with all the benefits that these type of networks provides. Each node run a Snort IDS and Guardians server that includes a Blockchain server and the connector between Snort and the Blockchain.

This tool is full developed in Python 3.

## Get started
In the first place you must to have installed <a href="https://www.python.org/downloads/release/python-370/">Python 3.7</a> or >= Python 3.0 <a href="https://www.palletsprojects.com/p/flask/">Flask</a> >= 1.0 and <a href="https://www.snort.org/">Snort</a> in your system.

### Configuration

Before run Guardians server must be generated a first block (you can run Guardians server in only one node and copy manually) and copy this to each node. Also several configurations must be done in each node: 

- Snort must be installed and configurated as NIDS and running as a service.
- Set a passphrase in the file './secret'. This password will be used in order to add new nodes to the blockchain.
- Add peers lists to file './peers' with format 'IP:Port/'. Exclude self IP address.
- Generate TLS certificates inside './certificate/' in PEM format.
- Create file '/etc/snort/rules/blockchain.rules'. This file will contains rules exchanged between all the nodes.

### Usage
To run the application execute the following command:
```bash
python3 guardians_server.py
```
To add a new rule and share it execute the following script:
```bash
python3 ./scripts/add_rule.py
```
To update Snort rules with the new rules execure the following script:
```bash
python3 ./scripts/update_snort_rules.py
```
It is recommended to automate this script with a crontab. In order to automate this rules update.

To add a new node to the CIDS without needing to copy the chain manually, execute the folowing script:
```bash
python3 ./scripts/join_in_blockchain.py
```
