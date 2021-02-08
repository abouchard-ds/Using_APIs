# -*- coding: utf-8 -*-
"""
Created on Fri Feb  5 2021

@author: alexandre.bouchard
"""
import requests
import pandas as pd

# pas besoin, mais requests spam des warnings.
import urllib3
urllib3.disable_warnings()

# chaque data sera ecrit dans Excel.
dropExcelFiles = True

# parametres
# c'est ici qu'on met ca dans un dictionnary/json
# et on peut configurer de poll tous les vcenter de Bell

usr = "username"
pwd = "password"
vcenterURL = "https://vcenter"

# pour chaque vCenter
def get_token(username, password, endpointBaseURL):
    
    authURL = endpointBaseURL + "/rest/com/vmware/cis/session"

    response = requests.post(authURL, auth=(username, password), verify=False)
    
    if response.ok:
        return response.json()['value']
    else:
        return None

# obtenir et stocker le token
access_token = get_token(usr,pwd,vcenterURL)

# --------------------------------------------------------
#                    VMs list
# --------------------------------------------------------
reponse = requests.get(vcenterURL + "/rest/vcenter/vm", verify=False, headers={"vmware-api-session-id": access_token})
dfvm = pd.DataFrame(reponse.json()['value'])

# --------------------------------------------------------
#                    VMs details
# --------------------------------------------------------

dfvmdetail = pd.DataFrame()
templist = []
for vm in dfvm['vm']:
    
    reponse = requests.get(vcenterURL + "/rest/vcenter/vm/" + vm, verify=False, headers={"vmware-api-session-id": access_token})
    
    c = reponse.json()
    c['value']['vm'] = vm

    templist.append(c)

v = pd.json_normalize(templist)
dfvmdetail = v

if dropExcelFiles:
    dfvmdetail.to_excel("vCenter_API_VMdetails.xlsx", index=False)

# --------------------------------------------------------
#                    guests/identity
# --------------------------------------------------------
dfguests = pd.DataFrame()
templist = []
for vm in dfvm['vm']:
    
    reponse = requests.get(vcenterURL + "/rest/vcenter/vm/" + vm + "/guest/identity", verify=False, headers={"vmware-api-session-id": access_token})
    
    c = reponse.json()
    c['value']['vm'] = vm

    templist.append(c)

v = pd.json_normalize(templist)
dfguests = v

del(c,v)
if dropExcelFiles:
    dfguests.to_excel("vCenter_API_Identities.xlsx", index=False)


# --------------------------------------------------------
#                    guests/local filesystem
# --------------------------------------------------------
# donne la taille des disque dans l'OS

# reponse = requests.get(vcenterURL + "/rest/vcenter/vm/" + vm + "/guest/local-filesystem", verify=False, headers={"vmware-api-session-id": access_token})
# {'value': [{'value': {'free_space': 3796189184, 'capacity': 5358223360},
#    'key': '/usr'},
#   {'value': {'free_space': 1787240448, 'capacity': 2136997888}, 'key': '/opt'},
#   {'value': {'free_space': 338014208, 'capacity': 520785920}, 'key': '/boot'},
#   {'value': {'free_space': 5319311360, 'capacity': 5358223360},
#    'key': '/var/log'},
#   {'value': {'free_space': 10692870144, 'capacity': 10726932480},
#    'key': '/home'},
#   {'value': {'free_space': 5323653120, 'capacity': 5358223360},
#    'key': '/var/log/audit'},
#   {'value': {'free_space': 5284622336, 'capacity': 5358223360}, 'key': '/'},
#   {'value': {'free_space': 2103107584, 'capacity': 2136997888}, 'key': '/tmp'},
#   {'value': {'free_space': 4262830080, 'capacity': 5358223360},
#    'key': '/var'}]}


# --------------------------------------------------------
#                     vm / hardware / disk
# --------------------------------------------------------
dfvmdisk = pd.DataFrame()
for vm in dfvm['vm']:
    
    reponse = requests.get(vcenterURL + "/rest/vcenter/vm/" + vm + "/hardware/disk", verify=False, headers={"vmware-api-session-id": access_token})
    
    # vm name dans le json
    # optimiser ca pour append les reponse ensemble sans traitement
    # puis faire le traitement a la fin
    c = pd.json_normalize(reponse.json(), 'value')
    c['vm'] = vm
    dfvmdisk = dfvmdisk.append(c, ignore_index=True)
del(c)

# details par disques
#'{"value":{"scsi":{"bus":0,"unit":1},"backing":{"vmdk_file":"[DS-MTRL-NIMBLE-FC-01] BL3C2S/BL3C2S_1.vmdk","type":"VMDK_FILE"},"label":"Hard disk 2","type":"SCSI","capacity":26843545600}}'
dfdisk = pd.DataFrame()
for index, row in dfvmdisk.iterrows():
   
    reponse = requests.get(vcenterURL + "/rest/vcenter/vm/" + row['vm'] + "/hardware/disk/" + row['disk'], verify=False, headers={"vmware-api-session-id": access_token})
    
    x = {'vm':row['vm'],
         'disk':row['disk'], 
         'vmdk_file':reponse.json()['value']['backing']['vmdk_file'],
         'file_type':reponse.json()['value']['backing']['type'],
         'disk_type':reponse.json()['value']['type'],
         'disk_capacity':reponse.json()['value']['capacity']}
                                   
    dfdisk = dfdisk.append(x, ignore_index=True)
del(x)

# join disk data to vmdata
diskfinal = pd.merge(dfvm, dfdisk, on=['vm'])

if dropExcelFiles:
    diskfinal.to_excel("vCenter_API_Disks.xlsx", index=False)


# --------------------------------------------------------
#              datastore list et get
# --------------------------------------------------------
reponse = requests.get(vcenterURL + "/rest/vcenter/datastore", verify=False, headers={"vmware-api-session-id": access_token})
dfdstore = pd.json_normalize(reponse.json(), 'value')

dfdstoredetails = pd.DataFrame()
for dstore in dfdstore['datastore']:
    
    reponse = requests.get(vcenterURL + "/rest/vcenter/datastore/" + dstore, verify=False, headers={"vmware-api-session-id": access_token})
    dfdstoredetails = dfdstoredetails.append(reponse.json()['value'], ignore_index=True)


dstorefinal = pd.merge(dfdstore, dfdstoredetails, on=['name'])

if dropExcelFiles:
    dstorefinal.to_excel("vCenter_API_Dstore.xlsx", index=False)

# --------------------------------------------------------
#                          folder
# --------------------------------------------------------
reponse = requests.get(vcenterURL + "/rest/vcenter/folder", verify=False, headers={"vmware-api-session-id": access_token})
dffolder = pd.json_normalize(reponse.json(), 'value')

if dropExcelFiles:
    dffolder.to_excel("vCenter_API_Folder.xlsx", index=False)

# --------------------------------------------------------
#                          network
# --------------------------------------------------------
reponse = requests.get(vcenterURL + "/rest/vcenter/network", verify=False, headers={"vmware-api-session-id": access_token})
dfnetwork = pd.json_normalize(reponse.json(), 'value')

if dropExcelFiles:
    dfnetwork.to_excel("vCenter_API_Network.xlsx", index=False)

# --------------------------------------------------------
#                          hosts
# --------------------------------------------------------
reponse = requests.get(vcenterURL + "/rest/vcenter/host", verify=False, headers={"vmware-api-session-id": access_token})
dfhost = pd.json_normalize(reponse.json(), 'value')

if dropExcelFiles:
    dfhost.to_excel("vCenter_API_Host.xlsx", index=False)
