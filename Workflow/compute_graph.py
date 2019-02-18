
import copy


class node():
    def __init__(self, function=None, args=[], kwargs={}, name=None, parents=[]):
        self.function = function
        self.args = list(args)
        self.kwargs = kwargs
        self.name = name
        self.parents=parents
        self.out = None
        self.args_parents = {}
        self.kwargs_parents = {}
        
        self.long_name = ""

        #Trace parents and store
        for i,arg in enumerate(self.args):
            if type(arg)==type(self):
                self.args_parents[i]  = arg
                self.long_name += arg.long_name + "." 
                
        for kw in self.kwargs:
            if type(self.kwargs[kw])==type(self):
                self.kwargs_parents[kw]=self.kwargs[kw]
                self.long_name += self.kwargs[kw].long_name + "." 

    def run(self):
        
        if self.out is not None:
            #If function at this node has already been computed, 
            #just return the value
            return(self.out)
        else:
            #If function has not been computed, first compute all
            #arguments that are also nodes, then compute
            #the function itself and store the result.
            
            for i in self.args_parents:
                #self.args[i]=self.args_parents[i].run()
                self.args[i]=self.args_parents[i].out
            for kw in self.kwargs_parents:
                #self.kwargs[kw]=self.kwargs_parents[kw].run()
                self.kwargs[kw]=self.kwargs_parents[kw].out()
            self.out =  self.function(*self.args, **self.kwargs)
            return (self.out)  
            
    def get_args(self):
        for i in self.args_parents:
            #self.args[i]=copy.copy(self.args_parents[i].out)
            self.args[i]=self.args_parents[i].out
        return  self.args   
        
    def get_kwargs(self): 
        for kw in self.kwargs_parents:
            #self.kwargs[kw]=copy.copy(self.kwargs_parents[kw].out)
            self.kwargs[kw]=self.kwargs_parents[kw].out      
        return  self.kwargs       
            