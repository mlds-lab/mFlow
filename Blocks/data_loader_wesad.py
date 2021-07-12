import sys, os
sys.path.insert(0, os.path.abspath('..'))
from Workflow.compute_graph import node

import requests, zipfile, io
import glob
import pandas as pd
import time
import tarfile
from cerebralcortex.kernel import Kernel
from pyspark.sql import functions as F
from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType
from cerebralcortex.core.datatypes.datastream import DataStream


def wesad_data_loader(**kwargs):
    return (node(function = __wesad_data_loader, kwargs=kwargs, name="WESAD Data Loader"),
            node(function = __wesad_label_loader, kwargs=kwargs, name="WESAD Label Loader"))

def __wesad_data_loader(data_size="small"):

    CC = Kernel(cc_configs="default", study_name="wesad")
    CC.sqlContext.sql("set spark.sql.shuffle.partitions=1")

    #Get the data
    data = CC.get_stream("wesad.chest.ecg")
    if(data_size=="small"):
        data = data.filter_user(["s2"])

    #Get and process the labels
    labels = CC.get_stream("wesad.label")
    if(data_size=="small"):
        labels = labels.filter_user(["s2"])

    # window label data into 60 seconds chunks
    win = F.window("timestamp", windowDuration="60 seconds",startTime='0 seconds')
    windowed_labels=labels.groupby(["user","version",win]).agg(F.collect_list("label"))

    # label each window
    label_window_udf = udf(lambda s: max(set(s), key=s.count), IntegerType())
    final_labels = DataStream(windowed_labels.withColumn("target", label_window_udf(F.col("collect_list(label)"))).drop("collect_list(label)"))
    final_labels = DataStream(final_labels.withColumn("timestamp",final_labels["window"].start).drop("version").drop("window"))
    
    return({"dataframe": data,}) 

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