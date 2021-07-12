
import networkx as nx
import time
from concurrent import futures
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
import Workflow.scheduler as scheduler
from Workflow.compute_graph import pipelineNode
import os
        
class workflow():

    def __init__(self, nodes={}):

        self.graph=nx.DiGraph()
        self.labels={}
        self.out_nodes = []
        self.pipeline_dict = {}
        self.pipelineGraph = nx.DiGraph()
        #If have compute nodes, add to graph
        #along with all parents
        for out_tag in nodes:
            node = nodes[out_tag]
            node.out_tag = out_tag
            self.add(node)
        self.pipeline(self.graph)
    
    def add(self, nodes):
        
        if type(nodes) is not list:
            nodes=[nodes]
        self.out_nodes = self.out_nodes + nodes
        for node in nodes: 
            if(not hasattr(node,"out_tag")):
                node.out_tag = node.name           
            self.recursive_add_node(node)

    def remove(self, nodes):
        
        #print(self.graph.nodes())
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
        #Get node name and ID
        # print(node)
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
        #self.blocks[name] = block
        self.graph.add_node(name, block=block, label=block.name, shape="box", style="filled", fillcolor="white",color="black", fontname="helvetica")
        self.labels[name] = block.name

    
    def add_edge(self, node_from, node_to):
        self.graph.add_edge(node_from, node_to)
        
    def set_status(self,node,status):
        if(status=="scheduled"):
            node["fillcolor"]="lemonchiffon"
        elif(status=="notscheduled"):
            node["fillcolor"]="white"
        elif(status=="running"):
            node["fillcolor"]="palegreen3"
        elif(status=="done"):
            node["fillcolor"]="lightblue"
            
        
    
    def draw(self, refresh=False):
        import networkx as nx
        from networkx.drawing.nx_agraph import write_dot, graphviz_layout
        import matplotlib.pyplot as plt
        from IPython import display
        
        pdot = nx.drawing.nx_pydot.to_pydot(self.graph)
        pdot.set_rankdir("LR")
        #pdot.set_splines("ortho")
        
        if not os.path.exists("Temp"):
            os.mkdir("Temp")
        pdot.write_png("Temp/temp.png")
        #pdot.write_pdf("Temp/temp.pdf")
        img=mpimg.imread('Temp/temp.png')
        
        plt.figure(1,figsize=(img.shape[1]/100,img.shape[0]/100))
        plt.imshow(img,interpolation='bicubic')
        plt.axis('off')
           
        display.clear_output(wait=True)
        if(refresh):
            display.display(plt.gcf())  

    def drawPipelined(self, refresh=False):
        import networkx as nx
        from networkx.drawing.nx_agraph import write_dot, graphviz_layout
        import matplotlib.pyplot as plt
        from IPython import display
        
        pdot = nx.drawing.nx_pydot.to_pydot(self.pipelineGraph)
        pdot.set_rankdir("LR")
        #pdot.set_splines("ortho")
        
        pdot.write_png("Temp/temp.png")
        #pdot.write_pdf("Temp/temp.pdf")
        img=mpimg.imread('Temp/temp.png')
        
        plt.figure(1,figsize=(img.shape[1]/100,img.shape[0]/100))
        plt.imshow(img,interpolation='bicubic')
        plt.axis('off')
           
        display.clear_output(wait=True)
        if(refresh):
            display.display(plt.gcf())      
    
    def run(self, backend="sequential", num_workers=1, monitor=False,from_scratch=False):
        return scheduler.run(self, backend=backend, num_workers=num_workers, monitor=monitor,from_scratch=from_scratch)

    def add_pipeline_node(self, id, plNode):
        self.pipelineGraph.add_node(id, block=plNode, label=plNode.name, shape="box", style="filled", fillcolor="white",color="black", fontname="helvetica")

    ### Method is called by the class constructor after creating a pipelined sets of nodes
    def pipelineGraphCreate(self, process_dict):
        pipelineNodeList = []
        # headNodes = {}
        # tailNodes = {}
        for key in process_dict:
            plNode = pipelineNode(self.graph, process_dict[key], key)
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
        

    ### Called in the class constructor. Produces a pipelined graph object which is used by the scheduler to run the job.
    def pipeline(self, initGraph):
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


    
    
