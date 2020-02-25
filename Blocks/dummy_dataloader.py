from Workflow.compute_graph import node

import pandas as pd
import time
import numpy as np

###The dummy data loader is used to remove dependency on file reads in the dataloader step. It generates a random dataframe to be processed
def dummy_data_loader(**kwargs):
    return node(function = __dummy_data_loader, kwargs=kwargs, name=" Dummy Data Loader")

def __dummy_data_loader():
    col_list = []
    for i in range(100):
        col_list.append(str(i))
    #print(len(col_list))
    X = np.random.normal(0,100,size=(1000000,100))
    z = np.ones(X.shape[0])
    for i in range(X.shape[1]):
        z += (i+1)*X[:,i]
    pr = 1/(1+np.exp(-z))
    y = np.random.binomial(1,pr)
    print(X.shape, y.shape)

    df = pd.DataFrame(X, columns=col_list)
    # df=df.rename(index=str, columns={"199": "target"})
    df2 = pd.DataFrame(y, columns=['target'])
    df = pd.concat([df, df2], axis=1, sort=False)
    # df = pd.DataFrame(np.random.randint(0,100,size=(100, 4)), columns=list('ABCD'))
    df.index.names = ["ID"]

    return({"dataframe":df})