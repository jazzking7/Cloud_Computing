from flask import Flask, jsonify, request
import docker
from threading import Thread, Lock

client = docker.from_env()

lock = Lock()

# job launch
from datetime import datetime
import subprocess
app = Flask(__name__)


nodes = []
jobs = []
pods = {}

# render page
@app.route('/get_data')
def get_data():
    names = []
    status = []
    for node in nodes:
        names.append(node.name)
        status.append(node.status)
    return jsonify(names, status)


@app.route('/cloudproxy/nodes/<name>/<pod_name>')
def cloud_register(name, pod_name):
    if request.method == 'GET':
        print('request to register new node: ' + str(name))
        result = 'unknown'
        node_status = 'unknown'
        if name.startswith('default'):
            print('cannot add node with name starts with "default"')
            result = 'add node failed, choose a new name'
            return jsonify({'result': result, 'node_status': node_status, 'node_name': name, 'pod_name': 'default'})
        if len(pod_name) == 0:
            for node in pods['default']:
                if name == node.name:
                    print('Node already exists: ' + node.name + 'with status' + node.status)
                    result = 'already_exists'
                    node_status = node.status
            if result == 'unknown' and node_status == 'unknown':
                result = 'node_added'
                ## here thee nodes are added in form of containers
                ## with no job waiting in the list
                if len(jobs) == 0:
                    temp_container = client.containers.create('alpine', detach = True, name = name)
                    pods['default'].append(temp_container)
                    nodes.append(temp_container)
                ## if there are jobs waiting, we create mutex lock
                ## ATTENTION: i passed the job[0] as the file need to run when i created the new container
                else:
                    lock.acquire()
                    temp_container = client.containers.create('alpine', jobs[0], detach = True, name = name)
                    pods['default'].append(temp_container)
                    nodes.append(temp_container)
                    jobs.pop(0)
                    lock.release()

                node_status = 'Idle'
                print('Successfully added a new node: ' + str(name))
            return jsonify({'result': result, 'node_status': node_status, 'node_name': name, 'pod_name': 'default'})
       ##################
        elif pod_name in pods:
            for node in pods[str(pod_name)]:
                if name == node.name:
                    print('Node already exists: ' + node.name + 'with status' + node.status)
                    result = 'already_exists'
                    node_status = node.status
            if result == 'unknown' and node_status == 'unknown':
                result = 'node_added'
                ## here thee nodes are added in form of containers
                ## with no job waiting in the list
                if len(jobs) == 0:
                    temp_container = client.containers.create('alpine', detach = True, name = name)
                    nodes.append(temp_container)
                    pods[pod_name].append(temp_container)
                ## if there are jobs waiting, we create mutex lock
                ## ATTENTION: i passed the job[0] as the file need to run when i created the new container
                else:
                    lock.acquire()
                    temp_container = client.containers.create('alpine', jobs[0], detach = True, name = name)
                    pods[pod_name].append(temp_container)
                    nodes.append(temp_container)
                    jobs.pop(0)
                    lock.release()

                node_status = 'Idle'
                print('Successfully added a new node: ' + str(name))

            return jsonify({'result': result, 'node_status': node_status, 'node_name': name, 'pod_name': pod_name})
        else:
            result = "failed to add the node to the non-existing pod"
            print(str(pod_name) + ' (pod) does not exist, cannot add node to it.')

            node_status = 'unknown'
            return jsonify({'result': result, 'node_status': node_status, 'node_name': name, 'pod_name': pod_name})


@app.route('/cloudproxy/pods/')
def cloud_init():
    if request.method == 'GET':
        default_nodes = []
        result = 'unknown'
        for i in range(40):
            temp_container = client.containers.create('alpine', detach = True, name = str('default' + str(i)))
            print(temp_container.name) ## = str('default' + str(i))
            print(temp_container.status) ## = 'Idle'
            default_nodes.append(temp_container)
            # job launch
            nodes.append(temp_container)
        pods['default'] = default_nodes
        result = 'initialized'
        ## under condition only one pod
        print('Successfully initialized default pods with 40 default nodes')
        return jsonify({'result': result})


@app.route('/cloudproxy/pods/<pod_name>')
def cloud_pod_register(pod_name):
    if request.method == 'GET':
        print('request to register new pod: ' + str(pod_name))
        result = 'unknown'
        if str(pod_name) in pods:
            result = 'pod name already exists'
        else:
            pods[str(pod_name)] = []
            result = 'new pod added'
            print('Successfully added a new pod: ' + str(pod_name))

        return jsonify({'result': result})


