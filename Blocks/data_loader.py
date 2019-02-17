import sys, os
sys.path.insert(0, os.path.abspath('..'))
from Workflow.compute_graph import node

import requests, zipfile, io
import glob
import pandas as pd
import time


def extrasensory_data_loader(**kwargs):
    return node(function = __extrasensory_data_loader, kwargs=kwargs, name="ES Data Loader")

def __extrasensory_data_loader(label="SLEEPING"):

    start = time.time()

    directory = "data/extrasensory/"
    pkl_file  = "extrasensory.pkl"

    try:
        os.stat(directory)
    except:
        print("  Extrasensory data directory not found. Downloading data...")
        os.mkdir(directory)  
        data = "http://extrasensory.ucsd.edu/data/primary_data_files/ExtraSensory.per_uuid_features_labels.zip"
        r    = requests.get(data)
        z    = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(directory)
    
    try: 
        os.stat(directory + pkl_file)
        print("  Loading Extrasensory pkl file...")
        df = pd.read_pickle(directory + pkl_file)
    except:
        print("  Extrasensory pkl file not found. Extracting data...")
        df_list=[]
        uuid_list = []
        files = glob.glob(directory + "*.gz")
        for file in files:
            uuid = os.path.basename(file).split(".")[0]
            df = pd.read_csv(file, compression='gzip', header=0, sep=',', quotechar='"')
            df_list.append(df)
            uuid_list.append(uuid)

        df = pd.concat(df_list, axis = 0, keys=uuid_list)
        df.to_pickle(directory + pkl_file)

    #Extract desired label
    label_str = "label:" + label
    other_labels = list(filter(lambda x : "label" in x , df.keys().values ))
    other_labels.remove(label_str)
    df=df.rename(index=str, columns={label_str: "target"})
    df=df.drop(columns=other_labels)
    df.index.names = ["ID","Time"]
    #df=df[:100000]
    
    end = time.time()
    #print("Data Loader Time",end-start)
    return({"dataframe":df}) 
    #return(0)