import sys, os
sys.path.insert(0, os.path.abspath('..'))
from Workflow.compute_graph import node
import pandas as pd
import time

def ccwrapper(*args, **kwargs):
    f=args[0]

    if("name" in kwargs):
        name = kwargs["name"]
        del kwargs["name"]
    else:
        name = f.__name__

    return node(function = __ccwrapper, args=args, kwargs=kwargs, name=name)
            
def __ccwrapper(f, df, sort_field=None, **kwargs):
    df=df["dataframe"]
    df=f(df, **kwargs)

    if(sort_field is not None):
        df=df.sort(sort_field)

    return({"dataframe":df}) 

def cc_to_pandas(*args, **kwargs):

    if("name" in kwargs):
        name = kwargs["name"]
        del kwargs["name"]
    else:
        name = "cc_to_pandas"

    return node(function = __cc_to_pandas, args=args, kwargs=kwargs, name=name)

def __cc_to_pandas(df, participant_field=None, datetime_field=None, time_trunc="1T",cache_filename=None ):

    #Check if requesting cached copy and have cached copy 
    if(cache_filename is not None):
        if(os.path.exists(cache_filename)):
            df = pd.read_pickle(cache_filename)
            return({"dataframe":df})

    #Get the dataframe
    df=df["dataframe"].toPandas()
    df[datetime_field]=df[datetime_field].apply(lambda x: x.floor(freq=time_trunc))
    df=df.set_index([participant_field,datetime_field])
    df.index.names = ["ID","Time"]

    #If needed, cache the dataframe
    if(cache_filename is not None):
        df.to_pickle(cache_filename)    

    return({"dataframe":df}) 