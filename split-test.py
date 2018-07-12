#coding=utf-8
print('Load libs...')
import subprocess
import shutil
import os
import uuid
from tqdm import tqdm
from os import listdir
from os.path import isfile, join
from datetime import datetime as dt
import os
import platform
import time
import json
print('Init...')
temp_dir = '/home/vpuhoff/tmp/'

def GetGUID():
    return str(uuid.uuid4())

def GetTempDir():
    newpath =temp_dir +GetGUID()
    if not os.path.exists(newpath):
        #print('Create temp dir...',newpath)
        os.makedirs(newpath)
        return newpath
    else:
        raise Exception('Non uniq GUID!')

def Call(command):
    #print(command)
    result= list()
    run = command
    p = subprocess.Popen(run, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        cline = line.decode().replace('\n','')
        #print(cline)
        result.append(cline)
    retval = p.wait()
    return retval, result

def ListFiles(path):
    onlyfiles = [join(path, f) for f in listdir(path) if isfile(join(path, f))]
    return onlyfiles

def GetMD5(filename):
    code, result =  Call('md5sum  {}'.format(filename))
    if code==0:
        md5 = result[0].split(' ')[0]
        return md5
    else:
        raise Exception(result)

def creation_date(path_to_file):
    if platform.system() == 'Windows':
        return (os.path.getctime(path_to_file))
    else:
        stat = os.stat(path_to_file)
        try:
            return (stat.st_birthtime)
        except AttributeError:
            return (stat.st_mtime)

def GetFileSize(path):
    statinfo = os.stat(path)
    return statinfo.st_size

def SplitFile(filename, size):
    start = time.time()
    for t in tqdm([1],total=1,desc='Split file:'+filename):
        temp_dir = GetTempDir()
        uid = GetGUID()
        guidname = 'Split.Part.'+uid+"."
        splitcommand =  'split  --additional-suffix=.zip -a 1 -d --bytes={}M {} {}/{}'.format(str(size),filename,temp_dir,guidname)
        code, result = Call(splitcommand)
        if code==0:
            chunk_files = ListFiles(temp_dir)
            whole_md5 = GetMD5(filename)
            chunks=dict()
            files=dict()
            for chunk in tqdm(chunk_files):
                base=os.path.basename(chunk)
                chunks[base] = GetMD5(chunk)
                files[base]=GetFileSize(chunk)
            ctime= creation_date(filename)
            filedate=dt.fromtimestamp(ctime).isoformat()
            whole_size = GetFileSize(filename)
            result = {'md5':whole_md5,
                'split.time':dt.now().isoformat(),
                'split.duration':time.time()-start,
                'created':filedate,
                'created.ctime':ctime,
                'size':whole_size,
                'uid':uid,
                'chunks.items':chunks,
                'filename':os.path.basename(filename),
                'files':files,
                'chunks.storage':temp_dir,
                'chunks.template':guidname,
                'location':filename
            }
            return result
        else:
            raise Exception(result)

def DeleteFolder(path):
    shutil.rmtree(path)

def MoveFile(old,new):
    shutil.move(old,new)

def JoinFile(config, storage):
    start = time.time()
    for t in tqdm([1],total=1,desc='Join file :'+storage):
        template=config['chunks.template']
        outfile=storage+'/'+config['filename']
        command = 'cat ' + storage+'/'+template+"* >"+outfile
        code, result = Call(command)
        if code==0:
            md5 = GetMD5(outfile)
            if  md5==config['md5']:
                os.utime(outfile,(config['created.ctime'],config['created.ctime']))
                return outfile
            else:
                raise Exception('File corrupted')

print('Start...')

ret = SplitFile("/home/vpuhoff/tmp/atlassian-bitbucket-5.10.1-x64.bin",50)


print(json.dumps(ret, indent=4, sort_keys=True))

outfile = JoinFile(ret,ret['chunks.storage'])

MoveFile(outfile,"/home/vpuhoff/tmp/atlassian-bitbucket-5.10.1-x64_copy.bin")