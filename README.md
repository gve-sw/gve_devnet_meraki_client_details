# gve_devnet_meraki_client_details
Scans all organizations for a given API key, and writes all client details found within each organization to a CSV.


## Contacts
* Charles Llewellyn

## Solution Components
* Meraki
*  Python


## Installation/Configuration

This project requires the following setup: 
1. Install Python3
2. Install pip3 (if not installed with python3)
3. Create virtual environment

   ``` python3 -m venv venv```
   
4. Activate vitrual environment:

   OSX/Linux:
      
      ```source venv/bin/activate```
      
   Windows:
      
      ```venv\Scripts\activate```
  
5. Upgrade pip3

    ```pip3 install --upgrade pip```
  
6. Install script requirements

    ```pip3 install -r requirements.txt```


## Usage

``` python find_clients.py -k <api key> [ -o <org name> -n <net filter> -c <client filter> -t <timespan>]```

Script syntax:


      Mandatory parameters:
          -k <api key>            : Your Meraki Dashboard API key

      Optional parameters:
          -o <org name>           : Organization name query string
          -n <net filter>         : Network query string. Matches names, tags and productTypes
          -c <client filter>      : Client query string. Matches description, IP or MAC
          -t <timespan>           : Look back timespan in days. Default is 7

          Ommiting a query string will match all items. Query strings are not
          case sensitive. Examples of valid productType filters: wireless, switch, appliance.
          Filters for productTypes must be exact matches. All other filters support partial matching

      Example:
          python find_clients.py -k 1234 -o "Big Industries" -c "iphone"



# Screenshots

![/IMAGES/0image.png](/IMAGES/0image.png)

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