@app.route('/cloudproxy/pods/<pod_name>/rm/')
def cloud_pod_rm(pod_name):
    if request.method == 'GET':
        print('request to remove pod: ' + str(pod_name))
        result = 'unknown'
        if str(pod_name) not in pods:
            result = 'pod name does not exists'
        elif str(pod_name) == 'default':
            result = 'cannot remove default pod'
        elif len(pods[str(pod_name)]) != 0:
            result = 'pod has nodes registered to,cannot delete'
        else:
            del pods[str(pod_name)]
            result = 'pod is removed'
        return jsonify({'result': result})

@app.route('/cloudproxy/nodes/<name>/rm/')
def cloud_rm(name):
    if request.method == 'GET':
        print('request to remove node: ' + str(name))
        result = 'unknown'
        for node in nodes:
            if name == node.name:
                if name.startswith('default'):
                    result = 'cannot remove default nodes'
                    return jsonify({'result': result})
                # correction (resolved)
                if node.status == 'created':
                    nodes.remove(node)
                    node.remove()
                    result = 'node is removed'
                    return jsonify({'result': result})
        result = 'removal failed either name not exists or status not Idle'
        return jsonify({'result': result})

# Launch Jobs
@app.route('/cloudproxy/jobs/launch')
def cloud_launch(file_path):
    if request.method == 'POST':
        print('request to post a job: ' + str(file_path))
        # Create new job
        now = datetime.now()
        d1 = now.strftime("%d/%m/%Y>%H:%M:%S")
        JID = file_path + d1
        new_job = {"JID": JID, "status": "Registered",
                   "node": None, "process": None}
        launched = False
        jobs.append(new_job)
        for node in nodes:
            # found idle node
            if node['status'] == 'Idle':
                launched = True
                new_job['status'] = 'Running'
                new_job['node'] = node
                node['status'] = 'Running'
                node['log_file'].append(f"Started Executing {JID}")
                print(JID)
                # Run the job
                process = subprocess.Popen(['sh', file_path], stdout=subprocess.PIPE)
                new_job['process'] = process
                new_job['status'] = 'Completed'
                node['status'] = 'Idle'
                node['log_file'].append(f"Finished Executing {JID}")
        result = "Launched" if launched else "Failure"
        return jsonify({'result': result})

@app.route('/cloudproxy/jobs/')
def cloud_abort(JID):
    for job in jobs:
        if job['JID'] == job:
            if job['status'] == 'Registered':
                jobs.remove(job)
                return jsonify({'result': 'Success'})
            elif job['status'] == 'Running':
                job['process'].kill()
                job['status'] = 'Aborted'
                job['node']['status'] = 'Idle'
                return jsonify({'result': 'Success'})
    return jsonify({'result': 'Failure'})

@app.route('/cloudproxy/pods')
def could_pod_ls():
    for pod in pods:
        i = 0
        for node in pod:
            i =+ 1
        print(str(pod['name'])+":"+str(i)+"nodes")
    return jsonify({'result':'success'})

@app.route('/cloudproxy/pods')
def cloud_node_ls(res_pod_ID):
    result="unknown"
    if len(res_pod_ID)==0:
        for pod in pods:
            for node in pod:
                print(str(node.name) + str(node.status))
                result="success"
    elif str(res_pod_ID) not in pods:
        result="not such pod"
    else:
        for node in pods(str(res_pod_ID)):
            print(str(node.name)+str(node.status))
            result="success"
    return jsonify({'result':result})
                   
@app.route('/cloudproxy/jobs')
def cloud_job_ls(node_ID):
    if len(node_ID)==0:
        for job in jobs:
            print(str(job['name']+job['status']))
            return jsonify({'success'})
    else:
        i=0
        for job in jobs:
            if job['node']==str(node_ID):
                i=+1
                print(str(job['name'])+str(node_ID)+str(job['status']))
        if i==0:
            return jsonify({"result":"no such node"})
        else:
            return jsonify("success")
    
@app.route('/cloudproxy/jobs')
def cloud_job_log(job_ID):
    if len(job_ID)==0:
        return jsonify('command fails')
    else:
        for job in jobs:
            if job['JID']==str(job_ID):
                print(job['node'].log_file[JID])
                return jsonify({"result":"success"})
        return jsonify({"command fails"})
        
@app.route('/cloudproxy/nodes')
def cloud_log_node(node_ID):
    if len(node_ID)==0:
        return jsonify("command fails")
    else:
        for node in nodes:
            if node.name == str(node_ID):
                for item in node.log_file.values():
                    print(item)                
                return jsonify("success")
        return jsonify("command fails")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6000)
