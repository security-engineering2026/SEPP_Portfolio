# =====================================
# SEC-001 AssetWatch
# Version : v1.0
#
# Features:
# [x] Read Assets
# [x] Normalize Data
# [x] Validate Asset Format
# [x] Remove Duplicate
# [x] Multi-Type Query
# [x] Asset Summary
# [x] Report Output
# =====================================

assets = []

with open("data/assets.txt", "r") as file:
    for line in file:
        asset = line.lower().strip()
        

        if asset and  asset.count("-") == 2:

            assets.append(asset)
            
clean = []

for s in assets:
    if s not in clean:
        clean.append(s)
        
requested_types = ["web", "db"]

filtered_assets = []

for asset in clean:

    for search in requested_types:

        if asset.startswith(search):
            filtered_assets.append(asset)
            
summary = {}


for asset in filtered_assets:

    asset_type = asset.split("-")[0]
    
    if asset_type not in summary:
        
        summary[asset_type]=1
    else:
        summary[asset_type]+=1

print("====================")
print("SEC-001 AssetWatch")
print("Version : v1.0")
print("====================")
print()
# Future Improvement
print("Requested Types :", ", ".join(requested_types))
print()

print("Total assets:", len(filtered_assets))
print()

for key in summary:
    print(key, ":", summary[key])

print()    
print("====================")