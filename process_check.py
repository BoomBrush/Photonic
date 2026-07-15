import os

processname = 'gphoto2'
tmp = os.popen("ps -Af").read()
proccount = tmp.count(processname)

if proccount > 0:
    print(proccount, ' processes running of ', processname, 'type')
