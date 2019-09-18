import requests
import json
from getpass import getpass

host = input('Introduce IP to connect: ')
myip = input('Introduce your IP: ')
print('Introduce secret: \n')
password = getpass()

data = {"node_address": host, "myip": myip, "secret": password}
headers = {"Content-Type": "application/json"}

response_nt = requests.post('https://127.0.0.1:8000/register_with',
                            data=json.dumps(data), headers=headers, verify=False)
print(response_nt)
print(response_nt.status_code)