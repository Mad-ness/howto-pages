#!/usr/bin/env python

import os
import sys
import argparse
import requests
from urllib3 import disable_warnings


disable_warnings()

try:
  import json
except:
  import simplejson as json

class BaseAPI(object):
 
  def __init__(self, endpoint, token):
    self.endpoint = endpoint
    while self.endpoint[-1] == '/': self.endpoint = self.endpoint[:-1]
    self.token = token
  
  def get(self, function):
    headers = {
      'Accept': 'application/json',
      'Authorization': 'Bearer {0}'.format(self.token)
    }
    constructed_url = "{0}{1}".format(self.endpoint, function)
    return requests.get(constructed_url, headers=headers, verify=False)


class NodeAPI(BaseAPI):

  def getNodes(self):
    nodes = {}
    groups = {}
    resp = self.get('/api/v1/nodes')
    if resp.status_code in [ 200, ]:
      nodes_details = resp.json().get("items")
      for node_detail in nodes_details:
        metadata = node_detail.get('metadata')
        labels = metadata.get('labels')

        nodes[labels.get('kubernetes.io/hostname')] = {
          'labels': labels,
          'ansible_ssh_host': [ 
            pair.get('address') for pair in (node_detail.get('status').get('addresses')) if pair.get('type') == 'InternalIP' 
          ][0]
        }

        # Placing the hosts into groups
        # Groups names are taken from label "node-role.kubernetes.io/***"
        for label in labels:
          group_name = 'ungroupped'
          # Supposing that role names are "node-role.kubernetes.io/master", 
          # "node-role.kubernetes.io/compute", and "node-role.kubernetes.io/infra"
          if label.startswith("node-role.kubernetes.io/") and len(label) > len("node-role.kubernetes.io/"):
            group_name = label.split('/')[1] + 's'

            if groups.get(group_name):
              groups[group_name]['hosts'].append(labels.get('kubernetes.io/hostname'))
            else:
              groups[group_name] = { 
                'hosts': [ labels.get('kubernetes.io/hostname'), ]
              }
    
    return groups, nodes

class OpenShiftInventory(object):
  def __init__(self, endpoint, token):
    self.endpoint, self.token = endpoint, token
    self.inventory = {}
    self.read_cli_args()

    if self.args.list:
      self.inventory = self.get_inventory()
  
    elif self.args.host:
      self.inventory = ((self.get_inventory().get('_meta')).get('hostvars')).get(self.args.host)
      if self.inventory == None:
        self.inventory = self.empty_inventory()

    else:
      self.inventory = self.empty_inventory()

    print(json.dumps(self.inventory, indent=4))

  def empty_inventory(self): return { '_meta': { 'hostvars': {}}}
    
  def get_inventory(self):
    api = NodeAPI(endpoint=self.endpoint, token=self.token)
    groups, hosts = api.getNodes()
    inv = groups
    inv['_meta'] = {
      'hostvars': hosts
    }
    return inv

  def read_cli_args(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host', action='store')
    self.args = parser.parse_args()
  pass

#
# It's better to create a service account and give to it permissions (roles) to
# perform "get" operation on "nodes" and put here its token
#
OpenShiftInventory(endpoint="https://kubernetes.default.svc", token="your-token")

