import copy
import time

class node():
    def __init__(self, isPipelineNode=False, function=None, args=[], kwargs={}, name=None, parents=[], initGraph=None, node_list=[], id=""):
        
        if isPipelineNode:
            self.init_pipeline_node(initGraph, node_list, id)
        else:
            self.init_node(function, args, kwargs, name, parents)

        self.isPipelineNode = isPipelineNode
        # print (self.isPipelineNode, isPipelineNode)

    def init_pipeline_node(self, initGraph, node_list, id):
        
        self.id = id
        self.head = node_list[0]
        self.tail = node_list[len(node_list)-1]
        self.name = ""
        self.node_list = node_list
        self.initGraph = initGraph
        
        for i, id in enumerate(node_list):
            self.name += initGraph.nodes[id]["block"].name
            if i != len(node_list)-1:
                self.name += "."
        self.out = None

    def init_node(self, function=None, args=[], kwargs={}, name=None, parents=[]):

        self.function = function
        self.args = list(args)
        self.kwargs = kwargs
        self.name = name
        self.is_output=False
        self.out = None
        self.status=None
        self.parents=parents
        self.args_parents = {}
        self.kwargs_parents = {}
        self.future=None
        
        self.long_name = ""

        #Trace parents and store
        for i,arg in enumerate(self.args):
            if type(arg)==type(self):
                # print(arg)
                self.args_parents[i]  = arg
                self.long_name += arg.long_name + "." 
                
        for kw in self.kwargs:
            if type(self.kwargs[kw])==type(self):
                self.kwargs_parents[kw]=self.kwargs[kw]
                self.long_name += self.kwargs[kw].long_name + "." 

    def run(self):            

        if self.isPipelineNode:
            time1 = time.time()
            if self.out is None:
                for node_id in self.node_list:
                    intermediate_out = self.initGraph.nodes[node_id]["block"].run()
                self.out = intermediate_out
                #print("Time taken by "+ str(self.initGraph.node[node_id]["block"].name) + " : " + str(time.time()-time1))
        else:
            for i in self.args_parents:
                self.args[i]=self.args_parents[i].out
            for kw in self.kwargs_parents:
                self.kwargs[kw]=self.kwargs_parents[kw].out

            self.out = self.function(*self.args, **self.kwargs)

        return (self.out)
            
    def get_args(self):
        for i in self.args_parents:
            self.args[i]=self.args_parents[i].out
        return  self.args   
        
    def get_kwargs(self): 
        for kw in self.kwargs_parents:
            self.kwargs[kw]=self.kwargs_parents[kw].out      
        return  self.kwargs