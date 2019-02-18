
import networkx as nx
import time
from concurrent import futures
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
        

def run(flow, backend="sequential", num_workers=1, monitor=False, from_scratch=False):
    
    print("Running Scheduler", backend)
    
    if(backend=="sequential"):
        return run_sequential(flow,monitor=monitor,from_scratch=from_scratch)
    elif(backend=="multithread" or backend=="multiprocess"):
        return run_parallel(flow, backend=backend, num_workers=num_workers,monitor=monitor,from_scratch=from_scratch)   


def run_sequential(flow, data=None, monitor=False,from_scratch=False):

    print("  Running Sequential Scheduler\n")

    exectute_order = list(nx.topological_sort(flow.graph))

    for i,id in enumerate(exectute_order):
        
        if from_scratch or low.graph.node[id]["block"].out is None:    
            print("Running step %s"%flow.graph.node[id]["block"].name)
            flow.set_status(flow.graph.node[id], "running")
            if(monitor): flow.draw(refresh=True)                        
            flow.graph.node[id]["block"].run()
            flow.set_status(flow.graph.node[id], "done")                
            print("")
            
    flow.set_status(flow.graph.node[id], "done")
    if(monitor): flow.draw() 
    
    print("  Workflow complete\n")                            
    return({n.name: n.out for n in flow.out_nodes})
    
def run_parallel(flow,data=None,backend="multithread",num_workers=1,monitor=False,from_scratch=False):
    
    print("  Running Parallel Scheduler\n")
    
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
    print("  Workflow complete\n") 
                       
    return({n.name: n.out for n in flow.out_nodes})
