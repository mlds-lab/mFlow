import sys, os
from mFlow.Workflow.compute_graph import node

import copy
import numpy as np
import pandas as pd
import copy
import itertools
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GroupKFold, KFold, GroupShuffleSplit

import warnings
from sklearn.exceptions import ConvergenceWarning,UndefinedMetricWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UndefinedMetricWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
import  time

def df_to_sk(df):
    
    features = list(set(df.columns) - {'target'})
    X = df[features].values
    Y = df["target"].values
    
    return X,Y

def addTarget(*args, **kwargs):

    if("name" in kwargs):
        name = kwargs["name"]
        del kwargs["name"]
    else:
        name = "addTarget"
    
    return node(function = __addTarget, args=args, kwargs=kwargs, name=name)

def __addTarget(df_data,df_labels,*args, key_data="dataframe", key_labels="dataframe",**kwargs):

    df = df_data[key_data].join(df_labels[key_labels],how="inner")
    return {"dataframe": df} 


def ExpTrainTest(*args, **kwargs):
    
    if("name" in kwargs):
        name = kwargs["name"]
        del kwargs["name"]
    else:
        name = "Train-Test Experiment"
    
    if("n_folds" in kwargs):
        n_folds = kwargs["n_folds"]
    else:
        n_folds = 5
    
    args       = list(args)
    estimators = copy.copy(args[1])
    
    node_list = []
    for estimator in estimators:
        new_estimator  = {estimator: estimators[estimator]}
        args[1]        = new_estimator
        name           = "EXP-TT: %s"%(estimator)
        node_list.append(node(function = __ExpTrainTest, args=copy.copy(args), kwargs=copy.copy(kwargs), name=name))
    
    return node_list

def __ExpTrainTest(df, estimators, metrics=(), random_state=11, train_size=.8, partition_index_number=0,key="dataframe", grouped=True, show=False):

    df=df[key]

    if(grouped):
        index = df.index.names
        partition_index = index[partition_index_number]

        all_ids = np.unique(np.array(df.index.get_level_values(partition_index)))
        tr_ids, te_ids = train_test_split(all_ids, train_size=train_size,test_size=1-train_size, random_state=random_state)

        df_tr = df[df.index.get_level_values(partition_index).isin(list(tr_ids))]
        df_te = df[df.index.get_level_values(partition_index).isin(list(te_ids))]        

    else:
        df_tr,df_te=train_test_split(df, train_size=train_size,test_size=1-train_size, random_state=random_state)        
    
    X_tr, Y_tr = df_to_sk(df_tr)
    X_te, Y_te = df_to_sk(df_te)

    m = list(map(lambda x: str(x.__name__), metrics))
    report = pd.DataFrame(columns=m, index=list(estimators.keys()),dtype=float)

    fit_estimators={}


    for name in estimators:
        if(show): print("  Fitting and testing %s"%name)
    
        estimator = copy.deepcopy(estimators[name])
        
        estimator.fit(X_tr,Y_tr)
        fit_estimators[name]=estimator
    
        y_predict = estimator.predict(X_te)
        for i, metric in enumerate(metrics):
            report[m[i]].loc[name] = metric(Y_te, y_predict)        
    
    
    return {"report":report, "fit_estimators":fit_estimators}


def ExpCV(*args, **kwargs):
    
    #Example of a node expander
    #Single function call returns a list of nodes
    #Calling function must accept a list of nodes
    
    if("n_folds" in kwargs):
        n_folds = kwargs["n_folds"]
    else:
        n_folds = 5
    
    args       = list(args)
    estimators = copy.copy(args[1])
    
    node_list = []
    for k in range(n_folds):
        for estimator in estimators:
            new_estimator  = {estimator: estimators[estimator]}
            args[1]        = new_estimator
            kwargs["fold"] = k
            name           = "EXP-CV(%d): %s"%(k+1, estimator)
            node_list.append(node(function = __ExpCV, args=copy.copy(args), kwargs=copy.copy(kwargs), name=name))
    
    return node_list

    
