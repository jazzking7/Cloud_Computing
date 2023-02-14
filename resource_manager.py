from flask import Flask, jsonify, request, render_template
import pycurl
import json
from io import BytesIO

cURL = pycurl.Curl()
proxy_url = 'http://192.168.2.14:6000/'

app = Flask(__name__)

# render page
@app.route('/', methods=['GET'])
def render_page():
    data = BytesIO()
    cURL.setopt(cURL.URL, proxy_url + 'get_data')
    cURL.setopt(cURL.WRITEFUNCTION, data.write)
    cURL.perform()
    data = json.loads(data.getvalue())
    return render_template("index.html", data=data)


@app.route('/', methods=['GET', 'POST'])
def cloud():
    if request.method == 'GET':
        print('A Client says hello')
        response = 'Cloud says hello'
        return jsonify({'response': response})


@app.route('/cloud/nodes/<name>', defaults={'pod_name': 'default'})
@app.route('/cloud/nodes/<name>/<pod_name>')
def cloud_register(name, pod_name):
    if request.method == 'GET':
        print('Request to register new node: ' + str(name) + ' on pod: ' + str(pod_name))
        ## TO: for future assignment: management for pod_name
        ## todo : logic for invoking PM-proxy

        ## TO: call proxy to register node
        data = BytesIO()
        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/nodes/' + str(name) + '/' + str(pod_name))
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())
        print(dictionary)

        result = dictionary['result']
        node_status = dictionary['node_status']
        new_node_name = dictionary['node_name']
        new_node_pod = dictionary['pod_name']
        
        render_page()
        
        return jsonify({'result': result, 'node_status': node_status, 'new_node_name': new_node_name,
                        'new_node_pod': new_node_pod})


@app.route('/cloud/pods/')
def cloud_init():
    if request.method == 'GET':
        print('request to initialize the cloud')
        data = BytesIO()
        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/pods/')
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())
        print(dictionary)

        result = dictionary['result']
        new_node_pod = 'default'
        return jsonify({'result': result})


@app.route('/cloud/pods/<pod_name>')
def cloud_pod_register(pod_name):
    if request.method == 'GET':
        print('request to register a new pod')
        data = BytesIO()
        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/pods/' + str(pod_name))
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())
        print(dictionary)

        result = dictionary['result']
        return jsonify({'result': result})


@app.route('/cloud/pods/<pod_name>/rm/')
def cloud_pod_rm(pod_name):
    print("this is the debug")
    if request.method == 'GET':
        print('request to remove a pod')
        data = BytesIO()
        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/pods/' + str(pod_name) + '/rm/')
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())

        print(dictionary)
        result = dictionary['result']
        return jsonify({'result': result})


@app.route('/cloud/nodes/<name>/rm/')
def cloud_rm(name):
    if request.method == 'GET':
        print('request to remove a node')
        data = BytesIO()
        cURL.setopt(cURL.URL, proxy_url + '/cloudproxy/nodes/' + str(name) + '/rm/')
        cURL.setopt(cURL.WRITEFUNCTION, data.write)
        cURL.perform()
        dictionary = json.loads(data.getvalue())

        print(dictionary)
        result = dictionary['result']
        return jsonify({'result': result})

# Launch Jobs
@app.route('/cloud/jobs/launch', methods=["POST"])
def cloud_launch():
    if request.method == 'POST':
        print("Client is posting a file")
        job_file = request.files["files"]
        # proxy

        print(job_file.read())
        result = "Success"
        return jsonify({'result': result})


@app.route('/cloud/jobs/abort')
def cloud_abort(JID):
    if request.method == 'GET':
        print('request to abort job')
        data = BytesIO()
    return

@app.route('/cloud/pods')
def cloud_pod_ls():
    if request.method == 'GET':
        print("Cloud is listing its pods")
        data=BytesIO()
    return

@app.route('/cloud/pods')
def cloud_node_ls(res_pod_ID):
    if request.method == 'GET':
        print('Cloud is listing nodes')
        data=BytesIO()
    return

@app.route('/cloud/jobs')
def cloud_job_ls(node_ID):
    if request.method=='GET':
        print('Cloud is listing jobs')
        data=ByteIO()
    return
@app.route('/cloud/jobs')
def cloud_job_log(job_ID):
    if request.method=='GET':
        print('Cloud is listing log files of the job')
        data=ByteIO()
    return
@app.route('/cloud/nodes')
def cloud_log_node(node_ID):
    if request.method=='GET':
        print('Cloud is listing the log file of the node')
        data=ByteIO()
    return

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
