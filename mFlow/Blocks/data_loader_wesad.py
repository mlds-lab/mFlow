import sys, os
from mFlow.Workflow.compute_graph import node
from mFlow.Utilities.utilities import getDataDir

import requests, zipfile, io, tarfile
import glob
import pandas as pd
import time
import tarfile
from cerebralcortex.kernel import Kernel
from pyspark.sql import functions as F
from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType
from cerebralcortex.core.datatypes.datastream import DataStream

#def wesad_data_loader(**kwargs):
#    return (node(function = __wesad_data_loader, kwargs=kwargs, name="WESAD Data Loader"),
#            node(function = __wesad_label_loader, kwargs=kwargs, name="WESAD Label Loader"))

def wesad_data_loader(**kwargs):
    return node(function = __wesad_data_loader, kwargs=kwargs, name="WESAD Data Loader")

def __wesad_data_download(data_size="all"):
    base_data_dir       = getDataDir()
    compressed_data_dir = os.path.join(base_data_dir,"compressed")
    wesad_data_dir      = os.path.join(base_data_dir,"wesad_"+data_size)
    wesad_cc_dir        = os.path.join(wesad_data_dir,"cc_data")

    if(data_size=="all"):
        compressed_file="cc_data.tar.bz2"
    elif(data_size=="small"):
        compressed_file="s2_data.tar.bz2"

    compressed_data_url="http://mhealth.md2k.org/images/datasets/%s"%compressed_file
    compressed_data_local_file = os.path.join(compressed_data_dir,compressed_file)

    #Make all data directories
    for d in [base_data_dir, compressed_data_dir, wesad_data_dir]:
        if(not os.path.exists(d)):
            os.mkdir(d)

    #Check if cc data store exists:
    if(not os.path.exists(wesad_cc_dir)):
        
        #Check if compressed cc version of the data set exists
        if(not os.path.isfile(compressed_data_local_file)):
            print("Downloading WESAD data archive to %s "%compressed_data_local_file,end="")
            #Download the compressed data file
            response = requests.get(compressed_data_url, stream=True)
            response.raise_for_status()
            with open(compressed_data_local_file , 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024): 
                    f.write(chunk)
                    print(".",end="",flush=True)
            print("")
            print("Done")
        
        #Extract the data set
        print("Extracting WESAD data archive to %s ..."%wesad_cc_dir,end="",flush=True)
        tar = tarfile.open(compressed_data_local_file)
        tar.extractall(wesad_data_dir)
        tar.close()
        print(" Done")

def __wesad_data_loader(data_size="small"):

    #Download the data if needed
    base_data_dir       = getDataDir()
    compressed_data_dir = os.path.join(base_data_dir,"compressed")
    wesad_data_dir      = os.path.join(base_data_dir,"wesad_"+data_size)
    wesad_cc_dir        = os.path.join(wesad_data_dir,"cc_data")
    if(not os.path.exists(wesad_cc_dir)):
        __wesad_data_download(data_size=data_size)

    #Creat CC kernel to load WESAD data
    cc_configs = {"nosql_storage": "filesystem", 
              "filesystem":{"filesystem_path": wesad_cc_dir },
              "relational_storage": "sqlite",
              "sqlite": {"file_path": wesad_cc_dir },
             }
    CC = Kernel(cc_configs=cc_configs, study_name="wesad")
    CC.sqlContext.sql("set spark.sql.shuffle.partitions=1")

    #Get the data
    data = CC.get_stream("wesad.chest.ecg")
    if(data_size=="small"):
        data = data.filter_user(["s2"])

    #Get and process the labels
    labels = CC.get_stream("wesad.label")
    if(data_size=="small"):
        labels = labels.filter_user(["s2"])
    elif(data_size=="all"):
        pass
    else:
        raise ValueError("Error: data_size must be 'small' or 'all'")

    #Data set documentation indicates removing label 0 and 5,6,7
    #for this data set
    labels = labels.filter("label > 0")
    labels = labels.filter("label < 5")
    
    #Convert problem to stress/not stress with stress=1, not stress=0
    labels= labels.replace({1:0,2:1,3:0,4:0},[], subset=["label"])
    
    # window label data into 60 seconds chunks
    win = F.window("timestamp", windowDuration="60 seconds",startTime='0 seconds')
    windowed_labels=labels.groupby(["user","version",win]).agg(F.collect_list("label"))

    # label each window
    label_window_udf = udf(lambda s: max(set(s), key=s.count), IntegerType())
    final_labels = DataStream(windowed_labels.withColumn("target", label_window_udf(F.col("collect_list(label)"))).drop("collect_list(label)"))
    final_labels = DataStream(final_labels.withColumn("timestamp",final_labels["window"].start).drop("version").drop("window"))
       
    return({"dataframe": data,"labels":final_labels}) 

def __wesad_label_loader(data_size="small"):

    CC = Kernel(cc_configs="default", study_name="wesad")
    CC.sqlContext.sql("set spark.sql.shuffle.partitions=1")

    #Get and process the labels
    labels = CC.get_stream("wesad.label")
    if(data_size=="small"):
        labels = labels.filter_user(["s2"])
    elif(data_size=="all"):
        pass
    else:
        raise ValueError("Error: data_size must be 'small' or 'all'")

    #Data set documentation indicates removing label 0 and 5,6,7
    #for this data set
    labels = labels.filter("label > 0")
    labels = labels.filter("label < 5")
    
    #Convert problem to stress/not stress with stress=1, not stress=0
    labels= labels.replace({1:0,2:1,3:0,4:0},[], subset=["label"])
    
    # window label data into 60 seconds chunks
    win = F.window("timestamp", windowDuration="60 seconds",startTime='0 seconds')
    windowed_labels=labels.groupby(["user","version",win]).agg(F.collect_list("label"))

    # label each window
    label_window_udf = udf(lambda s: max(set(s), key=s.count), IntegerType())
    final_labels = DataStream(windowed_labels.withColumn("target", label_window_udf(F.col("collect_list(label)"))).drop("collect_list(label)"))
    final_labels = DataStream(final_labels.withColumn("timestamp",final_labels["window"].start).drop("version").drop("window"))
    
    return({"dataframe": final_labels}) 