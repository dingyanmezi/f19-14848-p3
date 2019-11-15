from flask import Flask, request
from http.server import HTTPServer, BaseHTTPRequestHandler
#from my_execpt import *
from manager import manager
import json, os, sys

app = Flask(__name__)

def is_json(myjson):
  try:
    json_object = json.loads(myjson)
  except ValueError as e:
    return False
  return True

@app.route('/config', methods=['POST'])
def create_config_file():
    json_obj = request.get_json(force=False, silent=False)
    if (json_obj == None):
        return "", 409	    
    if 'major' not in json_obj:
        return "", 409
    result = manager.create_config(json_obj)
    if (result == "invalid"):
        return "", 409
    return "", 200

@app.route('/cfginfo', methods=['GET'])
def get_config_list():
    result = manager.get_config()
    return result, 200


@app.route('/launch', methods=['POST'])
def create_instance_container():
    json_obj = request.get_json(force=False, silent=False)
    # print(json_obj)
    if (json_obj == None):
        return "", 409	    
    if 'major' not in json_obj:
        return "", 409
    result = manager.launch_container(json_obj)
    return "", 200


@app.route('/list', methods=['GET'])
def get_running_instance_list():
    return


@app.route('/destroy/<instance>', methods=['DELETE'])
def destroy_running_instance():
    return

@app.route('/destroyall/', methods=['DELETE'])
def destroy_all():
    return

    

def main():
    
    app.run('localhost', '8080')

if __name__ == '__main__':
    main()
