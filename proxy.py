from flask import Flask, jsonify, request

# job launch
from datetime import datetime
import subprocess
app = Flask(__name__)

nodes = []
jobs = []
pods = {}

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
                if name == node['name']:
                    print('Node already exists: ' + node['name'] + 'with status' + node['status'])
                    result = 'already_exists'
                    node_status = node['status']
            if result == 'unknown' and node_status == 'unknown':
                result = 'node_added'
                pods['default'].append({'name': name, 'status': 'Idle'})
                # job launch
                nodes.append({'name': name, 'status': 'Idle', 'log_file': {}})
                node_status = 'Idle'
                print('Successfully added a new node: ' + str(name))
            return jsonify({'result': result, 'node_status': node_status, 'node_name': name, 'pod_name': 'default'})
        elif pod_name in pods:
            for node in pods[str(pod_name)]:
                if name == node['name']:
                    print('Node already exists: ' + node['name'] + 'with status' + node['status'])
                    result = 'already_exists'
                    node_status = node['status']
            if result == 'unknown' and node_status == 'unknown':
                result = 'node_added'
                pods[str(pod_name)].append({'name': name, 'status': 'Idle'})
                # job launch
                nodes.append({'name': name, 'status': 'Idle', 'log_file': {}})
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
            default_nodes.append({'name': ('default' + str(i)), 'status': 'Idle'})
            # job launch
            nodes.append({'name': ('default' + str(i)), 'status': 'Idle', 'log_file': {}})
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
            if name == node['name']:
                if name.startswith('default'):
                    result = 'cannot remove default nodes'
                    return jsonify({'result': result})
                # correction (resolved)
                if node['status'] == 'Idle':
                    nodes.remove(node)
                    result = 'node is removed'
                    return jsonify({'result': result})
        result = 'removal failed either name not exists or status not Idle'
        return jsonify({'result': result})

# Launch Jobs
@app.route('/cloudproxy/jobs/launch/')
def cloud_launch(file_path):
    if request.method == 'POST':
        print('request to post a job: ' + str(file_path))
        # Create new job
        now = datetime.now()
        d1 = now.strftime("%d/%m/%Y>%H:%M:%S")
        JID = file_path + d1
        # Q1 Job structure
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
                print(JID)
                # Q2 How to run
                process = subprocess.Popen(['sh', file_path], stdout=subprocess.PIPE)
                new_job['process'] = process
                new_job['status'] = 'Completed'
                node['status'] = 'Idle'
                # Q3 How to direct output
                node['log_file'][JID] = None
                # Q4 How to connect to proxy
                # Q5 How to clear the queue
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
                job['node'] = None
                return jsonify({'result': 'Success'})
    return jsonify({'result': 'Failure'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6000)
