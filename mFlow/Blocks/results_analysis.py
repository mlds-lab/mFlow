import sys, os
from mFlow.Workflow.compute_graph import node
import pandas as pd

def ResultsConcat(*args, **kwargs):
    
    new_args = []
    for arg in args:
        if(type(arg)==list):
            new_args = new_args + arg
        else:
            new_args.append(arg)    
            
    return node(function = __ResultsConcat, args=new_args, kwargs=kwargs, name="Results Concat")
            
def __ResultsConcat(*args,inplace=True, show=False):
    if(show): print("  Concatenating Results")
    
    results = [x["report"] for x in args]
    df = pd.concat(results)
    
    if(show):
        display(df)
    
    return({"report": df})

def ResultsCVSummarize(*args, **kwargs):
    return node(function = __ResultsCVSummarize, args=args, kwargs=kwargs, name="Results CV Summarize")
 
def __ResultsCVSummarize(*args,inplace=True, show=False):
     if(show): print("  Summarizing CV results table")
    
     #Get one CV report as input
     report = args[0]["report"]
     m = list(report.columns)
     
     #Collapse out folds and summarize as mean and sem
     metric_conv = {}
     for metric_name in m:
          metric_conv[metric_name] = ['mean', 'sem']
     summary_report = report.groupby("Method").agg(metric_conv)

     if(show):
        display(summary_report)
    
     return({"report": summary_report})
     
def DataYieldReport(*args, **kwargs):

    return node(function = __DataYieldReport, args=args, kwargs=kwargs, name="Data Yield Analysis")
    
def __DataYieldReport(*args, names=None, show=False):
    
    num_instances   = []
    num_features    = []
    num_instances   = []
    num_individuals = []
    num_idividuals_with_data = []
    num_observed_feature_values = []
    num_observed_label_values = []
    observed_feature_rate = []
    observed_label_rate =[]
    
    for i,frame in enumerate(args):
        
        df = frame["dataframe"]
        features = list(set(df.columns) - {'target'})

        num_instances.append(df[features].shape[0])
        num_features.append(df[features].shape[1])
        num_individuals.append(len(df.index.levels[0]))
        
        num_idividuals_with_data.append(len(list(set(df.index.get_level_values(0)))))

        num_observed_feature_values.append( df[features].notna().sum().sum())
        num_observed_label_values.append(df["target"].notna().sum().sum())

        observed_feature_rate.append(100*num_observed_feature_values[-1]/(num_instances[-1]*num_features[-1]))
        observed_label_rate.append(100*num_observed_label_values[-1]/num_instances[-1])
            
    d = {"#Individuals": num_individuals,
         "#Individuals with Data": num_idividuals_with_data,
         "#Instances": num_instances,
         "#Labeled Instances": num_observed_label_values,
         "%Labeled Instances": observed_label_rate,
         "#Features": num_features,
         "#Observed Feature Values": num_observed_feature_values,
         "%Observed Feature Values": observed_feature_rate}

    if(names is not None):
        report = pd.DataFrame(d, index=names)
    else:
        report = pd.DataFrame(d)
        
    report=report.round(2)
    
    if(show):
        display(report)
    
    return({"report": report,"lists":d})