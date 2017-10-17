from __future__ import print_function
import paramiko
import os
import subprocess
import time
import sys
from multiprocessing.pool import ThreadPool

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def connect(ip, host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname = ip, username = host, password = host)
    return client

def get_cpu_usage():
    time.sleep(12)
    p = subprocess.Popen(["mpstat 1 10 | awk '/^Average/ {print 100-$NF}'"],
                         shell = True, stdout = subprocess.PIPE)
    return p.communicate()[0]
    
def run(respond, vm_id):
    client = connect("10.0.0.%d" % (vm_id + 1), "vm%d" % vm_id)

    stdin, stdout, stderr = client.exec_command("sudo python scripts/stats.py %d" % respond,
                                                get_pty = True)

    stdin.write("vm%d\n" % vm_id)
    stdin.flush()   
  
    pool = ThreadPool(processes=1)
    async_res = pool.apply_async(get_cpu_usage)

    for line in stderr:
        if len(line.strip()) > 0:
            eprint(line.strip())    

    vm_stdout = []
    for line in stdout:
        vm_stdout.append(line.strip())
    client.close()
    
    cpu_usage = async_res.get()
    print("CPU: %s" % cpu_usage)

    for line in vm_stdout:
        if "RX Stat" in line:
            print(line) 

if __name__ == "__main__":
    run(int(sys.argv[1]), int(sys.argv[2]))
