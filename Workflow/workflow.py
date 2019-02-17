
import networkx as nx
import time
from concurrent import futures
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
import Workflow.scheduler as scheduler
        
class workflow():

    def __init__(self, nodes=[]):

        self.graph=nx.DiGraph()
        self.labels={}
        self.out_nodes = []
        
        #If have compute nodes, add to graph
        #along with all parents
        self.add(nodes)
            
    
    def add(self, nodes):

        if type(nodes) is not list:
            nodes=[nodes]

        self.out_nodes = self.out_nodes + nodes
        for node in nodes:
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
                    this_node = self.graph.node[descendant_id]["block"]
                    print("  Removing: ", this_node.name, descendant_id)
                
                    self.graph.remove_node(descendant_id)
                    if(this_node in self.out_nodes):
                        self.out_nodes.remove(this_node)                



    def recursive_add_node(self, node):
        #Get node name and ID
        
        node_id = str(id(node))
        
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
        
        pdot.write_png("Temp/temp.png")
        pdot.write_pdf("Temp/temp.pdf")
        img=mpimg.imread('Temp/temp.png')
        
        plt.figure(1,figsize=(img.shape[1]/100,img.shape[0]/100))
        plt.imshow(img,interpolation='bicubic')
        plt.axis('off')
           
        display.clear_output(wait=True)
        if(refresh):
            display.display(plt.gcf())        
    
    def run(self, backend="sequential", num_workers=1, monitor=False,from_scratch=False):
        return scheduler.run(self, backend=backend, num_workers=num_workers, monitor=monitor,from_scratch=from_scratch)
    
    
