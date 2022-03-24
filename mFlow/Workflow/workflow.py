
import networkx as nx
import time
from concurrent import futures
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
from networkx.generators.triads import triad_graph
import mFlow.Workflow.scheduler as scheduler
from mFlow.Workflow.compute_graph import node #pipelineNode
import os
        
class workflow():

    def __init__(self, nodes={}):
        
        '''
        Workflow constructor
        
        Args:
            nodes (dict): a dictionary of workflow output nodes. Keys are used as tags
            to identify outputs.
        '''

        self.graph=nx.DiGraph()
        self.labels={}
        self.out_nodes = []
        self.pipeline_dict = {}
        self.pipelineGraph = nx.DiGraph()
        #If have compute nodes, add to graph
        #along with all parents

        for tag in nodes:
            node = nodes[tag]
            self.add_output(node, tag)
        self.pipeline(self.graph)

    def add_output(self, node, tag):
        '''
        Adds the given workflow node to the set of workflow outputs with the given tag,
        then adds all of the node's ancestors to the workflow.
        
        
        Args:
            node: a workflow node
            tag: a string to identifiy the node
        '''
        
        node.out_tag = tag
        node.is_output=True
        self.add(node)

    def add(self, nodes):
        '''
        Adds the given list of workflow nodes to the workflow, along with all
        of their ancestors. Sets the out_tag property of the nodes if not
        already set.
        
        Args:
            nodes: a list of workflow nodes (or a single workflow node).
        '''
        
        if type(nodes) is not list:
            nodes=[nodes]
        self.out_nodes = self.out_nodes + nodes
        for node in nodes: 
            if(not hasattr(node,"out_tag")):
                node.out_tag = node.name           
            self.recursive_add_node(node)

    def remove(self, nodes):
        '''
        Removes the given workflow nodes from the workflow, along with all of their
        descendents.
        
        Args:
            nodes: a list of workflow nodes (or a single workflow node).
        '''        

        if type(nodes) is not list:
            nodes = [nodes]
        
        for node in nodes:
            node_id = str(id(node))
            
            #print("  Removing: ", node.name, node_id)
            
            if node_id in self.graph.nodes():
                
                #Get descendents
                descendants = nx.descendants(self.graph,source=node_id)

                #Remove node from graph
                self.graph.remove_node(node_id)            
                if(node in self.out_nodes):
                    self.out_nodes.remove(node)
            
                #Remove any descendents from graph
                for descendant_id in descendants:
                    this_node = self.graph.nodes[descendant_id]["block"]
                    print("  Removing: ", this_node.name, descendant_id)
                
                    self.graph.remove_node(descendant_id)
                    if(this_node in self.out_nodes):
                        self.out_nodes.remove(this_node)                



    def recursive_add_node(self, node):
        
        '''
        Adds the given list of workflow nodes to the workflow, along with all
        of their ancestors. If the node is already in the workflow, does
        not add duplicates.
        
        Args:
            nodes: a list of workflow nodes.
        '''
        
        #Get node name and ID
        node_id = str(id(node))
        # print(str(id(node)))
        if node_id in self.graph.nodes(): #list(self.blocks.keys()):
            #If node exists, do not add agan,
            #just return node name
            return(node_id)
        else:
            
            #If node does not exist, add to graph
            self.add_node(node_id, node)
            
            #Check for all nodes that are parents in args list
            #and add, with edges to this node              
            for i in node.args_parents:
                parent_id = self.recursive_add_node(node.args_parents[i])
                self.graph.add_edge(parent_id, node_id)
            
            #Check for all nodes that are parents in kwargs list
            #and add, with edges to this node           
            for kw in node.kwargs_parents:
                parent_id = self.recursive_add_node(node.kwargs_parents[kw])
                self.graph.add_edge(parent_id, node_id)
            
            return(node_id)      
    
    def add_node(self, name, block):
        '''
        Adds a node to the workflow with a specified name and block.
        
        Args:
            name (str): unique name for workflow node
            block: the workflow block for this node
        '''
        
        #self.blocks[name] = block
        self.graph.add_node(name, block=block, label=block.name, shape="box", style="filled", fillcolor="white",color="black", fontname="helvetica")
        self.labels[name] = block.name

    
    def add_edge(self, node_from, node_to):
        '''
        Add a directed edge between nodes
        
        Args:
            node_from: ID of from node
            node_to: ID of to node 
        '''
        
        self.graph.add_edge(node_from, node_to)
        
    def set_status(self,node,status):
        '''
        Set the status of a workflow node
        
        Args:
            node: a workflow node
            status (string): scheduled | notscheduled | running | done
        '''
        
        node["block"].status=status
        if(status=="scheduled"):
            node["fillcolor"]="lemonchiffon"
        elif(status=="notscheduled"):
            node["fillcolor"]="white"
        elif(status=="running"):
            node["fillcolor"]="palegreen3"
        elif(status=="done"):
            node["fillcolor"]="lightblue"
    
    def draw(self, refresh=True):
        '''
        Display the workflow graph in a Jupyter notebook
        
        Args:
            refresh (bool): If True, clear the cell before drawing.   
        '''
        import networkx as nx
        from networkx.drawing.nx_agraph import write_dot, graphviz_layout
        import matplotlib.pyplot as plt
        from IPython.display import Image, display,clear_output
        
        pdot = nx.drawing.nx_pydot.to_pydot(self.graph)
        pdot.set_rankdir("LR")
        
        if not os.path.exists("Temp"):
            os.mkdir("Temp")
        pdot.write_png("Temp/temp.png")

        if(refresh):
            clear_output(wait=True)
        display(Image(filename='Temp/temp.png')) 

    def drawPipelined(self, refresh=True):
        '''
        Display pipilined workflow graph in a Jupyter notebook.
        
        Args:
            refresh (bool): If True, clear the cell before drawing.   
        '''        
        
        import networkx as nx
        from networkx.drawing.nx_agraph import write_dot, graphviz_layout
        import matplotlib.pyplot as plt
        from IPython.display import Image, display,clear_output
        
        pdot = nx.drawing.nx_pydot.to_pydot(self.pipelineGraph)
        pdot.set_rankdir("LR")
        
        pdot.write_png("Temp/temp.png")

        if(refresh):
            clear_output(wait=True)
        display(Image(filename='Temp/temp.png'))     
    
    def run(self, backend="sequential", num_workers=1, monitor=False,from_scratch=False):
        '''
        Run the workflow with the specified backend scheduler. 
        
        Args:
            backend (string): The type of scheduling backend to use (sequential | multithread | multiprocess | pipeline | multithread_pipeline | multiprocess_pipeline). See mFlow.Workflow.scheduler for documentation.
            num_workers (int): Number of workers to use in parallel backends
            monitor (bool): If True, use graphical execution monitorin for Jupyter notebooks
            from_scratch (bool): If True, run the workflow from scratch, discarding any cached results.
        '''

        for id in self.graph.nodes():
            node=self.graph.nodes[id]
            self.set_status(node,"notscheduled")

        if not(monitor):
            print(f"Running {backend} Scheduler\n")
        
        return scheduler.run(self, backend=backend, num_workers=num_workers, monitor=monitor,from_scratch=from_scratch)

    def add_pipeline_node(self, id, plNode):
        '''
        Add a pipline node to pipeline workflow graph
 
        Args:
            id (string): id for the node
            plNode: pipelined workflow node
        '''       
        
        self.pipelineGraph.add_node(id, block=plNode, label=plNode.name, shape="box", style="filled", fillcolor="white",color="black", fontname="helvetica")

    def pipelineGraphCreate(self, process_dict):
        '''
        Convert a dictionary of pipelined workflow nodes to a pipelined workflow graph.
        
        Args:
            process_dict: dictionary of pipelined workflow nodes.
        '''

        pipelineNodeList = []
        for key in process_dict:
            # plNode = pipelineNode(self.graph, process_dict[key], key)
            plNode = node(isPipelineNode=True, initGraph=self.graph, node_list=process_dict[key], id=key)
            pipelineNodeList.append(plNode)
            self.add_pipeline_node(key, plNode)
        for plNode in pipelineNodeList:
            for plNode_adj in pipelineNodeList:
                # print(self.graph.node[plNode.tail]["block"])
                # print(list(self.graph.node[plNode_adj.head]["block"].args_parents.values()))
                # print("next")
                if self.graph.nodes[plNode.tail]["block"] in self.graph.nodes[plNode_adj.head]["block"].args_parents.values():
                    # print("1")
                    self.pipelineGraph.add_edge(plNode.id, plNode_adj.id)
        

    def pipeline(self, initGraph):
        '''
        Convert the given workflow graph to a pipelined representation where chanins in the workflow graph are replaced 
        by single node.
        
        Args:
            initGraph: A workflow graph.
        '''
        
        execute_order = list(nx.topological_sort(initGraph))
        # print("execute order : ")
        root_nodes = []
        for idx, id in enumerate(execute_order):            
            if len(list(initGraph.predecessors(id))) == 0:
                root_nodes.append(idx)
                #print(initGraph.node[id]["block"].name + str(id))
        node_lists = []
        for idx in root_nodes:
            node_lists.append(list(nx.dfs_preorder_nodes(initGraph, source=execute_order[idx])))
        process_dict = {}
        marked_nodes = []
        key_num = 0
        #print(node_lists)
        for node_list in node_lists:
            for id in node_list:
                marked_nodes.append(id)
                if len(list(initGraph.predecessors(id))) == 0:
                    # process_dict[key_num] = [initGraph.node[id]["block"].name]
                    process_dict[key_num] = [id]
                    if len(list(initGraph.successors(id))) == 1:
                        if list(initGraph.successors(id))[0] in marked_nodes:
                            key_num += 1
                    elif len(list(initGraph.successors(id))) == 0:
                        key_num += 1
                    elif len(list(initGraph.successors(id))) > 1:
                        key_num += 1
                        
                elif len(list(initGraph.predecessors(id))) == 1:
                    if len(list(initGraph.successors(id))) == 1:
                        if key_num not in process_dict.keys():
                            # process_dict[key_num] = [initGraph.node[id]["block"].name]
                            process_dict[key_num] = [id]
                        else:
                            # process_dict[key_num].append(initGraph.node[id]["block"].name)
                            process_dict[key_num].append(id)
                        if list(initGraph.successors(id))[0] in marked_nodes:
                            key_num += 1
                    elif len(list(initGraph.successors(id))) == 0:
                        if key_num not in process_dict.keys():
                            # process_dict[key_num] = [initGraph.node[id]["block"].name]
                            process_dict[key_num] = [id]
                            key_num += 1
                        else:
                            # process_dict[key_num].append(initGraph.node[id]["block"].name)
                            process_dict[key_num].append(id)
                            key_num += 1
                    elif len(list(initGraph.successors(id))) > 1:
                        if key_num not in process_dict.keys():
                            # process_dict[key_num] = [initGraph.node[id]["block"].name]
                            process_dict[key_num] = [id]
                        else:
                            # process_dict[key_num].append(initGraph.node[id]["block"].name)
                            process_dict[key_num].append(id)
                        key_num += 1
                            
                elif len(list(initGraph.predecessors(id))) > 1:
                    key_num += 1
                    if len(list(initGraph.successors(id))) == 1:
                        # process_dict[key_num] = [initGraph.node[id]["block"].name]
                        process_dict[key_num] = [id]
                        if list(initGraph.successors(id))[0] in marked_nodes:
                            key_num += 1
                    elif len(list(initGraph.successors(id))) == 0:
                        # process_dict[key_num] = [initGraph.node[id]["block"].name]
                        process_dict[key_num] = [id]
                        key_num += 1
                    elif len(list(initGraph.successors(id))) > 1:
                        # process_dict[key_num] = [initGraph.node[id]["block"].name]
                        process_dict[key_num] = [id]
                        key_num += 1
        # print(process_dict)
        self.pipelineGraphCreate(process_dict)


    
    
