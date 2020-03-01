#Creates a weighted, directed graph of all of the Clinton emails of the type
# email_sender ------weight-------> email_recipient
# where "email_sender" and "email_recipient" are nodes and
# weight is the weight of the edge, defined
# as the number of emails sent by email_sender to email_recipient
# for example, .....

#first the imports

import pandas as pd
import networkx as nx
import numpy as np
from collections import Counter, defaultdict
import matplotlib.pylab as pylab
import matplotlib.pyplot as plt

#setup the plotting
pylab.rcParams['figure.figsize'] = 16, 16


# read the main data source
emails = pd.read_csv("../input/Emails.csv")

#cleanup the names in the From and To fields
with open("../input/Aliases.csv") as f:
    file = f.read().split("\r\n")[1:] #skip the header line
    aliases = {}
    for line in file:
        line = line.split(",")
        aliases[line[1]] = line[2]

with open("../input/Persons.csv") as f:
    file = f.read().split("\r\n")[1:] #skip header line
    persons = {}
    for line in file:
        line = line.split(",")
        persons[line[0]] = line[1]
        
def resolve_person(name):
    name = str(name).lower().replace(",","").split("@")[0]
    #print(name)
    #correct for some of the common people who are resolved to several different
    # names by the given Aliases.csv file:  Cheryl Mills, Huma Abedin, Jake Sullivan
    # and Lauren Jiloty
    # Also convert "h" and variations to Hillary Clinton
    if ("mills" in name) or ("cheryl" in name) or ("nill" in name) or ("miliscd" in name) or ("cdm" in name) or ("aliil" in name) or ("miliscd" in name):
        return "Cheryl Mills"
    elif ("a bed" in name) or ("abed" in name) or ("hume abed" in name) or ("huma" in name) or ("eabed" in name):
        return "Huma Abedin"
    #elif (name == "abedin huma") or (name=="huma abedin") or (name=="abedinh"): 
    #    return "Huma Abedin"
    elif ("sullivan" in name)  or ("sulliv" in name) or ("sulliy" in name) or ("su ii" in name) or ("suili" in name):
        return "Jake Sullivan"
    elif ("iloty" in name) or ("illoty" in name) or ("jilot" in name):
        return "Lauren Jiloty"
    elif "reines" in name: return "Phillip Reines"
    elif (name == "h") or (name == "h2") or ("secretary" in name) or ("hillary" in name) or ("hrod" in name):
        return "Hillary Clinton"
    #fall back to the aliases file
    elif str(name) == "nan": return "Redacted"
    elif name in aliases.keys():
        return persons[aliases[name]]
    else: return name
    
emails.MetadataFrom = emails.MetadataFrom.apply(resolve_person)
emails.MetadataTo = emails.MetadataTo.apply(resolve_person)

#Extract the to: from: and Raw body text from each record

From_To_RawText = []
temp = zip(emails.MetadataFrom,emails.MetadataTo,emails.RawText)
for row in temp:
    From_To_RawText.append(((row[0],row[1]),row[2]))

#Create a dictionary of all edges, i.e. (sender, recipient) relationships 
# and store the individual email text in a list for each key
From_To_allText = defaultdict(list)
for people, text in From_To_RawText:
    From_To_allText[people].append(text)
len(From_To_allText.keys()), len(From_To_RawText)

#Set the weights of each directed edge equal to the number of emails 
# (number of raw text documents) associated with that edge
edges_weights = [[key[0], key[1], len(val)] for key, val in From_To_allText.items()]
edge_text = [val for key, val in From_To_allText.items()]

#initialize the graph
graph = nx.DiGraph()

#transform the dict with keys (from,to) and vals weight back to a 
# tuple(from, to, weight)
graph.add_weighted_edges_from(edges_weights)
nx.set_edge_attributes(graph, 'text', edge_text)

#Calculate the pagerank of each person (node) and store it with the node.
pagerank = nx.pagerank(graph)
pagerank_list = {node: rank for node, rank in pagerank.items()}
nx.set_node_attributes(graph, 'pagerank', pagerank_list)

#draw the graph
positions=nx.spring_layout(graph)

#size of the graphed node proportional to its pagerank
nodesize = [x['pagerank']*30000 for v,x in graph.nodes(data=True)]
edgesize = [np.sqrt(e[2]['weight']) for e in graph.edges(data=True)]

nx.draw_networkx_nodes(graph, positions, node_size=nodesize, alpha=0.4)
nx.draw_networkx_edges(graph, positions, edge_size=edgesize, alpha=0.2)
nx.draw_networkx_labels(graph, positions, font_size=10)

plt.savefig("email_graph.png")
plt.title("Graph of all send/receive relationships in the Clinton email database", fontsize=20)
plt.clf()

#That graph is pretty big. Let's make a smaller one with just the most
# important people.  
#This will plot only the nodes with pagerank greater than
#  pagerank_cutoff

pagerank_cutoff = 0.0045

small_graph = graph.copy()
for n, p_rank in small_graph.nodes(data=True):
    if p_rank['pagerank'] < pagerank_cutoff: small_graph.remove_node(n)
    
spositions=nx.spring_layout(small_graph, weight=None)
snodesize = [x['pagerank']*30000 for v,x in small_graph.nodes(data=True)]
sedgesize = [np.log(e[2]['weight']) for e in small_graph.edges(data=True)]
scolors = np.random.rand(len(small_graph.nodes()))

nx.draw_networkx_nodes(small_graph, spositions, node_size=snodesize, node_color=scolors, alpha=0.3)
nx.draw_networkx_edges(small_graph, spositions, alpha=0.3, arrows=False) #, width=sedgesize)
nx.draw_networkx_labels(small_graph, spositions, font_size=14)
plt.title("Graph of only those people with a pagerank of greater than %s" % pagerank_cutoff, fontsize=20)
plt.savefig("small_graph.png")