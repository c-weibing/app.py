#!flask/bin/python
from flask import Flask, jsonify, request, abort, make_response
import subprocess, atexit

app = Flask(__name__)

flows = [
        {
                "id": 0,
                "priority": "Input Priority",
                "in_port": "Input In_Port",
                "output": "Input Output",
        }
]

#Not found
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'No such task'}), 404)

#Bad request
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': '1.priority/in_port/output field is missing. 2.in_port and priority value cannot be the same as existing. 3.Please input a valid integer. 4.Invalid id chosen (flow 0 cannot be edited)'}), 400)

#Read all flows in cli
@app.route('/todo/api/v1.0/readall/flowscli', methods=['GET'])
def get_flowscli():
    p = subprocess.Popen(["sudo", "ovs-ofctl", "dump-flows", "s1"], stdout=subprocess.PIPE)
    output, err = p.communicate()
    return output

#Read all flows in json
@app.route('/todo/api/v1.0/readall/flowsjson', methods=['GET'])
def get_flowsjson():
    return jsonify({'flows': flows})

#Read one flow
@app.route('/todo/api/v1.0/readone/<int:flow_id>', methods=['GET'])
def get_flow(flow_id):
    flow = [ flow for flow in flows if flow['id'] == flow_id]
    if len(flow) == 0:
            abort(404)
    return jsonify({'flows': flow[0]})

#Create flow
@app.route('/todo/api/v1.0/create/addflows', methods=['POST'])
def create_flow():
    #check priority,in_port,output 3 variables has be entered
    if not request.json or not 'priority' in request.json:
            abort(400)
    if not request.json or not 'in_port' in request.json:
            abort(400)
    if not request.json or not 'output' in request.json:
            abort(400)

    #check if they are all integers
    if 'priority' in request.json:
        try:
            priorityCheckInt = int(request.json['priority'])
        except ValueError:
            abort(400)

    if 'in_port' in request.json:
        try:
            inportCheckInt = int(request.json['in_port'])
        except ValueError:
            abort(400)
    if 'output' in request.json:
        try:
            outputCheckInt  = int(request.json['output'])
        except ValueError:
            abort(400)

    appendFlow = {
        'id': flows[-1]['id'] + 1,
        'priority': request.json['priority'],
        'in_port': request.json['in_port'],
        'output': request.json['output'],
    }

    getPriority = request.json['priority']
    getInport = request.json['in_port']
    getOutput = request.json['output']

    #if user user input has the same priority and in_port value as existing flows, abort, 
    #because it will replace flows instead of existing
    #also checks if user entered an exact info as existing flows
    flow = [flow for flow in flows if flow['priority'] == getPriority and flow['in_port'] == getInport]
    if len(flow) == 0:
        flows.append(appendFlow)
        sudoAddFlow = "sudo ovs-ofctl add-flow s1 priority=%i,in_port=%i,actions=output:%i" % (int(getPriority),int(getInport),int(getOutput))
        subprocess.call(sudoAddFlow, shell = True)
    else:
        abort(400)

    #Show created flow
    return jsonify({'flow': appendFlow}), 201

#Delete flow - Note containers that have the same in_port value as flow_id's in_port value will also be deleted
@app.route('/todo/api/v1.0/delete/<int:flow_id>', methods=['DELETE'])
def delete_flow(flow_id):
    #check if flow with flow_id exists
    flow = [flow for flow in flows if flow['id'] == flow_id]

    if len(flow) == 0:
        abort(404)

    #abort if flow_id is 0, don't delete flow 0
    if flow_id == 0:
        abort(400)

    #get in_port variable from container where id=flow_id
    fetchInport = flow[0]['in_port']

    #remove from both cli and json container
    sudoDelFlows = "sudo ovs-ofctl del-flows s1 in_port=%i" % int(fetchInport)
    subprocess.call(sudoDelFlows, shell = True)
    flows.remove(flow[0])

    #check if other containers have the same in_port number, if so, delete
    check = True
    while check:
        flow1 = [flow1 for flow1 in flows if flow1['in_port'] == fetchInport]
        if len(flow1) != 0:
            flows.remove(flow1[0])
            check = True
            flow1 = ""
        else:
            break

    #after deleting, show everything in the json container again
    return jsonify({'flows': flows})

#Update output field of specific flow
@app.route('/todo/api/v1.0/update/<int:flow_id>', methods=['PUT'])
def update_specificFlow(flow_id):
    #check if flow id exists
    flow = [flow for flow in flows if flow['id'] == flow_id]
    if len(flow) == 0:
        abort(404)

    #abort if flow_id is 0, don't delete flow 0
    if flow_id == 0:
        abort(400)

    #check output has be entered
    if not request.json or not 'output' in request.json:
        abort(400)

    #check if it is an integer
    if 'output' in request.json:
        try:
            outputCheckInt  = int(request.json['output'])
        except ValueError:
            abort(400)

    getOutput = request.json['output']
    fetchPriority = flow[0]['priority']
    fetchInport = flow[0]['in_port']

    #update output field with output value that has been entered
    flow[0]['output'] = getOutput

    #update in cli the output field of flow_id
    specificUpdate = "sudo ovs-ofctl add-flow s1 priority=%i,in_port=%i,actions=output:%i" % (int(fetchPriority),int(fetchInport),int(getOutput))
    subprocess.call(specificUpdate, shell = True)

    #show updated container
    return jsonify({'flow': flow[0]})

#Update output of all flows with the same in_port specified by user - Bulk update
@app.route('/todo/api/v1.0/update/all', methods=['PUT'])
def update_bulkFlow():
    #check output, in_port 2 variables has be entered
    if not request.json or not 'output' in request.json:
        abort(400)
    if not request.json or not 'in_port' in request.json:
        abort(400)

    #check if they are integers
    if 'in_port' in request.json:
        try:
            inportCheckInt = int(request.json['in_port'])
        except ValueError:
            abort(400)

    if 'output' in request.json:
        try:
            outputCheckInt  = int(request.json['output'])
        except ValueError:
            abort(400)

    getInport = request.json['in_port']
    getOutput = request.json['output']
    #check if other containers have the same in_port number but different output, 
    #if so, update output field to match user input
    check = True
    while check:
        flow = [flow for flow in flows if flow['in_port'] == getInport and flow['output'] != getOutput]
        if len(flow) != 0:
            flow[0]['output'] = getOutput
            check = True
            flow = ""
        else:
            break

    #update in cli the output field of all flows where in_port is the same
    bulkUpdate = "sudo ovs-ofctl mod-flows s1 'in_port=%i,actions=output:%i'" % (int(getInport),int(getOutput))
    subprocess.call(bulkUpdate, shell = True)

    #after updating, show everything in the json container again
    return jsonify({'flows': flows})

#when this script is terminating, delete all existing flows
def exit_handler():
    delAll = "sudo ovs-ofctl del-flows s1"
    subprocess.call(delAll, shell = True)

atexit.register(exit_handler)

if __name__ == '__main__':
        app.run(debug=True)

