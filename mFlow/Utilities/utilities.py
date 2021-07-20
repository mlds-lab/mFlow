from pathlib import Path
import os

def getmFlowUserHome():
    home_dir  = str(Path.home())
    mflow_dir = os.path.join(home_dir,"mFlow")    
    if(not os.path.exists(mflow_dir)):
        os.mkdir(mflow_dir)
    return mflow_dir

def getDataDir():
    mflow_dir = getmFlowUserHome()
    data_dir  = os.path.join(mflow_dir,"data")
    if(not os.path.exists(data_dir)):
        os.mkdir(data_dir)
    return data_dir 

def getCacheDir():
    data_dir  = getDataDir()
    cache_dir = os.path.join(data_dir,"cache")
    if(not os.path.exists(cache_dir )):
        os.mkdir(cache_dir )
    return cache_dir  
