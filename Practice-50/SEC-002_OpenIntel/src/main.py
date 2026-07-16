# =====================================
# SEC-002 OpenIntel
# Version : v1.0
#
# Features:
# [x] Read Input
# [x] Normalize Data
# [x] Remove Duplicate
# [x] Entity Classification
# [x] Statistics Report
# [x] Search Engine
# [x] Interactive Search
# =====================================

entities = []

with open("data/input.txt", "r") as file:
    for line in file:
        clean_line = line.lower().strip()

        if clean_line:
            entities.append(clean_line)
            
clean_entities = []
for e in entities:
    if e not in clean_entities:
        clean_entities.append(e)

emails = []

domains = []

names = []

for u in clean_entities:
    if "@" in u and "." in u:
        emails.append(u)
    elif "@" not in u and "." in u:
        domains.append(u)
    else:
        names.append(u)

print("========================")
print("SEC-002 OpenIntel")
print("Version : v0.1")
print("========================")
print()
print("Data Statistics")
print("---------------")
print()
print("Total Input        :", len(entities))
print("Unique Entities    :", len(clean_entities))
print("Duplicate Removed  :", len(entities) - len(clean_entities))
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
    print("-" , domain) 
print() 

print("Name List")
print("---------")

for name in names:
    print("-" , name)    
    
# ============================
# Search Engine
# ============================

query = input("Search > ")

search_results = []

for entity in clean_entities:
    if query in entity:
        search_results.append(entity)

print()
print("Search Results")
print("--------------")
if search_results:
 for item in search_results:
        print("-", item)
else:
        print("No results found.")