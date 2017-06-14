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

#Show all flows in cli
@app.route('/todo/api/v1.0/readall/flowscli', methods=['GET'])
def get_flowscli():
        p = subprocess.Popen(["ovs-ofctl", "dump-flows", "s1"], stdout=subprocess.PIPE)
        output, err = p.communicate()
        return output + "\n"

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

        flows.append(flow)
        prior = int(request.json['priority'])
        inport = int(request.json['in_port'])
        out = int(request.json['output'])
        concat = "ovs-ofctl add-flow s1 priority=%i,in_port=%i,actions=output:%i" % (prior,inport,out)
        subprocess.call(concat, shell = True)
        return jsonify({'flow': flow}), 201

if __name__ == '__main__':
        app.run(debug=True)
