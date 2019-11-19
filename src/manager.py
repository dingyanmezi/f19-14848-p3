import configparser
import os
import glob
import os.path
from os import path
import tarfile
import json
from multiprocessing import Process

instances = []

class manager:
    
    

    def create_config(data):
        config = configparser.RawConfigParser()
        sectionName = data["name"] + "-" + data["major"] + "-" + data["minor"]
        config.add_section(sectionName)
        config.set(sectionName, 'name', data["name"])
        config.set(sectionName, 'major', data['major'])
        config.set(sectionName, 'minor', data['minor'])
        config.set(sectionName, 'base_image', data['base_image'])
        config.set(sectionName, 'mounts', data['mounts'])
        config.set(sectionName, 'startup_script', data['startup_script'])
        config.set(sectionName, 'startup_owner', data['startup_owner'])
        config.set(sectionName, 'startup_env', data['startup_env'])
        filename = data["name"] + '-' + data['major'] + '-' + data['minor'] + '.cfg'
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

    def launch_container_process(port):
        os.system('sudo chroot basefs /bin/bash -c "export PORT=' + port + ' && /webserver/tiny.sh"')

    def launch_container(data):
        global instances
        config = configparser.RawConfigParser()
        
        cfgName = data["name"] + "-" + data["major"] + "-" + data["minor"] + ".cfg"
        sectionName = data["name"] + "-" + data["major"] + "-" + data["minor"]
        thisfolder = os.path.dirname(os.path.abspath(__file__))
        initfile = os.path.join(thisfolder, cfgName)
        config.read(initfile)
        # mounts = data['mounts']
        mounts = config.get(sectionName, 'mounts').split(",")
        # print(mounts)
        # print(type(mounts))
        port = config.get(sectionName, 'startup_env').split(";")[0].split('=')[-1]
        print(port)
        
        os.chdir("../base_images/")
        os.system("mkdir " + sectionName)
        os.chdir("../base_images/" + sectionName)
        pathForContainer = os.getcwd()     # inside sensible-1-01 directory
        with tarfile.open("../basefs.tar.gz") as tar:
            tar.extractall(path=pathForContainer)
    
        # mount each entry
        
        for mount in mounts:
            mountNoSpace = mount.split()
            mountTarFile = mountNoSpace[0].split("'")[-1]   # potato.tar
            mountTarFileDes = mountNoSpace[1]               # /webserver/potato
            desDirName = ""                                 # "potato" directory
            if ( mountTarFileDes.split('/')[-1] != "/"):
                desDirName = mountTarFileDes.split('/')[-1]   
            state = mountNoSpace[-1].split("'")[0]            #  READ
            print(state)
            os.system("mkdir " + desDirName)
            os.system("cp ../../mountables/" + mountTarFile + " ./")
            os.system("mkdir -p ./basefs" + mountTarFileDes)

            with tarfile.open(mountTarFile) as tar1:
                tar1.extractall(path=pathForContainer)

            if (state == "READ"):
                os.system("sudo mount --bind -o ro $PWD/" + desDirName + " $PWD/basefs" + mountTarFileDes)
            elif (state == "READWRITE"):
                os.system("sudo mount --bind -o rw $PWD/" + desDirName + " $PWD/basefs" + mountTarFileDes)

        container_process = Process(target=manager.launch_container_process, args=(port, ))
        container_process.start()

        data["instance"] = cfgName
        instances.append(data)

        os.chdir("../../src")

        return cfgName

    def get_instances():
        global instances
        result = {
            "instances" : instances
        }
        return result

    