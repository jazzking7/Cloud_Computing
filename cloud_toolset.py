import pycurl
import sys
import os
import requests

cURL = pycurl.Curl()

def cloud_hello(url):
    cURL.setopt(cURL.URL, url)
    cURL.perform()


def cloud_register(url, command):
    command_list = command.split()
    if len(command_list) == 3:
        cURL.setopt(cURL.URL, url + '/cloud/nodes/' + command_list[2])
        cURL.perform()
    elif len(command_list) == 4:
        cURL.setopt(cURL.URL, url + '/cloud/nodes/' + command_list[2] + '/' + command_list[3])
        cURL.perform()


def cloud_init(url):
    cURL.setopt(cURL.URL, url + '/cloud/pods/')
    cURL.perform()


def cloud_pod_register(url, command):
    command_list = command.split()
    cURL.setopt(cURL.URL, url + '/cloud/pods/' + command_list[3])
    cURL.perform()


def cloud_pod_rm(url, command):
    command_list = command.split()
    cURL.setopt(cURL.URL, url + '/cloud/pods/' + command_list[3] + '/rm/')
    cURL.perform()


def cloud_rm(url, command):
    command_list = command.split()
    cURL.setopt(cURL.URL, url + '/cloud/nodes/' + command_list[2] + '/rm/')
    cURL.perform()

# Launch Jobs
def cloud_launch(url, command):
    command_list = command.split()
    if len(command_list) == 3:
        file_path = command_list[2]
        if os.path.isfile(file_path):
            files = {'Files': open(file_path, 'rb')}
            ret = requests.post(url+'/cloud/jobs/launch', files=files)
            print(ret.text)

def cloud_abort(url, command):
    command_list = command.split()
    if len(command_list) == 3:
        JID = command_list[2]
        cURL.setopt(cURL.URL, url + '/cloud/jobs/abort' + command_list[2])
        cURL.perform()
        
def cloud_pod_ls(url, command):
    command_list = command.split()
    if len(command_list) == 3:
        cURL(cURL.URL, url+'/cloud/pods')
        cURL.perform()
        
def cloud_node_ls(url, command):
    command_list = command.split()
    if len(command_list)==4:
        res_pod_ID = command_list[3]
        cURL(cURL.URL, url+'/cloud/pods'+command_list[3])
        cURL.perform()
        
def cloud_job_ls(url,command):
    command_list = command.split()
    if len(command_list)==4:
        node_ID=command_list[3]
        cURL(cURL.URL, url+ '/cloud/jobs/'+command_list[3])
        cURL.perform()
        
def cloud_job_log(url,command):
    command_list = command.split()
    if len(command_list)==4:
        cURL(cURL.URL, url+'/cloud/jobs/'+command_list[3])
        cURL.perform()
        
def cloud_node_log(url,command):
    command_list = command.split()
    if len(command_list)==4:
        cURL(cURL.URL, url+'/cloud/nodes/'+command_list[3])
        cURL.perform()
        
def main():
    rm_url = sys.argv[1]
    while (1):
        command = input('$ ')
        if command == 'cloud hello':
            cloud_hello(rm_url)
        elif command == 'exit':
            exit()
        elif command.startswith('cloud register'):
            cloud_register(rm_url, command)
        elif command == 'cloud init':
            cloud_init(rm_url)
        elif command.startswith('cloud pod register'):
            cloud_pod_register(rm_url, command)
        elif command.startswith('cloud pod rm'):
            cloud_pod_rm(rm_url, command)
        elif command.startswith('cloud rm'):
            cloud_rm(rm_url, command)
        # Launch Jobs
        elif command.startswith("cloud launch"):
            cloud_launch(rm_url, command)
        elif command.startswith("cloud abort"):
            cloud_abort(rm_url, command)


if __name__ == '__main__':
    main()
