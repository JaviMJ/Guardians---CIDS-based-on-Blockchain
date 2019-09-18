import requests
from datetime import datetime
import os.path

if not os.path.isfile('update_snort_rules.log'):
    file = open('./update_snort_rules.log', 'w+')
    file.close()

response = requests.post('https://127.0.0.1:8000/update_snort_rules', verify=False)
if response.status_code == 200:
    time = datetime.now()
    with open('./update_snort_rules.log', 'a') as file:
        file.write(time.strftime("%d/%m/%Y %H:%M:%S") + ' 200 - Update was successfully done.\r\n')
else:
    time = datetime.now()
    with open('./update_snort_rules.log', 'a') as file:
        file.write(time.strftime("%d/%m/%Y %H:%M:%S") + " " + str(response.status_code) + ' - ERROR update was not done.\r\n')


# To automate this script add the following line to your crontab.
# This task will throw this script everyday at 04:30
# 30 04 * * * python $ROUTE_SCRIPT & systemctl restart snortd
