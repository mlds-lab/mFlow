
import sys, os
from mFlow.Workflow.compute_graph import node

from sklearn.impute import SimpleImputer
import pandas as pd
import numpy as np



def Imputer(*args, **kwargs):
    return node(function = __Imputer, args=args, kwargs=kwargs, name="Imputer")

def __Imputer(df, method="mean", show=False):
    
    model = SimpleImputer(missing_values=np.nan, strategy=method)

    df = df["dataframe"]

    features = list(set(df.columns) - {'target'})
    numeric = df[features].values
    h,w = numeric.shape
    if(show): print("  Imputer: Running on matrix of size %dx%d"%(h,w))
    if np.any(np.isnan(numeric)):
        model.fit(numeric)
        imp = model.transform(numeric)
        
        df1 = pd.DataFrame(data=imp, columns=features, index=df.index)
        if 'target' in df.columns:
            df1['target'] = df['target']
        return({"dataframe":df1})

    else:
        if(show): print("  Imputer: No missing values")
        return({"dataframe":df})

