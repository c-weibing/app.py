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

if __name__ == '__main__':
        app.run(debug=True)
