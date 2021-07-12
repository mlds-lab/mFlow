
import networkx as nx
import time
from concurrent import futures
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
        

def run(flow, backend="sequential", num_workers=1, monitor=False, from_scratch=False):
    
    for id in flow.graph.nodes():
        node=flow.graph.nodes[id]
        flow.set_status(node,"notscheduled")
    
    if(backend=="sequential"):
        return run_sequential(flow,monitor=monitor,from_scratch=from_scratch)
    elif(backend=="multithread" or backend=="multiprocess"):
        return run_parallel(flow, backend=backend, num_workers=num_workers,monitor=monitor,from_scratch=from_scratch) 
    elif(backend == "pipeline"):
        return run_pipeline(flow, monitor=monitor,from_scratch=from_scratch)
    elif(backend=="multithread_pipeline" or backend=="multiprocess_pipeline"):
        return run_parallel_pipeline(flow, backend=backend, num_workers=num_workers,monitor=monitor,from_scratch=from_scratch)  


def run_sequential(flow, data=None, monitor=False,from_scratch=False):
    import os
    if(monitor==False): print("Running Sequential Scheduler\n")
    
    for id in flow.graph.nodes():
        node=flow.graph.nodes[id]
        flow.set_status(node,"notscheduled")
    
    exectute_order = list(nx.topological_sort(flow.graph))

    for i,id in enumerate(exectute_order):
        
        if from_scratch or flow.graph.nodes[id]["block"].out is None:    
            if(monitor==False): print("Running step %s"%flow.graph.nodes[id]["block"].name)
            flow.set_status(flow.graph.nodes[id], "running")
            if(monitor): flow.draw(refresh=True)                        
            flow.graph.nodes[id]["block"].run()
            flow.set_status(flow.graph.nodes[id], "done")                
            if(monitor==False): print("")
            
    flow.set_status(flow.graph.nodes[id], "done")
    if(monitor): flow.draw() 
    
    if(monitor==False): print("Workflow complete\n")                            
    return({n.name: n.out for n in flow.out_nodes})


### Runs the pipelined graph in sequential order
def run_pipeline(flow, data=None, monitor=False,from_scratch=False):
    import os
    if(monitor==False): print("Running Sequential Scheduler\n")

    
    # print(os.environ["MKL_NUM_THREADS"])
    exectute_order = list(nx.topological_sort(flow.pipelineGraph))
    # print(exectute_order)

    for i,id in enumerate(exectute_order):
        # print(flow.pipelineGraph.node[id]["block"].out)
        if from_scratch or flow.pipelineGraph.node[id]["block"].out is None:    
            print("Running step %s"%flow.pipelineGraph.node[id]["block"].name)
            flow.set_status(flow.pipelineGraph.node[id], "running")
            if(monitor): flow.drawPipelined(refresh=True)
            # print(flow.pipelineGraph.node[id]["block"].name)                     
            flow.pipelineGraph.node[id]["block"].run()
            flow.set_status(flow.pipelineGraph.node[id], "done")                
            print("")
            
    flow.set_status(flow.pipelineGraph.node[id], "done")
    if(monitor): flow.drawPipelined() 
    
    if(monitor==False):print("Workflow complete\n")                            
    return({n.name: n.out for n in flow.out_nodes})
    
def run_parallel(flow,data=None,backend="multithread",num_workers=1,monitor=False,from_scratch=False):
    
    if(monitor==False): print("Running Parallel Scheduler\n")
    
    for id in flow.pipelineGraph.nodes():
        node=flow.pipelineGraph.node[id]
        flow.set_status(node,"notscheduled")
    
    nodes_waiting   = list(flow.graph.nodes)
    nodes_done      = []
    nodes_scheduled = []
    nodes_running   = []
        
    no_parents    = True
    flow.parents  = {}
    

    par_out = {}
    times  = {}
    
    if(monitor):
        flow.draw(refresh=True)
    
    if(backend=="multithread"):
        executor = futures.ThreadPoolExecutor(max_workers=num_workers) 
    elif(backend=="multiprocess"):
        executor = futures.ProcessPoolExecutor(max_workers=num_workers)
    else:
        raise
    
    with executor as ex:
    
        while len(nodes_waiting)+len(nodes_scheduled)+len(nodes_running)>0: 
            
            changed=False
                   
            for node in nodes_waiting:
                parents = list(flow.graph.predecessors(node))
                if(len(parents)==0 or all(x in nodes_done for x in parents)):
                    changed=True                        
                    nodes_waiting.remove(node)
                    if from_scratch or flow.graph.node[node]["block"].out is None:
                        nodes_scheduled.append(node)
                         
                        args   = flow.graph.node[node]["block"].get_args()
                        kwargs = flow.graph.node[node]["block"].get_kwargs()
                        f      = ex.submit(flow.graph.node[node]["block"].function, *args, **kwargs)
                        par_out[node]=f
                        
                        flow.set_status(flow.graph.node[node], "scheduled")
                        
                        
                        print("Scheduled:", flow.graph.node[node]["block"].name)
                    else:
                        nodes_done.append(node)
                        flow.set_status(flow.graph.node[node], "done")
                        print("Done:", flow.graph.node[node]["block"].name)                       

            for node in nodes_scheduled:
                if par_out[node].running() or par_out[node].done():
                    changed=True
                    nodes_running = nodes_running + [node]
                    nodes_scheduled.remove(node) 
                    flow.set_status(flow.graph.node[node], "running")

                    print("Running:", flow.graph.node[node]["block"].name)
                        
            for node in nodes_running:
                if par_out[node].done():
                    changed=True
                    flow.graph.node[node]["block"].out=par_out[node].result() 
                    nodes_done = nodes_done + [node]
                    nodes_running.remove(node)  
                    flow.set_status(flow.graph.node[node], "done")
                                    
                    print("Done:", flow.graph.node[node]["block"].name)
                    
            if(monitor and changed):
                flow.draw(refresh=True)
                
            time.sleep(0.1) 
            
    for node in list(set(list(flow.graph.nodes)) - set(nodes_done)):
        flow.set_status(flow.graph.node[node], "done")
        flow.graph.node[node]["block"].out=par_out[node].result() 
    
    if(monitor):                 
        flow.draw(refresh=False)    
    if(monitor==False): print("Workflow complete\n") 
                       
    return({n.name: n.out for n in flow.out_nodes})



