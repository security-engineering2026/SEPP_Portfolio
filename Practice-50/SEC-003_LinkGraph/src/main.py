# =====================================
# SEC-003 LinkGraph
# Version : v1.0
#
# Features:
# [x] Read Entities
# [x] Normalize Data
# [x] Remove Empty Lines
# [x] Remove Duplicate
# [x] Entity Classification
# [x] Build Relationships
# [x] Extract Nodes
# [x] Calculate Node Degree
# [x] Find Most Connected Node
# [x] Export Graph
# [x] Import Graph
# [x] Graph Search
# =====================================

entities = []

with open("data/entities.txt", "r") as file:
    for line in file:
        clean_line = line.lower().strip()

        if clean_line:
            entities.append(clean_line)

# -------------------------------------
# Remove Duplicate
# -------------------------------------

unique_entities = []

for entity in entities:
    if entity not in unique_entities:
        unique_entities.append(entity)

# -------------------------------------
# Classification
# -------------------------------------

emails = []
domains = []
names = []

for entity in unique_entities:

    if "@" in entity and "." in entity:
        emails.append(entity)

    elif "." in entity:
        domains.append(entity)

    else:
        names.append(entity)

# -------------------------------------
# Build Relations
# -------------------------------------

relations = []

for email in emails:

    domain = email.split("@")[1]

    if domain in domains:

        relation = {
            "source": email,
            "target": domain
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
# Node Degree
# -------------------------------------

node_degree = {}

for relation in relations:

    source = relation["source"]
    target = relation["target"]

    if source in node_degree:
        node_degree[source] += 1
    else:
        node_degree[source] = 1

    if target in node_degree:
        node_degree[target] += 1
    else:
        node_degree[target] = 1

# -------------------------------------
# Most Connected Node
# -------------------------------------

top_node = None
top_degree = 0

for node in node_degree:

    degree = node_degree[node]

    if degree > top_degree:
        top_degree = degree
        top_node = node

# -------------------------------------
# Export Graph
# -------------------------------------

with open("output/graph.txt", "w") as file:

    for relation in relations:

        line = relation["source"] + " -> " + relation["target"] + "\n"

        file.write(line)

# -------------------------------------
# Import Graph
# -------------------------------------

graph_lines = []

with open("output/graph.txt", "r") as file:

    for line in file:

        clean_line = line.lower().strip()

        if clean_line:
            graph_lines.append(clean_line)

# -------------------------------------
# Graph Search
# -------------------------------------

query = input("Graph Search > ")

search_results = []

for graph in graph_lines:

    if query in graph:
        search_results.append(graph)

# -------------------------------------
# Report
# -------------------------------------

print("========================")
print("SEC-003 LinkGraph")
print("Version : v1.0")
print("========================")
print()

print("Data Statistics")
print("----------------")
print()

print("Total Input        :", len(entities))
print("Unique Entities    :", len(unique_entities))
print("Duplicate Removed  :", len(entities) - len(unique_entities))
print()

print("Entity Summary")
print("--------------")
print()

print("Emails             :", len(emails))
print("Domains            :", len(domains))
print("Names              :", len(names))
print()

print("Email List")
print("----------")

for email in emails:
    print("-", email)

print()

print("Domain List")
print("-----------")

for domain in domains:
    print("-", domain)

print()

print("Name List")
print("---------")

for name in names:
    print("-", name)

print()

print("Relations")
print("---------")

for relation in relations:
    print("-", relation["source"], "->", relation["target"])

print()

print("Nodes")
print("-----")

for node in nodes:
    print("-", node)

print()

print("Node Degree")
print("-----------")

for node in node_degree:
    print("-", node, ":", node_degree[node])

print()

print("Most Connected Node")
print("-------------------")

print(top_node, ":", top_degree)

print()

print("Imported Graph")
print("--------------")

for line in graph_lines:
    print("-", line)

print()

print("Graph Search Results")
print("--------------------")

if search_results:
    for item in search_results:
        print("-", item)
else:
    print("No results found.")

print()
print("========================")
print("End of Report")
print("========================")