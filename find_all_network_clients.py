"""
CISCO SAMPLE CODE LICENSE Version 1.1 Copyright (c) 2020 Cisco and/or its affiliates

These terms govern this Cisco Systems, Inc. ("Cisco"), example or demo source code and its associated documentation 
(together, the "Sample Code"). By downloading, copying, modifying, compiling, or redistributing the Sample Code, you 
accept and agree to be bound by the following terms and conditions (the "License"). If you are accepting the License on 
behalf of an entity, you represent that you have the authority to do so (either you or the entity, "you"). Sample Code is 
not supported by Cisco TAC and is not tested for quality or performance. This is your only license to the Sample Code and all 
rights not expressly granted are reserved.

    LICENSE GRANT: Subject to the terms and conditions of this License, Cisco hereby grants to you a perpetual, 
    worldwide, non-exclusive, non- transferable, non-sublicensable, royalty-free license to copy and modify the 
    Sample Code in source code form, and compile and redistribute the Sample Code in binary/object code or other 
    executable forms, in whole or in part, solely for use with Cisco products and services. For interpreted languages 
    like Java and Python, the executable form of the software may include source code and compilation is not required.

    CONDITIONS: You shall not use the Sample Code independent of, or to replicate or compete with, a Cisco product or service. 
    Cisco products and services are licensed under their own separate terms and you shall not use the Sample Code in any way that 
    violates or is inconsistent with those terms (for more information, please visit: www.cisco.com/go/terms).

    OWNERSHIP: Cisco retains sole and exclusive ownership of the Sample Code, including all intellectual property rights 
    therein, except with respect to any third-party material that may be used in or by the Sample Code. Any such third-party 
    material is licensed under its own separate terms (such as an open source license) and all use must be in full accordance 
    with the applicable license. This License does not grant you permission to use any trade names, trademarks, service marks, 
    or product names of Cisco. If you provide any feedback to Cisco regarding the Sample Code, you agree that Cisco, its partners, 
    and its customers shall be free to use and incorporate such feedback into the Sample Code, and Cisco products and services, 
    for any purpose, and without restriction, payment, or additional consideration of any kind. If you initiate or participate in any 
    litigation against Cisco, its partners, or its customers (including cross-claims and counter-claims) alleging that the Sample Code 
    and/or its use infringe any patent, copyright, or other intellectual property right, then all rights granted to you under this License 
    shall terminate immediately without notice.

    LIMITATION OF LIABILITY: CISCO SHALL HAVE NO LIABILITY IN CONNECTION WITH OR RELATING TO THIS LICENSE OR USE OF THE SAMPLE CODE, 
    FOR DAMAGES OF ANY KIND, INCLUDING BUT NOT LIMITED TO DIRECT, INCIDENTAL, AND CONSEQUENTIAL DAMAGES, OR FOR ANY LOSS OF USE, DATA, 
    INFORMATION, PROFITS, BUSINESS, OR GOODWILL, HOWEVER CAUSED, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

    DISCLAIMER OF WARRANTY: SAMPLE CODE IS INTENDED FOR EXAMPLE PURPOSES ONLY AND IS PROVIDED BY CISCO "AS IS" WITH ALL FAULTS AND WITHOUT 
    WARRANTY OR SUPPORT OF ANY KIND. TO THE MAXIMUM EXTENT PERMITTED BY LAW, ALL EXPRESS AND IMPLIED CONDITIONS, REPRESENTATIONS, 
    AND WARRANTIES INCLUDING, WITHOUT LIMITATION, ANY IMPLIED WARRANTY OR CONDITION OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
    NON- INFRINGEMENT, SATISFACTORY QUALITY, NON-INTERFERENCE, AND ACCURACY, ARE HEREBY EXCLUDED AND EXPRESSLY DISCLAIMED BY CISCO. 
    CISCO DOES NOT WARRANT THAT THE SAMPLE CODE IS SUITABLE FOR PRODUCTION OR COMMERCIAL USE, WILL OPERATE PROPERLY, IS ACCURATE OR COMPLETE,
    OR IS WITHOUT ERROR OR DEFECT.

    GENERAL: This License shall be governed by and interpreted in accordance with the laws of the State of California, excluding its conflict 
    of laws provisions. You agree to comply with all applicable United States export laws, rules, and regulations. If any provision of this 
    License is judged illegal, invalid, or otherwise unenforceable, that provision shall be severed and the rest of the License shall remain 
    in full force and effect. No failure by Cisco to enforce any of its rights related to the Sample Code or to a breach of this License in a 
    particular situation will act as a waiver of such rights. In the event of any inconsistencies with any other terms, this License shall 
    take precedence.
"""

