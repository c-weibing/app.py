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

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'No such task'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': '1. priority/in_port/output field is missing. 2. in_port and priority value cannot be the same as existing 3. Please input a valid integer'}), 400)

#Show all flows in cli
@app.route('/todo/api/v1.0/readall/flowscli', methods=['GET'])
def get_flowscli():
        p = subprocess.Popen(["sudo", "ovs-ofctl", "dump-flows", "s1"], stdout=subprocess.PIPE)
        output, err = p.communicate()
        return output

#Show all flows in json
@app.route('/todo/api/v1.0/readall/flowsjson', methods=['GET'])
def get_flowsjson():
        return jsonify({'flows': flows})
#Select flow to show
@app.route('/todo/api/v1.0/readone/<int:flow_id>', methods=['GET'])
def get_flow(flow_id):
        flow = [ flow for flow in flows if flow['id'] == flow_id]
        if len(flow) == 0:
                abort(404)
        return jsonify({'flows': flow[0]})

#Add flow
@app.route('/todo/api/v1.0/create/addflows', methods=['POST'])
def create_flow():
        #check if priority, in_port, output has been entered
        if not request.json or not 'priority' in request.json:
                abort(400)
        if not request.json or not 'in_port' in request.json:
                abort(400)
        if not request.json or not 'output' in request.json:
                abort(400)

        #check if they are all integers
        if 'priority' in request.json:
                try:
                        priorCheckInt = int(request.json['priority'])
                except ValueError:
                        abort(400)

        if 'in_port' in request.json:
                try:
                        portCheckInt = int(request.json['in_port'])
                except ValueError:
                        abort(400)

        if 'output' in request.json:
                try:
                       outputCheckInt  = int(request.json['output'])
                except ValueError:
                        abort(400)

        flow = {
                'id': flows[-1]['id'] + 1,
                'priority': request.json['priority'],
                'in_port': request.json['in_port'],
                'output': request.json['output'],
        }

        priorCheck = request.json['priority']
        in_portCheck = request.json['in_port']

        #if a container that has the same priority and in_port as what the user inputted then abort, because that will replace the current instead of adding.
        #also checks if user entered an exact info as existing flows
        flow1 = [flow1 for flow1 in flows if flow1['priority'] == priorCheck and flow1['in_port'] == in_portCheck]
        if len(flow1) == 0:
                flows.append(flow)
                prior = request.json['priority']
                inport = request.json['in_port']
                out = request.json['output']
                concat = "sudo ovs-ofctl add-flow s1 priority=%i,in_port=%i,actions=output:%i" % (int(prior),int(inport),int(out))
                subprocess.call(concat, shell = True)
        else:
                abort(400)
        return jsonify({'flow': flow}), 201

#Delete flow
@app.route('/todo/api/v1.0/delete/<int:flow_id>', methods=['DELETE'])
def delete_flow(flow_id):
    flow = [flow for flow in flows if flow['id'] == flow_id]
    if len(flow) == 0:
        abort(404)

    in_portVar = flow[0]['in_port']

    concat = "sudo ovs-ofctl del-flows s1 in_port=%i" % int(in_portVar)
    subprocess.call(concat, shell = True)
    flows.remove(flow[0])

   #check if other containers have the same in_port number it will also be deleted from the json container because that's how the cli works

    check = True
    while check:
        flow1 = [flow1 for flow1 in flows if flow1['in_port'] == in_portVar]
        if len(flow1) != 0:
                flows.remove(flow1[0])
                check = True
                flow1 = ""
        else:
                break

    #after deleting, show everything in the json container again
    return jsonify({'flows': flows})

#Update output of specific flow
@app.route('/todo/api/v1.0/update/<int:flow_id>', methods=['PUT'])
def update_specificFlow(flow_id):
    #check if flow id exists
    flow = [flow for flow in flows if flow['id'] == flow_id]
    if len(flow) == 0:
        abort(404)
    #check if output has been entered
    if not request.json or not 'output' in request.json:
        abort(400)

    #Change output of specific flow (need to fetch priority and in_port from flow container)
    #check if output is an integer
    if 'output' in request.json:
        try:
                outputCheckInt  = int(request.json['output'])
        except ValueError:
                abort(400)

    getOutput = request.json['output']
    getPriority = flow[0]['priority']
    getInPort = flow[0]['in_port']

    flow[0]['output'] = getOutput

    specificUpdate = "sudo ovs-ofctl add-flow s1 priority=%i,in_port=%i,actions=output:%i" % (int(getPriority),int(getInPort),int(getOutput))  
    subprocess.call(specificUpdate, shell = True)

    return jsonify({'flow': flow[0]})

#Update output of all flows with the same in_port specified by user - Bulk update
@app.route('/todo/api/v1.0/update/all', methods=['PUT'])
def update_bulkFlow():
    if not request.json or not 'output' in request.json:
        abort(400)
    if not request.json or not 'in_port' in request.json:
        abort(400)

    if 'in_port' in request.json:
        try:
                portCheckInt = int(request.json['in_port'])
        except ValueError:
                abort(400)

    if 'output' in request.json:
        try:
                outputCheckInt  = int(request.json['output'])
        except ValueError:
                abort(400)

    fetchInport = request.json['in_port']
    fetchOut = request.json['output']

    check = True
    while check:
        flow = [flow for flow in flows if flow['in_port'] == fetchInport and flow['output'] != fetchOut]
        if len(flow) != 0:
                flow[0]['output'] = fetchOut
                check = True
                flow = ""
        else:
                break

    bulkUpdate = "sudo ovs-ofctl mod-flows s1 'in_port=%i,actions=output:%i'" % (int(fetchInport),int(fetchOut))
    subprocess.call(bulkUpdate, shell = True)

    return jsonify({'flows': flows})

def exit_handler():
    delAll = "sudo ovs-ofctl del-flows s1"
    subprocess.call(delAll, shell = True)

atexit.register(exit_handler)

if __name__ == '__main__':
        app.run(debug=True)

