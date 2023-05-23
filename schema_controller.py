# %%
#from transformers import pipeline
from optparse import OptionParser
#from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import json
import sys

# %%
#only thing left to do is receive this json file as an input from the server and make sure
#running the LLM works :), will eventually want to add some other options for LLMs to run
#and also listen for that input.
json_path="/Users/shawnschulz/Downloads/loop_test2.json"

with open(json_path) as json_file:
    schema_dictionary = json.load(json_file)

# %%
### Should probably update this to use a python class, so that when we add new node types
### we can reuse some methods without having to minor edits to make them compatible with
### new node types. This is okay for now tho, since that will require thinking some new logic for
### how the schema deals with sending outputs of nodes to nodes of different types

# %%
def schemaListToDictionary(schemaList):
    '''
        Takes nodes or edges list and makes a dictionary you can index list elements using the ID, probably
        only worth running this function if you have a really big graph you need to access nodes or edges of
        many times, but this option is available for that
    '''
    newDict={}
    for dictionary in schemaList:
        newDict[dictionary['id']] = dictionary.copy()
    return newDict

def hashedMappedSchemaDictionary(schema_dictionary):
    '''
        Take a whole schema dictionary and return a version that now has ID key'd nested dictionaries
        rather than lists
    '''
    newDict={'nodes':{}, 'edges':{}}
    nodesDict = schemaListToDictionary(schema_dictionary['nodes'])
    edgesDict = schemaListToDictionary(schema_dictionary['edges'])
    newDict['nodes'] = nodesDict
    newDict['edges'] = edgesDict
    return newDict

# %%
def findRoots(schema_dictionary):
    '''
        Finds the roots of a schema
        1. Get all the ids of all nodes, put in a stack
        2. Check what targets are currently in the schema
        3. Remove them as you find them

        Give schema dictionary (direct from json file), a dictionary
        Returns the stack of roots of the tree, False if schema nodes have no sources
    '''
    stack = []
    for edge in schema_dictionary['edges']:
        if edge['source'] not in stack:
            stack.append(edge['source'])
    for edge in schema_dictionary['edges']:
        if edge['target'] in stack:
            print("removing from stack")
            stack.remove(edge['target'])
    return stack

def checkBranch(node_id, schema_dictionary):
    '''
        Check if a node ever results in a terminal branch
    '''
    for node in schema_dictionary['nodes']:
        if node['id'] == node_id:
            for edge in schema_dictionary['edges']:
                if edge['source'] == node_id:
                    return False
                else:
                    return True
                
def checkLoop(node_id, schema_dictionary, truth_list = [], seen=[]):
    '''
        Recursively checks if following a node's targets only results in a terminal branch,
        returns a tuple of (bool, list), first part is True 
    '''
    target_list=[]
    if node_id in seen:
        return True
    else:
        seen.append(node_id)
        for edge in schema_dictionary['edges']:
            if edge['source']==node_id:
                target_list.append(edge['target'])
            else:
                truth_list.append(False)
        for target in target_list:
            truth_list.append(checkLoop(target, schema_dictionary, truth_list, seen=seen))
            print(truth_list)
            return bool(sum(truth_list))
    return(bool(sum(truth_list)))

        


# %%
def updateNodePrompts(node_prompt_dictionary, schema_dictionary):
    '''
        Takes a 
    '''
    new_dictionary = schema_dictionary.copy()
    for node in new_dictionary['nodes']:
        if node['id'] in node_prompt_dictionary.keys():
            old_prompt = node['data']['prompt'] 
            new_prompt = node_prompt_dictionary[node['id']] + ' \n' + old_prompt
            node['data']['prompt'] = new_prompt
    return(new_dictionary)
    
            

# %%
def removeNodeIDs(id_list, schema_dictionary):
    '''
        Takes a list of id's to be removed and returns a new schema dictionary with the node
        id's removed

        Note, when making graph smaller, it will usually make more sense to remove unique
        edge id's than nodes. However if there is some reason to this node removal function is here

        This is also really slow, consider changing if u actually make graphs really big
    '''
    new_dictionary = schema_dictionary.copy()
    for id in id_list:
        for node in new_dictionary['nodes']:
            if node['id'] == id:
                new_dictionary['nodes'].remove(node)
    return new_dictionary

# %%
def removeEdgeIDs(id_list, schema_dictionary):
    '''
        takes a list of edge id's and returns a new schema dictionary with the edge id's removed
        Note: important that you remove by edgeid, not source or target since the edge id is unique
    '''
    new_dictionary = schema_dictionary.copy()
    for id in id_list:
        for edge in new_dictionary['edges']:
            if edge['id'] == id:
                new_dictionary['edges'].remove(edge)
    return new_dictionary

# %%
#to start with, I think we should always start from the first node created. May make sense in the future to allow user to specify
#what node they want to start with, but i am too lazy to think of what the UX of that would be 

# %%
def runTextLLM(text):
    '''
        much simpler function that only runs LLM using text, not based on node
    '''
    #for testing just return a string
    print("Running LLM based on text")
    return "this is a test string"

def runNodeLLM(node_id, schema_dictionary):
    '''
        put a funciton that runs the LLM here
    '''
    #for testing just return a string to check that schema's working
    print("Running LLM")
    return "this is a test string"

    for node in schema_dictionary['nodes']:
        if node['id'] == node_id:
            prompt = ''
            for key in node['data'].keys():
                prompt += node['data'][key]
                prompt += " \n"
            # run LLM on prompt, note that this output will need to be sent over web somehow
    return prompt