def __ExpCV(df, estimators, metrics=(), random_state=11, partition_index_number=0, n_folds=5, fold=None,key="dataframe",grouped=True, show=False):
    
    df=df[key]    
    X, Y = df_to_sk(df)

    if(grouped):
        index = df.index.names
        partition_index = index[partition_index_number]
        skf = GroupKFold(n_splits=n_folds)
        iterator = enumerate(skf.split(X, Y, groups=df.index.get_level_values(partition_index)))
    else:
        skf = KFold(n_splits=n_folds, shuffle=False, random_state=random_state)
        iterator = enumerate(skf.split(X,Y))

    #Prepare multi-level report 
    m = list(map(lambda x: str(x.__name__), metrics))
    folds = [fold+1] 
    
    methods = list(estimators.keys())
    tuples=itertools.product(methods,folds) 
    index = pd.MultiIndex.from_tuples(tuples, names=['Method', 'Fold'])
    report = pd.DataFrame(columns=m, index=index, dtype=float)
    
    fit_estimators=[{}]*n_folds
    
    for j, (train_index, test_index) in iterator:

        if(j != fold):
            continue

        X_tr = X[train_index,:]
        X_te = X[test_index,:]

        Y_tr = Y[train_index]
        Y_te = Y[test_index]

        for name in estimators:
            if(show): print("  Fitting and testing %s"%(name))
        
            #kwargs = copy.copy(estimators[name])
            #del kwargs["estimator"]
            #estimator = estimators[name]["estimator"](**kwargs)
            estimator = copy.deepcopy(estimators[name])
            estimator.fit(X_tr,Y_tr)
            fit_estimators[j][name]=estimator
        
            y_predict = estimator.predict(X_te)
            for i, metric in enumerate(metrics):
                val = metric(Y_te, y_predict) 
                report[m[i]].loc[name,j+1] = val             

    return {"report":report, "fit_estimators":fit_estimators}




def ExpWithin(*args, **kwargs):
    
    #Example of a node expander
    #Single function call returns a list of nodes
    #Calling function must accept a list of nodes
    
    if("n_folds" in kwargs):
        n_folds = kwargs["n_folds"]
    else:
        n_folds = 5
    
    args       = list(args)
    estimators = copy.copy(args[1])
    
    node_list = []
    for k in range(n_folds):
        for estimator in estimators:
            new_estimator  = {estimator: estimators[estimator]}
            args[1]        = new_estimator
            kwargs["fold"] = k
            name           = "EXP-Within(%d): %s"%(k+1, estimator)
            node_list.append(node(function = __ExpWithin, args=copy.copy(args), kwargs=copy.copy(kwargs), name=name))
    
    return node_list

    
def __ExpWithin(df, estimators, metrics=(), random_state=11, partition_index_number=0, fold=None,n_folds=None, key="dataframe",train_size=.8,split="temporal", show=False):
    
    df   = df[key]    

    #Get train and test sets for one individual
    index = df.index.names
    partition_index = index[partition_index_number]
    ids = list(set(df.index.get_level_values(partition_index)))
    df = df.loc[ids[fold]]
    #X, Y = df_to_sk(df)
    
    if(split=="random"):
        df_tr,df_te=train_test_split(df, train_size=train_size,test_size=1-train_size, random_state=random_state) 

    elif(split=="temporal"):
        train_size = int(train_size*df.shape[0])
        df_tr = df[:train_size]
        df_te = df[train_size:]
        
    else:
        raise ValueError("Split type % s is not defined"%split)

    X_tr, Y_tr = df_to_sk(df_tr)
    X_te, Y_te = df_to_sk(df_te)
        
    #Prepare multi-level report 
    m = list(map(lambda x: str(x.__name__), metrics))
    folds = [fold+1] 
    
    methods = list(estimators.keys())
    tuples  = itertools.product(methods,folds) 
    index   = pd.MultiIndex.from_tuples(tuples, names=['Method', 'Individual'])
    report  = pd.DataFrame(columns=m, index=index, dtype=float)
    
    fit_estimators=[{}]*n_folds
    
    for name in estimators:
        if(show): print("  Fitting and testing %s"%(name))
    
        #kwargs = copy.copy(estimators[name])
        #del kwargs["estimator"]
        #estimator = estimators[name]["estimator"](**kwargs)
        estimator = copy.deepcopy(estimators[name])
        estimator.fit(X_tr,Y_tr)
        fit_estimators[fold][name]=estimator
    
        y_predict = estimator.predict(X_te)
        for i, metric in enumerate(metrics):
            val = metric(Y_te, y_predict) 
            report[m[i]].loc[name,fold+1] = val             

    return {"report":report, "fit_estimators":fit_estimators}