### Runs the pipelined graph in parallel, either in multithreaded or multiprocessed configurations depending on the flag
def run_parallel_pipeline(flow,data=None,backend="multithread_pipeline",num_workers=1,monitor=False,from_scratch=False, refresh_rate=0.05):
    
    if(monitor==False): print("Running Parallel Pipeline Scheduler\n")
    
    for id in flow.pipelineGraph.nodes():
        node=flow.pipelineGraph.node[id]
        flow.set_status(node,"notscheduled")
    
    nodes_waiting   = list(flow.pipelineGraph.nodes)
    nodes_done      = []
    nodes_scheduled = []
    nodes_running   = []
        
    no_parents    = True
    flow.parents  = {}
    

    par_out = {}
    times  = {}
    
    if(monitor):
        flow.drawPipelined(refresh=True)
    
    if(backend=="multithread_pipeline"):
        executor = futures.ThreadPoolExecutor(max_workers=num_workers) 
    elif(backend=="multiprocess_pipeline"):
        executor = futures.ProcessPoolExecutor(max_workers=num_workers)
    else:
        raise
    
    time_start = time.time()
    
    with executor as ex:
    
        while len(nodes_waiting)+len(nodes_scheduled)+len(nodes_running)>0: 
            
            changed=False
                   
            for node in nodes_waiting[:]:
                parents = list(flow.pipelineGraph.predecessors(node))
                if(len(parents)==0 or all(x in nodes_done for x in parents)):
                    changed=True                        
                    nodes_waiting.remove(node)
                    if from_scratch or flow.pipelineGraph.node[node]["block"].out is None:
                        nodes_scheduled.append(node)
                         
                        # args   = flow.pipelineGraph.node[node]["block"].get_args()
                        # kwargs = flow.pipelineGraph.node[node]["block"].get_kwargs()
                        # print("here")
                        f      = ex.submit(flow.pipelineGraph.node[node]["block"].run)
                        par_out[node]=f
                        
                        flow.set_status(flow.pipelineGraph.node[node], "scheduled")
                        
                        if(monitor==False): print("Scheduled:", flow.pipelineGraph.node[node]["block"].name)
                    else:
                        nodes_done.append(node)
                        flow.set_status(flow.pipelineGraph.node[node], "done")
                        if(monitor==False): print("Done:", flow.pipelineGraph.node[node]["block"].name)                       

            for node in nodes_scheduled[:]:
                if par_out[node].running() or par_out[node].done():
                    changed=True
                    nodes_running = nodes_running + [node]
                    nodes_scheduled.remove(node) 
                    flow.set_status(flow.pipelineGraph.node[node], "running")

                    #if(monitor==False): print("Running:", flow.pipelineGraph.node[node]["block"].name)
                        
            for node in nodes_running[:]:
                if par_out[node].done():
                    changed=True
                    if(monitor==False and par_out[node].exception() is not None): print(par_out[node].exception())
                    flow.pipelineGraph.node[node]["block"].out=par_out[node].result()
                    flow.graph.node[flow.pipelineGraph.node[node]["block"].tail]["block"].out = par_out[node].result()
                    nodes_done = nodes_done + [node]
                    nodes_running.remove(node)  
                    
                    flow.set_status(flow.pipelineGraph.node[node], "done")                
                    if(monitor==False): print("Done:", flow.pipelineGraph.node[node]["block"].name)
                    
            if(monitor and changed and time.time()-time_start>refresh_rate):
                flow.drawPipelined(refresh=True)
                time_start = time.time()  
            
            time.sleep(0.01) 
            
    for node in list(set(list(flow.pipelineGraph.nodes)) - set(nodes_done)):
        flow.set_status(flow.graph.node[node], "done")
        flow.graph.node[node]["block"].out=par_out[node].result() 
    
    if(monitor):                 
        flow.drawPipelined(refresh=False)    
    if(monitor==False):print("Workflow complete\n") 
                       
    return({n.name: n.out for n in flow.out_nodes})
