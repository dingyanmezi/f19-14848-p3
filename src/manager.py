import configparser
import os
import glob
import os.path
from os import path
import tarfile

class manager:
    
    instances = []

    def create_config(data):
        config = configparser.RawConfigParser()
        config.add_section(data['name'])
        config.set(data['name'], 'name', data['name'])
        config.set(data['name'], 'major', data['major'])
        config.set(data['name'], 'minor', data['minor'])
        config.set(data['name'], 'base_image', data['base_image'])
        config.set(data['name'], 'mounts', data['mounts'])
        config.set(data['name'], 'startup_script', data['startup_script'])
        config.set(data['name'], 'startup_owner', data['startup_owner'])
        config.set(data['name'], 'startup_env', data['startup_env'])
        filename = data['name'] + '-' + data['major'] + '-' + data['minor'] + '.cfg'
        if (path.exists(filename)):
            return "invalid"
        with open(filename, 'w') as configfile:
            config.write(configfile)
        return "succeed"

    def get_config():
        result = []
        
        files = glob.glob("*.cfg")
        files.sort(key=os.path.getmtime)

        json_obj = {
            "files": files
        }
        
        return json_obj

    def launch_container(data):
        config = configparser.RawConfigParser()
        # tarname = data['base_image']
        cfgName = data["name"] + "-" + data["major"] + "-" + data["minor"] + ".cfg"
        config.read(cfgName)
        mounts = data['mounts']
        print(mounts)
        print(type(mounts))
        onlyMount = mounts[0]
        print(onlyMount)
        items = onlyMount.split()
        mountTarFile = items[0]
        mountTarFileDes = items[1]
        desDirName = ""
        if ( mountTarFileDes.split('/')[-1] != "/"):
            desDirName = mountTarFileDes.split('/')[-1]
        state = items[2]
        os.chdir("../base_images/")
        pathForContainer = os.getcwd()
        with tarfile.open("basefs.tar.gz") as tar:
            tar.extractall(path=pathForContainer)
        os.system("sudo mkdir " + desDirName)
        os.system("sudo cp ../mountables/" + mountTarFile + " ./" + desDirName)
        os.system("sudo mkdir -p ./basefs" + mountTarFileDes)
        if (state == "READ"):
            os.system("sudo mount --bind -o ro $PWD/" + desDirName + " $PWD/basefs" + mountTarFileDes)
        return "succeeded"

    