graph = []

with open("data/graph.txt", "r") as file:
    for line in file:

        clean_line = line.lower().strip()

        if clean_line:
            graph.append(clean_line)

# -------------------------------------
# Build Relations
# -------------------------------------

relations = []

for g in graph:

    parts = g.split(" -> ")

    source = parts[0]
    target = parts[1]

    relation = {
        "source": source,
        "target": target
    }

    relations.append(relation)

# -------------------------------------
# Extract Nodes
# -------------------------------------

nodes = []

for relation in relations:

    source = relation["source"]
    target = relation["target"]

    if source not in nodes:
        nodes.append(source)

    if target not in nodes:
        nodes.append(target)

# -------------------------------------
# Node Frequency
# -------------------------------------

node_frequency = {}

for relation in relations:

    source = relation["source"]
    target = relation["target"]

    if source in node_frequency:
        node_frequency[source] += 1
    else:
        node_frequency[source] = 1

    if target in node_frequency:
        node_frequency[target] += 1
    else:
        node_frequency[target] = 1
        
        
top_node = None
top_count = 0

for node, count in node_frequency.items():

    if count > top_count:
        top_count = count
        top_node = node

# -------------------------------------
# Report
# -------------------------------------

print("====================")
print("SEC-004 DataFusion")
print("====================")
print()

print("Imported Relations :", len(graph))
print("Total Nodes :", len(nodes))

print()
print("Nodes")
print("-----")

for node in nodes:
    print("-", node)

print()
print("Node Frequency")
print("--------------")

for node, count in node_frequency.items():
    print(node, ":", count)
    
print()
print("Most Frequent Node")
print("------------------")
print(top_node, ":", top_count)
print()
print("Fusion Summary")
print("--------------")
print("Relations :", len(relations))
print("Nodes     :", len(nodes))
print("Top Node  :", top_node)
print()
# -------------------------------------
# Export Frequency
# -------------------------------------

with open("output/frequency.txt", "w") as file:

    for node, count in node_frequency.items():

        file.write(f"{node}:{count}\n")

print("====================")
print("End of Report")
print("====================")
