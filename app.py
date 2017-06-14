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

if __name__ == '__main__':
        app.run(debug=True)
