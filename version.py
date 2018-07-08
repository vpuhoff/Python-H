command= 'git describe --long'
import subprocess
import string

class DelChars:
  def __init__(self, keep=string.digits+"."):
    self.comp = dict((ord(c),c) for c in keep)
  def __getitem__(self, k):
    return self.comp.get(k)

DC =DelChars()

def GetVersion():
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    if p_status==0:
        return output.decode().replace('-','.').translate(DC)
    else:
        raise Exception(output.decode(),err)

