import os
import networkx as nx
import time
from concurrent import futures
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
        

def run(flow, backend="sequential", num_workers=1, monitor=False, from_scratch=False):
    
    # for id in flow.graph.nodes():
    #     node=flow.graph.nodes[id]
    #     flow.set_status(node,"notscheduled")
    
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
    # if(monitor==False): 
    #     print("Running Sequential Scheduler\n")
    # else:
    if monitor:
        from IPython import display
        display.clear_output()
    
    # for id in flow.graph.nodes():
    #     node=flow.graph.nodes[id]
    #     flow.set_status(node,"notscheduled")
    
    exectute_order = list(nx.topological_sort(flow.graph))
    completed_nodes=[]

    for i,id in enumerate(exectute_order):
        
        if from_scratch or flow.graph.nodes[id]["block"].out is None:    
            if(monitor==False): print("Running step %s"%flow.graph.nodes[id]["block"].name)
            flow.set_status(flow.graph.nodes[id], "running")
            if(monitor): flow.draw(refresh=True)                        
            flow.graph.nodes[id]["block"].run()
            flow.set_status(flow.graph.nodes[id], "done")                
            if(monitor==False): print("")
            completed_nodes.append(id)

        for id in completed_nodes:
            this_node = flow.graph.nodes[id]
            if( (this_node["block"].out is not None) and (this_node["block"].is_output==False)):
                all_done=True
                for child_id in flow.graph.neighbors(id):
                    child = flow.graph.nodes[child_id] 
                    if child["block"].status != "done":
                        all_done=False
                if(all_done):
                    this_node["block"].out = None
                    this_node["fillcolor"]="grey"
                        
        if(monitor): flow.draw() 
    
    if(monitor==False): print("Workflow complete\n")                            
    return({n.out_tag: n.out for n in flow.out_nodes})


### Runs the pipelined graph in sequential order
def run_pipeline(flow, data=None, monitor=False,from_scratch=False):
    import os
    # if(monitor==False): print("Running Sequential Scheduler\n")

    exectute_order = list(nx.topological_sort(flow.pipelineGraph))

    for i,id in enumerate(exectute_order):
        if from_scratch or flow.pipelineGraph.nodes[id]["block"].out is None:    
            if(monitor==False): print("Running step %s"%flow.pipelineGraph.nodes[id]["block"].name)
            flow.set_status(flow.pipelineGraph.nodes[id], "running")
            if(monitor): flow.drawPipelined(refresh=True)                   
            flow.pipelineGraph.nodes[id]["block"].run()
            flow.set_status(flow.pipelineGraph.nodes[id], "done")                
            
    flow.set_status(flow.pipelineGraph.nodes[id], "done")
    if(monitor): flow.drawPipelined() 
    
    if(monitor==False):print("Workflow complete\n")                            
    return({n.out_tag: n.out for n in flow.out_nodes})
    
