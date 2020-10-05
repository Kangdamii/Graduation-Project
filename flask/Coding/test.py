import requests
import json


url = 'http://192.168.0.96:8080/client/api'
def getLoginStatus():
    login_data = {'command':'login', 'username':'kamila', 'password': '123456', 'response':'json'}
    global user
    user = requests.Session()
    req = user.post(url, data=login_data)
    # print(req.json())
    global status
    status = req.status_code
    return status
def deploy():
    deploy_vm_data = {'command': 'deployVirtualMachine', 'serviceofferingid' : '6cef2eac-178d-4c6e-aee7-7172ef679894','templateid':'a7c7dd79-43d0-41b9-b91f-8a95b315a3ac','zoneid':'3f6a71a7-b5f8-4a10-aa2d-354b7b2bf7c5','response':'json'}
    global user
    req_dep_vm = user.post(url,data=deploy_vm_data)
    resp = req_dep_vm.json()
    res1 = resp['deployvirtualmachineresponse']
    res2 = res1 ['id']
    print(res2)
    return res2
def getVMIp():
    id = deploy()
    vm_data = {'command': 'listVirtualMachines', 'id' : id, 'response':'json'}
    global user
    req_vm = user.post(url,data=vm_data)
    resp = req_vm.json()
    res = resp['listvirtualmachinesresponse']
    res1 = res['virtualmachine']
    # print(res1[])
    res2 = res1[0]
    res3 = res2['nic']
    # print(res3)
    res4 = res3[0]
    res5 = res4['ipaddress']
    print(res5)
    # res2 = res1['nic']
    # res_ip = res2['ipaddress']
    # print(res_ip)
    # return print(res1)
    
def getState():
    vm_data = {'command': 'listVirtualMachines', 'id' : 'ed03d644-a971-4b92-825f-6d8e7d3cb5c8','response':'json'}
    global user
    req_vm = user.post(url,data=vm_data)
    resp = req_vm.json()
    res = resp['listvirtualmachinesresponse']
    res1 = res['virtualmachine']
    res1 = res1[0]
    print(res1['state'])



getLoginStatus()
# deploy()
getVMIp()
# getState()
