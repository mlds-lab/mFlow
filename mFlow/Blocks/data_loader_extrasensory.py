import sys, os
sys.path.insert(0, os.path.abspath('..'))
from mFlow.Workflow.compute_graph import node

import requests, zipfile, io
import glob
import pandas as pd
import time


def extrasensory_data_loader(**kwargs):
    return node(function = __extrasensory_data_loader, kwargs=kwargs, name="ES Data Loader")

def __extrasensory_data_loader(label="SLEEPING",data_size="large"):

    start = time.time()

    pkl_file  = "extrasensory.pkl"
    if(data_size=="large"):
        directory = "data/extrasensory/"
    elif(data_size=="small"):
        directory = "data/small_extrasensory/"

    try:
        os.stat(directory)
    except:
        print("  Extrasensory data directory not found. Downloading data...")
        os.makedirs(directory)
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
        df_all=None
        for file in files:
            print(file)
            uuid = os.path.basename(file).split(".")[0]
            df = pd.read_csv(file, compression='gzip', header=0, sep=',', quotechar='"')
            df_list.append(df)
            uuid_list.append(uuid)

        print("Done reading files")
        df = pd.concat(df_list, axis = 0, keys=uuid_list)
        print("Done building dataframe")
        df_list=None
        df.to_pickle(directory + pkl_file)
        print("Done writing pkl file")

    #Extract desired label
    label_str = "label:" + label
    other_labels = list(filter(lambda x : "label" in x , df.keys().values ))
    other_labels.remove(label_str)
    df=df.rename(index=str, columns={label_str: "target"})
    df=df.drop(columns=other_labels)
    df.index.names = ["ID","Time"]

    return({"dataframe":df}) 
 