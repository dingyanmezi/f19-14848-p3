import configparser
import os, signal
import glob
import os.path
from os import path
import tarfile
import json
from multiprocessing import Process
import time

instances = []
processes = []

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
        # os.system('sudo chroot basefs /bin/bash -c "export PORT=' + port + ' && /webserver/tiny.sh"')
        os.system('unshare -p -f --mount-proc=$PWD/basefs/proc chroot basefs /bin/bash -c "export PORT=' + port + ' && /webserver/tiny.sh"')

    def launch_container(data):
        global instances
        global processes
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
            # os.system("mkdir " + desDirName)
            os.system("cp ../../mountables/" + mountTarFile + " ./")
            os.system("sudo mkdir ./basefs" + mountTarFileDes)

            with tarfile.open(mountTarFile) as tar1:
                tar1.extractall(path=pathForContainer)

            if (state == "READ"):
                print("inside READ !!")
                os.system("sudo mount --bind -o ro $PWD/" + desDirName + " $PWD/basefs" + mountTarFileDes)
            elif (state == "READWRITE"):
                os.system("sudo mount --bind -o rw $PWD/" + desDirName + " $PWD/basefs" + mountTarFileDes)

        os.system('mount -t proc proc $PWD/basefs/proc')

        container_process = Process(target=manager.launch_container_process, args=(port, ))
        container_process.start()
        os.setpgid(container_process.pid, container_process.pid)
        processes.append(container_process)
        data["instance"] = str(container_process.pid)
        time.sleep(1)
        result = container_process.pid
        instances.append(data)   ## instances contain an array of jsons

        os.chdir("../../src")

        return result

    def get_instances():
        global instances
        result = {
            "instances" : instances
        }
        return result

    def kill_one_container_process(pid):
        global processes
        global instances
        for process in processes:
            if process.is_alive() and str(process.pid) == pid:
                os.killpg(process.pid, signal.SIGKILL)
                print(process.is_alive())
                processes.remove(process)
                break
                # print("reached process termination")
                
        for instance in instances:
            if instance["instance"] == pid:
                sectionName = instance["name"] + "-" + instance["major"] + "-" + instance["minor"]
                config = configparser.RawConfigParser()
                cfgName = sectionName + ".cfg"
                thisfolder = os.path.dirname(os.path.abspath(__file__))
                initfile = os.path.join(thisfolder, cfgName)
                config.read(initfile)
                mounts = config.get(sectionName, 'mounts').split(",")
                for mount in mounts:
                    mountTarFileDes = mount.split()[1]
                    os.chdir("../base_images/")
                    # if len(mountTarFileDes.split("/")) == 3:
                    os.system("umount -l $PWD/"+ sectionName + "/basefs" + mountTarFileDes)
                    os.chdir("../src")
                os.chdir("../base_images/")
                os.system('chroot ./'+ sectionName + '/basefs /bin/bash -c "umount proc"')
                os.system("rm -rf ./" + sectionName)
                os.chdir("../src")
                instances = [x for x in instances if x["instance"] != pid]
                # instances.remove(instance)    ## just change it 
                break
                    
