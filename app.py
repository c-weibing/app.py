#!flask/bin/python
from flask import Flask, jsonify, request, abort, make_response
import subprocess

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
    return make_response(jsonify({'error': '1. priority/in_port/output field is missing. 2. in_port and priority value cannot be the same'}), 400)

#Show all flows in cli
@app.route('/todo/api/v1.0/readall/flowscli', methods=['GET'])
def get_flowscli():
        p = subprocess.Popen(["ovs-ofctl", "dump-flows", "s1"], stdout=subprocess.PIPE)
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
        if not request.json or not 'priority' in request.json:
                abort(400)
        if not request.json or not 'in_port' in request.json:
                abort(400)
        if not request.json or not 'output' in request.json:
                abort(400)

        flow = {
                'id': flows[-1]['id'] + 1,
                'priority': request.json['priority'],
                'in_port': request.json['in_port'],
                'output': request.json['output'],
        }

        priorCheck = request.json['priority']
        in_portCheck = request.json['in_port']

        #if a container that has the same priority and in_port as what the user inputted then abort, because that will replace the current instead of adding
        flow1 = [flow1 for flow1 in flows if flow1['priority'] == priorCheck and flow1['in_port'] == in_portCheck]
        if len(flow1) == 0:
                flows.append(flow)
                prior = int(request.json['priority'])
                inport = int(request.json['in_port'])
                out = int(request.json['output'])
                concat = "ovs-ofctl add-flow s1 priority=%i,in_port=%i,actions=output:%i" % (prior,inport,out)
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
    in_portVariable = str(flow[0]['in_port'])
    concat = "ovs-ofctl del-flows s1 in_port=%s" % in_portVariable
    flows.remove(flow[0])
    subprocess.call(concat, shell = True)

    check = True
    while check:
        flow1 = [flow1 for flow1 in flows if flow1['in_port'] == in_portVariable]
        if len(flow1) != 0:
                flows.remove(flow1[0])
                check = True
                flow1 = ""
        else:
                break
    return

if __name__ == '__main__':
        app.run(debug=True)