def run_parallel(flow,data=None,backend="multithread",num_workers=1,monitor=False,from_scratch=False):
    
    # if(monitor==False): print("Running Parallel Scheduler\n")
    
    # for id in flow.pipelineGraph.nodes():
    #     node=flow.pipelineGraph.nodes[id]
    #     flow.set_status(node,"notscheduled")
    
    nodes_waiting   = list(flow.graph.nodes)
    nodes_done      = []
    nodes_scheduled = []
    nodes_running   = []
    active_futures  = []
        
    no_parents    = True
    flow.parents  = {}

    par_out = {}
    times  = {}
    
    if(monitor):
        flow.draw(refresh=True)
    
    if(backend=="multithread"):
        ex = futures.ThreadPoolExecutor(max_workers=num_workers) 
    elif(backend=="multiprocess"):
        ex = futures.ProcessPoolExecutor(max_workers=num_workers)
    else:
        raise ValueError("Backend type is not known")


    done=False
    while not all(flow.graph.nodes[id]["block"].status=="done" for id in flow.graph.nodes):

        #Scheduling loop
        for id in list(flow.graph.nodes):

            this_block = flow.graph.nodes[id]["block"]
            this_node  = flow.graph.nodes[id]
            updated    = False

            #Node has no future set yet, see if it can run
            if(this_block.future is None):
                parents = list(flow.graph.predecessors(id))
                if(len(parents)==0 or all(flow.graph.nodes[p]["block"].status=="done" for p in parents)):
                    updated=True
                    if from_scratch or this_block.out is None:
                        #Submit the function to run
                        args   = this_block.get_args()
                        kwargs = this_block.get_kwargs()
                        this_block.out=None
                        this_block.future = ex.submit(this_block.function, *args, **kwargs)   
                    else:
                        #Already have cached outout, submit a dummy function
                        this_block.future = ex.submit(lambda: 0)   
                    flow.set_status(this_node, "scheduled")

        #Show new scheduled nodes
        if(monitor and updated):
            flow.draw(refresh=True)  

        #Wait until first scheduled job finishes or timeout, then process nodes
        active_nodes = [ id for id in flow.graph.nodes if flow.graph.nodes[id]["block"].status=="scheduled" ]
        active_nodes = active_nodes+[ id for id in flow.graph.nodes if flow.graph.nodes[id]["block"].status=="running" ] 
        active_futures = [flow.graph.nodes[id]["block"].future for id in active_nodes]
        running_nodes  = [[flow.graph.nodes[id]["block"].name,flow.graph.nodes[id]["block"].future.__dict__] for id in active_nodes]
        #print(running_nodes)
        #print(ex.__dict__)

        if(len(active_futures )>0):
            futures.wait(active_futures, timeout=1, return_when=futures.FIRST_COMPLETED)
        else:   
            time.sleep(0.5) 

        #Node status update loop            
        for id in list(flow.graph.nodes):

            this_block = flow.graph.nodes[id]["block"]
            this_node  = flow.graph.nodes[id]

            if(this_block.future is not None):

                #Future is in running state but node state is not running
                if this_block.future.running() and this_block.status!="running":
                    updated=True
                    flow.set_status(this_node, "running")
                    
                #Future is in done state but node state is not done
                elif this_block.future.done() and this_block.status!="done":
                    updated=True
                    flow.set_status(this_node, "done")
                    if this_block.out is None:
                        this_block.out=this_block.future.result()
                    else:
                        res=this_block.future.result()

                #If state is not done or running, error
                elif (not this_block.future.done()) and (not this_block.future.running()) and (not this_block.future._state=="PENDING"):
                    print(this_block.future._state)
                    raise ValueError("Future state is not running, done or pending")

                #Future is in done state and node state is done and output is still set and not a flow output
                '''
                elif this_block.future.done() and (this_block.status=="done") and (this_block.out is not None) and (this_block.is_output==False):

                    all_done=True
                    for child_id in flow.graph.neighbors(id):
                        child = flow.graph.nodes[child_id] 
                        if child["block"].status != "done":
                            all_done=False
                    if(all_done):
                        updated=True
                        this_block.out = None
                        this_node["fillcolor"]="grey" 
                '''
                    
        if(monitor and updated):
            flow.draw(refresh=True)               

        print('.',end="",flush=True)

    
    if(monitor):                 
        flow.draw(refresh=False)    
    else:
        print("Workflow complete\n") 
    
    ex.shutdown(wait=True)
    return({n.out_tag: n.out for n in flow.out_nodes})

'''
def run_parallel(flow,data=None,backend="multithread",num_workers=1,monitor=False,from_scratch=False):
    
    if(monitor==False): print("Running Parallel Scheduler\n")
    
    for id in flow.pipelineGraph.nodes():
        node=flow.pipelineGraph.nodes[id]
        flow.set_status(node,"notscheduled")
    
    nodes_waiting   = list(flow.graph.nodes)
    nodes_done      = []
    nodes_scheduled = []
    nodes_running   = []
    active_futures  = []
        
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
    
        completed_nodes=[]
        while len(nodes_waiting)+len(nodes_scheduled)+len(nodes_running)>0: 
            
            #Schedule nodes whose parents have all completed
            changed=False
            for node in nodes_waiting:
                parents = list(flow.graph.predecessors(node))
                if(len(parents)==0 or all(x in nodes_done for x in parents)):
                    changed=True                        
                    nodes_waiting.remove(node)
                    if from_scratch or flow.graph.nodes[node]["block"].out is None:
                        nodes_scheduled.append(node)
                         
                        args   = flow.graph.nodes[node]["block"].get_args()
                        kwargs = flow.graph.nodes[node]["block"].get_kwargs()
                        f      = ex.submit(flow.graph.nodes[node]["block"].function, *args, **kwargs)
                        par_out[node]=f
                        active_futures.append(f)
                        
                        flow.set_status(flow.graph.nodes[node], "scheduled")
                        
                        if(monitor==False): print("Scheduled:", flow.graph.nodes[node]["block"].name)
                    else:
                        nodes_done.append(node)
                        flow.set_status(flow.graph.nodes[node], "done")
                        if(monitor==False): print("Done:", flow.graph.nodes[node]["block"].name)                       

            if(monitor and changed):
                flow.draw(refresh=True)

            #Wait until first scheduled job finishes, then process nodes
            #res = futures.wait(active_futures, timeout=0.4, return_when=futures.FIRST_COMPLETED)
            #active_futures = list(res.not_done)

            #Check for nodes moved to running state
            changed=False
            for node in nodes_scheduled:
                if par_out[node].running() or par_out[node].done():
                    changed=True
                    nodes_running = nodes_running + [node]
                    nodes_scheduled.remove(node) 
                    flow.set_status(flow.graph.nodes[node], "running")
                    if(monitor==False): print("Running:", flow.graph.nodes[node]["block"].name)

            if(monitor and changed):
                flow.draw(refresh=True) 

            #Check for nodes that are done
            changed=False
            for node in nodes_running:
                if par_out[node].done():
                    changed=True
                    flow.graph.nodes[node]["block"].out=par_out[node].result() 
                    nodes_done = nodes_done + [node]
                    nodes_running.remove(node)  
                    flow.set_status(flow.graph.nodes[node], "done")
                    completed_nodes.append(node)
                    if(monitor==False): print("Done:", flow.graph.nodes[node]["block"].name)

            if(monitor and changed):
                flow.draw(refresh=True)

            #Remove result output from nodes that are not workflow outputs
            #and whose children have all completed running.
            if(changed):
                changed = False
                for id in completed_nodes:
                    this_node = flow.graph.nodes[id]
                    if( (this_node["block"].out is not None) and (this_node["block"].is_output==False)):
                        all_done=True
                        for child_id in flow.graph.neighbors(id):
                            child = flow.graph.nodes[child_id] 
                            if child["block"].status != "done":
                                all_done=False
                        if(all_done):
                            this_node["block"].out = None
                            this_node["fillcolor"]="grey"
                            changed=True

                if(monitor and changed):
                    flow.draw(refresh=True)
            
            time.sleep(0.5) 
            print('.',end="",flush=True)

    for node in list(set(list(flow.graph.nodes)) - set(nodes_done)):
        flow.set_status(flow.graph.nodes[node], "done")
        flow.graph.nodes[node]["block"].out=par_out[node].result() 
    
    if(monitor):                 
        flow.draw(refresh=False)    
    else:
        print("Workflow complete\n") 
                       
    return({n.out_tag: n.out for n in flow.out_nodes})
    '''

