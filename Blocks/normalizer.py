
#from fancyimpute.iterative_svd import IterativeSVD
#from fancyimpute.knn import KNN
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
# TODO: add a wrapper for fancy-impute with fit and transform methods instead of the built-in complete() method, that
# TODO: takes the imputer method (or its type maybe?) as an argument (in function form? similar to ColumnSelection).

import sys, os
sys.path.insert(0, os.path.abspath('..'))
from Workflow.compute_graph import node

def Normalizer(*args, **kwargs):
    return node(function = __Normalizer, args=args, kwargs=kwargs, name="Normalizer")


def __Normalizer(df, show=False):
    model = RobustScaler()

    df = df["dataframe"]

    features = list(set(df.columns) - {'target'})
    numeric = df[features].values
    
    h,w = numeric.shape
    if(show): print("  Normalizer: running matrix of size %dx%d"%(h,w))
    
    model.fit(numeric)
   
    out = model.transform(numeric)
    df1 = pd.DataFrame(data=out, columns=features, index=df.index)
    if 'target' in df.columns:
        df1['target'] = df['target']
    #df = df1.copy()

    return({"dataframe":df1})

