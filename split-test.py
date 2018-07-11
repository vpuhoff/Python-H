import subprocess
import os
import uuid

temp_dir = 'D:\\temp\\'

def GetGUID():
    return str(uuid.uuid4())

def GetTempDir():
    newpath =temp_dir +GetGUID()
    if not os.path.exists(newpath):
        os.makedirs(newpath)
        return newpath
    else:
        raise Exception('Non uniq GUID!')

def Call(command, attr=None):
    result= list()
    run =''
    if attr:
        run = [command, attr]
    else:
        run = command
    p = subprocess.Popen(run, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        result.append(line.decode().replace('\n',''))
    retval = p.wait()
    return retval, result

def SplitFile(filename, size):
    temp_dir = GetTempDir()
    splitcommand =  ' --bytes={}M {} {}'.format(str(size),filename,temp_dir)
    code, result = Call('split',splitcommand)
    if code==0:
        for x in result:
            print (x)
        return temp_dir
    else:
        raise Exception(result)

ret = SplitFile("D:/Downloads/youtrack-2018.1.41051.msi",50)
print(ret)