# %%
def outputToChatbot(output):
    '''
        Takes an output and sends it to the chatbot to be outputted.
        Should also store the outputs in a JSON file for context
    '''
    print("Running outputToChatbot")
    return("Ready to send to output!")

# %%
def listenForInput():
    '''
        Listens for an input from website if user pushes pause or stop
    '''
    print("Running listenForInput")
    return("Placeholder for listening to server!")

def retrieveNodePrompt(node_id, schema_dictionary):
    for node in schema_dictionary['nodes']:
        if node['id'] == node_id:
            return(node['data']['prompt'])

# %%
def runSchema(schema_dictionary, next_node_in_loop = "start", received_input=""):
    '''
        Take a schema and run the flow. Mutates schema dictionary and removes edges not part of a loop, edges within or downstream of loops are
        preserved.

        There are 2 things to track, what the current graph looks like and the stack of 
        nodes to run and their received prompts. Nodes on the stack have to check if they are a 
        root, or else they are not run yet. Root nodes on the stack are run in order, then
        targets are added to the stack with their associated prompt. If the target is already
        on the stack, simply give it the additional prompt.

        If there are nodes, and all of the nodes have a source, this means that there is a loop 
        somewhere in the graph. We still want to run the flow, because recursive nodes are a 
        selling point. In this case, if ALL the nodes have a source, pick the most recently 
        created node and run it, sending its prompts and adding the new targets to the stack. We
        do not update the graph now, instead simply running the node, then its targets in order.
        This will continue running iterations, until a stop button is pressed.

        The user will probably want to

        We should create a stack, a list of dictionaries that look like this:
        [{node_id: ____, sources_dict:{source_id:received_prompt = "" }}]
        This forms a stack. Sources dict may or may not have multiple source_ids in it. Queue up
        the next nodes to run based on what the targets of the node you just ran are. If
        a node has multiple sources when it's run, combine those sources into one prompt
        via concatenation. Received prompts are added first, with the LLMs actual text
        entered into it added last. We may have to do prompt engineering to make sure
        the LLM answers the prompt inputted into the box and not questions received as context,
        but this is not preferred.
        For bonus points, add an option to use dfs or bfs
    '''
    ### Should listen here to see if user hit the pause/stop button, and if they did pause or stop the execution of the code
    listenForInput()

    roots = findRoots(schema_dictionary)
    nodes_to_send_outputs={}
    next_schema_dictionary=schema_dictionary.copy()

    #Base case: Check if schema dictionary has no roots
    if len(roots) == 0:
        print("We are doing the loop case.")
        print("Here's the node we're doing:")
        print(next_node_in_loop)
        if not schema_dictionary['edges']:
            return(schema_dictionary)
        # Other special case: we are looping 
        #this doesn't work, should make a function that follows the targets and returns False if ends up at a terminal branch and True if it 
        #comes back to itself
        else:
            if next_node_in_loop == "start":
                for node in schema_dictionary['nodes']:
                    if checkLoop(node['id'], schema_dictionary):
                        current_node = node['id']
                        break
                    else:
                        print("Node just checked is terminal branch, skipping to find start node!")
            else:
                current_node = next_node_in_loop
            
            ### In the future, you may want to change the way this script combines received inputs
            # with the prompt a node has typed into it
            node_prompt = received_input + retrieveNodePrompt(current_node, schema_dictionary)
            print("the node prompt is: " + node_prompt)
            output = runTextLLM(node_prompt)
            next_received_input = output + " "
            outputToChatbot(output)
            for edge in next_schema_dictionary['edges']:
                if edge['source'] == current_node:
                    edge_id = edge['id']
                    nodes_to_send_outputs[edge['target']] = output
            for node_id in nodes_to_send_outputs:
                runSchema(schema_dictionary, next_node_in_loop=node_id, received_input=next_received_input)

    else:                    
        #Recursive case: Schema dictionary has roots. Get the outputs from the source node, make 
        #an updated schema dictionary where target nodes have the new outputs, and remove
        #the edges that have already been checked
        print("We are doing the tree case")
        edge_ids_to_remove=[]
        
        next_schema_dictionary=schema_dictionary.copy()
        for root in roots:
            for edge in next_schema_dictionary['edges']:
                if edge['source'] == root:
                    edge_id = edge['id']
                    edge_ids_to_remove.append(edge_id)
                    nodes_to_send_outputs[edge['target']] = ""
                    print("Printing the next nodes")
                    print(nodes_to_send_outputs)
                    print("Printing the edges to be removed")
                    print(edge_ids_to_remove)
            output = runNodeLLM(root, next_schema_dictionary)
            ### SEND OUTPUT TO CHATBOT TO OUTPUT HERE ####
            outputToChatbot(output)

            for node_id in nodes_to_send_outputs.keys():
                nodes_to_send_outputs[node_id] = output
            
            ### In the future you may want to change the way this script handles combining 
            ### prompts
            updated_prompts_dict = updateNodePrompts(nodes_to_send_outputs, schema_dictionary)
            next_schema_dictionary=removeEdgeIDs(edge_ids_to_remove, updated_prompts_dict)
        return(runSchema(next_schema_dictionary))

# %%
runSchema(schema_dictionary)

# %%



