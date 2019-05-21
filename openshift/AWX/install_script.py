#!/usr/bin/env python

"""
The script installs other a script as a custom script into AWX and creates an inventory in AWX based on the installed script.
It needs when AWX is deployed in OpenShift, and you want to have an inventory with OpenShift nodes.
In general, the installed script is https://raw.githubusercontent.com/Mad-ness/howto-pages/master/openshift/AWX/ocp-inventory.py.

Pay attention on the used environment variables. They need to access AWX.

The script creates or gets, if already exists, a few records in AWX to create an inventory in AWX. 
But the script does not have any information how to access to the hosts in the built inventory. Therefore
credentials should be created manually to start using the inventory.

The script might be run multiple times.
"""

import os
import sys
import argparse
import requests
from requests.auth import HTTPBasicAuth


try:
  from urllib3 import disable_warnings
  disable_warnings()
except:
  pass

try:
  import json
except:
  import simplejson as json


class BaseAPI(object):

  def __init__(self, endpoint, creds):
    self.endpoint = endpoint
    self.creds = creds
    while self.endpoint[-1] == '/': self.endpoint = self.endpoint[:-1]

  def downloadFile(self, url):
    resp = requests.get(url)
    result = ""
    for chunk in resp.iter_content(chunk_size=128):
      result = result + chunk
    return result

  def sendPOST(self, function, payload):
    headers = { 'Content-type': 'application/json' }
    constructed_url = "{0}{1}".format(self.endpoint, function)
    return requests.post(
      constructed_url, 
      auth = HTTPBasicAuth(self.creds[0], self.creds[1]), 
      headers = headers, 
      verify = False, 
      json = payload
    )

  def sendGET(self, function, payload):
    headers = { 'Content-type': 'application/json' }
    constructed_url = "{0}{1}".format(self.endpoint, function)
    return requests.post(
      constructed_url, 
      auth = HTTPBasicAuth(self.creds[0], self.creds[1]), 
      headers = headers, 
      verify = False, 
      data = payload
    )


class AwxAPI(BaseAPI):

  def createOrGet(self, function, function_params, params, get_params):
    resp = self.sendPOST(function, params)
    if resp.status_code not in [ 200, 201, 400 ]:
      raise Exception("Resp code {0}. Cannot create an instance of {1}. Message: {2}".format(resp.status_code, function, resp.text))
    elif resp.status_code == 400:
      while function[-1] == "/": function = function[:-1]
      get_url = "{0}?{1}".format(function, function_params)
      resp = self.sendGET(get_url, get_params)
      if resp.status_code not in [ 200, 201 ]:
        raise Exception("Resp code {0}. Cannot get the list of instances {1}. Message: {2}".format(resp.status_code, get_url, resp.text))
      j = resp.json()
      if int(j.get('count')) == 0:
        raise Exception("Required instance not found {0}".format(get_params))
      instance_id = (j.get('results')[0]).get('id')
    else:
      instance_id = resp.json().get('id')
    return instance_id

  def createInventory(self, source):
    """
    Uploads inventory script into AWX.
    If source starts as http(s):// then it tries to download the script from source.
    If source starts as "/" it looks up a source file on a local drive, 
    source is considered as a path to a file
    """

    #
    # Step 1. Creating the inventory_script
    #
    payload = ""
    description = ""
    if source.startswith("./"): source = source[2:]
    if source.split(":", 1)[0] in [ "http", "https", "ftp", "ftps" ]:
      payload = self.downloadFile(source)
      description = "Downloaded from {0}".format(source)
    elif os.path.isfile(source):
      try:
        payload = open(source, 'r').read()
      except IOError:
        print("Cannot read the source from a local file {0}".format(source))
        exit(1)
      description = "From local file {0}".format(source)
    else:
      raise Exception("Don't known how to obtain the source {0}".format(source))

    script_name = source.split('/')[-1]
    script_id = self.createOrGet(
      "/api/v2/inventory_scripts/",
      "name={0}".format(script_name),
      {
        "name": script_name,
        "description": description,
        "script": payload,
        "organization": "1"
      },
      {
        "organization": "1",
        "script": script_name
      }
    )
  
    if script_id == None:
      raise Exception("Coudn't create or get the needed script {0}".format(script_name))

    #
    # Step 2. Creating the inventory
    #
    inventory_name = "Underlying OpenShift Cluster"
    inventory_id = self.createOrGet(
      "/api/v2/inventories/",
      "name={0}".format(inventory_name),
      {
        "name": inventory_name,
        "description": "Includes nodes of the OpenShift cluster where the AWX is run",
        "organization": "1",
        "kind": ""
      },
      {
        "organization": "1",
        "script": script_name
      }
    )
  
    if inventory_id == None:
      raise Exception("Coudn't create or get the needed inventory {0}".format(inventory_name))

    #
    # Step 3. Creating the inventory_source
    #
    inventory_source_name = script_name
    inventory_source_id = self.createOrGet(
      "/api/v2/inventory_sources/",
      "name={0}".format(inventory_source_name),
      {
        "name": inventory_source_name,
        "description": "Created automatically by a smart person",
        "source": "custom",
        "source_script": script_id,
        "update_on_launch": 1,
        "update_cache_timeout": 3600,
        "inventory": inventory_id
      },
      {
      }
    )
  
    if inventory_id == None:
      raise Exception("Coudn't create or get the needed inventory_source {0}".format(inventory_source_name))
    
    print("Inventory_source created, id={0}".format(inventory_source_id))
  pass



awx_endpoint = os.environ.get("AWX_ENDPOINT")
awx_username = os.environ.get("AWX_USERNAME")
awx_password = os.environ.get("AWX_PASSWORD")
awx_script_source = os.environ.get("AWX_SCRIPT_SOURCE", "https://raw.githubusercontent.com/Mad-ness/howto-pages/master/openshift/AWX/ocp-inventory.py")


AwxAPI(endpoint=awx_endpoint, creds=( awx_username, awx_password )).createInventory( awx_script_source )