### Runs the pipelined graph in parallel, either in multithreaded or multiprocessed configurations depending on the flag
def run_parallel_pipeline(flow,data=None,backend="multithread_pipeline",num_workers=1,monitor=False,from_scratch=False, refresh_rate=0.05):
    
    # if(monitor==False): print("Running Parallel Pipeline Scheduler\n")
    
    # for id in flow.pipelineGraph.nodes():
    #     node=flow.pipelineGraph.nodes[id]
    #     flow.set_status(node,"notscheduled")
    
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
                    if from_scratch or flow.pipelineGraph.nodes[node]["block"].out is None:
                        nodes_scheduled.append(node)
                         
                        # args   = flow.pipelineGraph.nodes[node]["block"].get_args()
                        # kwargs = flow.pipelineGraph.nodes[node]["block"].get_kwargs()
                        # print("here")
                        f      = ex.submit(flow.pipelineGraph.nodes[node]["block"].run)
                        par_out[node]=f
                        
                        flow.set_status(flow.pipelineGraph.nodes[node], "scheduled")
                        
                        if(monitor==False): print("Scheduled:", flow.pipelineGraph.nodes[node]["block"].name)
                    else:
                        nodes_done.append(node)
                        flow.set_status(flow.pipelineGraph.nodes[node], "done")
                        if(monitor==False): print("Done:", flow.pipelineGraph.nodes[node]["block"].name)                       

            for node in nodes_scheduled[:]:
                if par_out[node].running() or par_out[node].done():
                    changed=True
                    nodes_running = nodes_running + [node]
                    nodes_scheduled.remove(node) 
                    flow.set_status(flow.pipelineGraph.nodes[node], "running")

                    #if(monitor==False): print("Running:", flow.pipelineGraph.nodes[node]["block"].name)
                        
            for node in nodes_running[:]:
                if par_out[node].done():
                    changed=True
                    if(monitor==False and par_out[node].exception() is not None): print(par_out[node].exception())
                    flow.pipelineGraph.nodes[node]["block"].out=par_out[node].result()
                    flow.graph.nodes[flow.pipelineGraph.nodes[node]["block"].tail]["block"].out = par_out[node].result()
                    nodes_done = nodes_done + [node]
                    nodes_running.remove(node)  
                    
                    flow.set_status(flow.pipelineGraph.nodes[node], "done")                
                    if(monitor==False): print("Done:", flow.pipelineGraph.nodes[node]["block"].name)
                    
            if(monitor and changed and time.time()-time_start>refresh_rate):
                flow.drawPipelined(refresh=True)
                time_start = time.time()  
            
            time.sleep(0.5) 
            print('.',end="",flush=True)
            
    for node in list(set(list(flow.pipelineGraph.nodes)) - set(nodes_done)):
        flow.set_status(flow.graph.nodes[node], "done")
        flow.graph.nodes[node]["block"].out=par_out[node].result() 
    
    if(monitor):                 
        flow.drawPipelined(refresh=False)    
    if(monitor==False):print("Workflow complete\n") 
                       
    return({n.out_tag: n.out for n in flow.out_nodes})
