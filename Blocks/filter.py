import sys, os
sys.path.insert(0, os.path.abspath('..'))
from Workflow.compute_graph import node
import time


def MisingLabelFilter(*args, **kwargs):
    return node(function = __MisingLabelFilter, args=args, kwargs=kwargs, name="Missing Label Filter")
            
def __MisingLabelFilter(df,key="dataframe",inplace=False):
    df=df[key]
    df=df.dropna(axis=0, subset=["target"], inplace=inplace)
    return({"dataframe":df})        
    
    
def MisingDataRowFilter(*args, **kwargs):
    return node(function = __MisingDataRowFilter, args=args, kwargs=kwargs, name="Missing Data Row Filter")
    
def __MisingDataRowFilter(df,thresh=0.2, inplace=False,key="dataframe"):
    df=df[key]
    df=df.dropna(axis=0, thresh = thresh*df.shape[0], inplace=inplace)  
    return({"dataframe":df})  



def MisingDataColumnFilter(*args, **kwargs):
    return node(function = __MisingDataColumnFilter, args=args, kwargs=kwargs, name="Missing Data Column Filter")    

def __MisingDataColumnFilter(df, thresh=0.2, inplace=False,key="dataframe"):
    df=df[key]
    df=df.dropna(axis=1, thresh = thresh*df.shape[0], inplace=inplace)  
    return({"dataframe":df})
    

def Take(*args, **kwargs):
    return node(function = __Take, args=args, kwargs=kwargs, name="Take")

def __Take(df, num):
        
    df = df["dataframe"][:num]
    return({"dataframe": df})