read_me = """Python 3 script to find clients with a specified string in their name,
    MAC or IP, and print their network usage statistics.

Script syntax:
    python find_clients.py -k <api key> [ -o <org name> -n <net filter>
        -c <client filter> -t <timespan>]
        
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

Required Python 3 modules:
    requests
    
To install these Python 3 modules via pip you can use the following commands:
    pip install requests
    
Depending on your operating system and Python environment, you may need to use commands 
    "python3" and "pip3" instead of "python" and "pip".
"""

import sys, getopt, time, datetime

from urllib.parse import urlencode
from requests import Session, utils
import pandas as pd
import os
from alive_progress import alive_bar, alive_it

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class NoRebuildAuthSession(Session):
    def rebuild_auth(self, prepared_request, response):
        """
        This method is intentionally empty. Needed to prevent auth header stripping on redirect. More info:
        https://stackoverflow.com/questions/60358216/python-requests-post-request-dropping-authorization-header
        """

API_MAX_RETRIES         = 3
API_CONNECT_TIMEOUT     = 60
API_TRANSMIT_TIMEOUT    = 60
API_STATUS_RATE_LIMIT   = 429

#Set to True or False to enable/disable console logging of sent API requests
FLAG_REQUEST_VERBOSE    = False

#Modify to customise what to print in tables when a field is None/empty
BLANK_FIELD             = ""

API_BASE_URL            = "https://api.meraki.com/api/v1"


def merakiRequest(p_apiKey, p_httpVerb, p_endpoint, p_additionalHeaders=None, p_queryItems=None, 
        p_requestBody=None, p_verbose=False, p_retry=0):
    #returns success, errors, responseHeaders, responseBody
    
    if p_retry > API_MAX_RETRIES:
        if(p_verbose):
            print("ERROR: Reached max retries")
        return False, None, None, None

    bearerString = "Bearer " + p_apiKey
    headers = {"Authorization": bearerString}
    if not p_additionalHeaders is None:
        headers.update(p_additionalHeaders)
        
    query = ""
    if not p_queryItems is None:
        query = "?" + urlencode(p_queryItems)
    url = API_BASE_URL + p_endpoint + query
    
    verb = p_httpVerb.upper()
    
    session = NoRebuildAuthSession()

    try:
        if(p_verbose):
            print(verb, url)
        if verb == "GET":
            r = session.get(
                url,
                headers =   headers,
                timeout =   (API_CONNECT_TIMEOUT, API_TRANSMIT_TIMEOUT)
            )
        elif verb == "PUT":
            if not p_requestBody is None:
                if (p_verbose):
                    print("body", p_requestBody)
                r = session.put(
                    url,
                    headers =   headers,
                    json    =   p_requestBody,
                    timeout =   (API_CONNECT_TIMEOUT, API_TRANSMIT_TIMEOUT)
                )
        elif verb == "POST":
            if not p_requestBody is None:
                if (p_verbose):
                    print("body", p_requestBody)
                r = session.post(
                    url,
                    headers =   headers,
                    json    =   p_requestBody,
                    timeout =   (API_CONNECT_TIMEOUT, API_TRANSMIT_TIMEOUT)
                )
        elif verb == "DELETE":
            r = session.delete(
                url,
                headers =   headers,
                timeout =   (API_CONNECT_TIMEOUT, API_TRANSMIT_TIMEOUT)
            )
        else:
            return False, None, None, None
    except:
        return False, None, None, None
    
    if(p_verbose):
        print(r.status_code)
    
    success         = r.status_code in range (200, 299)
    errors          = None
    responseHeaders = None
    responseBody    = None
    
    if r.status_code == API_STATUS_RATE_LIMIT:
        if(p_verbose):
            print("INFO: Hit max request rate. Retrying %s after %s seconds" % (p_retry+1, r.headers["Retry-After"]))
        time.sleep(int(r.headers["Retry-After"]))
        success, errors, responseHeaders, responseBody = merakiRequest(p_apiKey, p_httpVerb, p_endpoint, p_additionalHeaders, 
            p_queryItems, p_requestBody, p_verbose, p_retry+1)
        return success, errors, responseHeaders, responseBody        
            
    try:
        rjson = r.json()
    except:
        rjson = None
        
    if not rjson is None:
        if "errors" in rjson:
            errors = rjson["errors"]
            if(p_verbose):
                print(errors)
        else:
            responseBody = rjson  

    if "Link" in r.headers:
        parsedLinks = utils.parse_header_links(r.headers["Link"])
        for link in parsedLinks:
            if link["rel"] == "next":
                if(p_verbose):
                    print("Next page:", link["url"])
                splitLink = link["url"].split("/api/v1")
                success, errors, responseHeaders, nextBody = merakiRequest(p_apiKey, p_httpVerb, splitLink[1], 
                    p_additionalHeaders=p_additionalHeaders, 
                    p_requestBody=p_requestBody, 
                    p_verbose=p_verbose)
                if success:
                    if not responseBody is None:
                        responseBody = responseBody + nextBody
                else:
                    responseBody = None
    
    return success, errors, responseHeaders, responseBody
    
