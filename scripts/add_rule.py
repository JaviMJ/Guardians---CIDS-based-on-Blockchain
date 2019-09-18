import requests
import json

host = input('Introduce your IP connected to blockchain: ')
location = input('Introduce your location: ')
rule = input('Add new rule to pool: ')

data = {"host": host, "location": location, "rule": rule}
headers = {"Content-Type": "application/json"}

response_nt = requests.post('https://127.0.0.1:8000/new_transaction',
                            data=json.dumps(data), headers=headers, verify=False)
print(response_nt)
print(response_nt.status_code)

if response_nt.status_code == 200:
    print('Transaction added to unconfirmed transactions.')
    print('Sending request to mine the block.')
    response_mine = requests.post('https://127.0.0.1:8000/mine', verify=False)

    if response_mine.status_code == 200:
        print('The block has been mined.')
        print('Writing new rule into blockchain.rules temporarily, until update script will run.')
        try:
            with open('/etc/snort/rules/blockchain.rules', 'a') as file:
                file.write(rule)
        except:
            print('Error writing temporary rules.')

        print('Done!')
else:
    print(response_nt.status_code)
    print('The transaction has not been accepted')