def getOrganizations(p_apiKey):
    endpoint = "/organizations"
    success, errors, headers, response = merakiRequest(p_apiKey, "GET", endpoint, p_verbose=FLAG_REQUEST_VERBOSE)    
    return success, errors, headers, response
    
def getNetworks(p_apiKey, p_organizationId):
    endpoint = "/organizations/%s/networks" % p_organizationId
    success, errors, headers, response = merakiRequest(p_apiKey, "GET", endpoint, p_verbose=FLAG_REQUEST_VERBOSE)    
    return success, errors, headers, response
    
   
def getNetworkClients(p_apiKey, p_networkId, p_timespan):
    endpoint = "/networks/%s/clients" % p_networkId
    query = {"timespan": p_timespan}
    success, errors, headers, response = merakiRequest(p_apiKey, "GET", endpoint, p_queryItems=query, p_verbose=FLAG_REQUEST_VERBOSE)    
    return success, errors, headers, response
    
    

def killScript(reason=None):
    if reason is None:
        print(read_me)
    else:
        print("ERROR: %s" % reason)
    sys.exit(2)
    
    
def filterByKeyValue (array, key, value):
    queryStr = ""
    if not value is None:
        queryStr = str(value).lower()
    result = []
    if not array is None:
        for item in array:
            if isinstance(item[key], list):
                if queryStr in item[key]:
                    result.append(item)
            else:
                itemValue = ""
                if key in item:
                    if not item[key] is None:
                        itemValue = str(item[key]).lower()
                position = itemValue.find(queryStr)
                if position > -1:
                    result.append(item)
        
    return result
    
    
def deduplicateList (array):
    result = []
    for item in array:
        if not item in result:
            result.append(item)
    return result


def main(argv):
    arg_apiKey          = None
    arg_orgNameQuery    = ""
    arg_netQuery    = ""
    arg_clientQuery = ""
    arg_timespanDays    = 7
    arg_filename= "all_clients.csv"
    
    try:
        opts, args = getopt.getopt(argv, 'k:o:n:c:t:f:')
    except getopt.GetoptError:
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-k':
            arg_apiKey = arg
        if opt == '-o':
            arg_orgNameQuery = arg
        if opt == '-n':
            arg_netQuery = arg
        if opt == '-c':
            arg_clientQuery = arg
        if opt == '-t':
            arg_timespanDays = arg
        if opt == "-f":
            arg_filename = arg
            
    if arg_apiKey is None:
        killScript()     

    if arg_filename:
        extension = os.path.splitext(arg_filename)[1]
        if extension != ".csv":
            killScript("Output filename must contain '.csv' extension!")

        
    try:
        timespan = int(arg_timespanDays) * 86400
    except:
        killScript("Timespan must be integer")
        
    maxTimespan = 2678400
    if timespan < 1:
        timespan = 1
    if timespan > maxTimespan:
        timespan = maxTimespan
    
    success, errors, headers, rawOrgs = getOrganizations(arg_apiKey)        
    organizations = filterByKeyValue(rawOrgs, "name", arg_orgNameQuery)
    
    df = pd.DataFrame(columns=["Organization", "Organization ID", "Network", "Network ID", "Description", "Client ID", "User", "VLAN", "Named VLAN", "Switchport", "Adaptive Policy Group", "First Seen", "Last Seen", "Manufacturer", "OS", "Device Type Prediction", "Recent Device Serial", "Recent Device Name", "Recent Device Mac", "Recent Device Connection", "SSID", "Status", "Notes", "SM Installed", "Group Policy 8021x", "Mac Address", "IP Address", "IPv6", "IPv6 Local", "Up KB", "Down KB"])


    for org in organizations:
        orgHeaderNotPrinted = True
        success, errors, headers, rawNets = getNetworks(arg_apiKey, org["id"])
        networks  = filterByKeyValue(rawNets, "name", arg_netQuery)  
        networks += filterByKeyValue(rawNets, "tags", arg_netQuery)
        networks += filterByKeyValue(rawNets, "productTypes", arg_netQuery)
        networks  = deduplicateList(networks)

        with alive_bar(len(networks), dual_line=True, title=f'{bcolors.WARNING}Discovering Clients -> {bcolors.ENDC}{org["name"]}') as bar:
            for net in networks:
                bar.text = f'-> {bcolors.WARNING}Network: {bcolors.ENDC}{net["name"]}'

                netHeaderNotPrinted = True
                success, errors, headers, rawClients = getNetworkClients(arg_apiKey, net["id"], timespan)
                clients  = filterByKeyValue(rawClients, "description", arg_clientQuery)
                clients += filterByKeyValue(rawClients, "mac", arg_clientQuery)
                clients += filterByKeyValue(rawClients, "ip", arg_clientQuery)
                clients  = deduplicateList(clients)
                if len(clients) > 0:
                    for client in clients:                    
                        if (orgHeaderNotPrinted):
                            # print('\n\nResults for organization "%s" (%s):' % (org["name"], org["id"]))
                            orgHeaderNotPrinted = False
                        if (netHeaderNotPrinted):
                            # print ('\nNetwork "%s" (%s):' % (net["name"], net["id"]))
                            # print('%-32s %-18s %-16s %-13s %s' % ("Description", "Mac", "IP", "Up KB", "Down KB"))
                            netHeaderNotPrinted = False
                            
                        description = BLANK_FIELD
                        if "description" in client:
                            if not client["description"] is None:
                                descStr = str(client["description"])
                                if len(descStr) > 32:
                                    description = descStr[:29] + "..."
                                else: 
                                    description = descStr
                        
                        ip = BLANK_FIELD
                        if "ip" in client:
                            if not client["ip"] is None:
                                ip = client["ip"]

                        if "namedVlan" in client:
                            namedVlan = client['namedVlan']
                        else:
                            namedVlan = "N/A"

                        entry = pd.DataFrame.from_dict({
                                 "Organization": [org["name"]],
                                 "Organization ID":  [org["id"]],
                                 "Network": [net["name"]],
                                 "Network ID": [net["id"]],
                                 "Description": [description],
                                 "Mac Address": [client["mac"]],
                                 "IP Address": [ip],
                                 "Up KB": [client["usage"]["sent"]],
                                 "Down KB": [client["usage"]["recv"]],
                                 "Client ID": [client['id']],
                                 "User": [client['user']],
                                 "VLAN": [client["vlan"]],
                                 "Named VLAN": [namedVlan],
                                 "Switchport": [client['switchport']],
                                 "Adaptive Policy Group": [client['adaptivePolicyGroup']],
                                 "IPv6": [client['ip6']],
                                 "First Seen": [client['firstSeen']],
                                 "Last Seen": [client['lastSeen']],
                                 "Manufacturer": [client['manufacturer']],
                                 "OS": [client['os']],
                                 'Device Type Prediction': [client['deviceTypePrediction']],
                                 "Recent Device Serial": [client['recentDeviceSerial']],
                                 "Recent Device Name": [client['recentDeviceName']],
                                 "Recent Device Mac": [client['recentDeviceMac']],
                                 "Recent Device Connection": [client['recentDeviceConnection']],
                                 "SSID": [client['ssid']],
                                 "Status": [client['status']],
                                 "Notes": [client['notes']],
                                 "IPv6 Local": [client['ip6Local']],
                                 "SM Installed": [client['smInstalled']],
                                 "Group Policy 8021x": [client['groupPolicy8021x']]
                                })

                        df = pd.concat([df, entry], ignore_index=True)
                        
                        # print('%-32s %-18s %-16s %-13s %s' % (
                        #     description, 
                        #     client["mac"],
                        #     ip,
                        #     client["usage"]["sent"],
                        #     client["usage"]["recv"]))
                bar()
    dir_path = os.path.dirname(os.path.realpath(__file__))

    df.to_csv(arg_filename)
    print(f"{bcolors.BOLD}File Created at: {bcolors.HEADER}{os.path.join(dir_path, arg_filename)}{bcolors.ENDC}")

    
if __name__ == '__main__':
    main(sys.argv[1:])