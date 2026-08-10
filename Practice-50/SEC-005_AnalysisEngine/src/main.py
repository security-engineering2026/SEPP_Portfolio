# =====================================
# SEC-005 AnalysisEngine
# Version : v1.0
#
# Features:
# [x] Read Frequency Data
# [x] Parse Node Counts
# [x] Risk Classification
# [x] Numeric Risk Scoring
# [x] Build Risk Report
# [x] Sort by Score
# [x] Filter High Risk
# [x] Generate Top Findings
# [x] Export Report
# =====================================

# -------------------------------------
# Read Frequency Data
# -------------------------------------

node_frequency = {}

with open("data/frequency.txt", "r") as file:

    for line in file:

        clean_line = line.strip()

        if clean_line:

            parts = clean_line.split(":")

            node = parts[0]
            count = int(parts[1])

            node_frequency[node] = count

# -------------------------------------
# Risk Analysis
# -------------------------------------

risk_report = []

for node, count in node_frequency.items():

    if count >= 3:
        risk = "High"
        score = 90

    elif count == 2:
        risk = "Medium"
        score = 50

    else:
        risk = "Low"
        score = 10

    item = {
        "node": node,
        "risk": risk,
        "score": score
    }

    risk_report.append(item)

# -------------------------------------
# Sort by Score
# -------------------------------------

sorted_report = sorted(
    risk_report,
    key=lambda item: item["score"],
    reverse=True
)

# -------------------------------------
# High Risk Filter
# -------------------------------------

high_risk = []

for item in sorted_report:

    if item["risk"] == "High":

        high_risk.append(item)

# -------------------------------------
# Top Findings
# -------------------------------------

TOP_LIMIT = 5
top_findings = sorted_report[:TOP_LIMIT]

# -------------------------------------
# Export Report
# -------------------------------------

with open("output/report.txt", "w") as file:

    file.write("Priority Report\n")
    file.write("---------------\n")

    for item in sorted_report:
        file.write(
            f"{item['node']} : {item['risk']} ({item['score']})\n"
        )

    file.write("\n")

    file.write("High Risk Findings\n")
    file.write("------------------\n")

    if high_risk:

        for item in high_risk:
            file.write(
                f"{item['node']} ({item['score']})\n"
            )

    else:
        file.write("No high risk findings.\n")

    file.write("\n")

    file.write("Top Findings\n")
    file.write("------------\n")

    for item in top_findings:
        file.write(
            f"{item['node']} : {item['score']}\n"
        )

# -------------------------------------
# Report
# -------------------------------------

print("====================")
print("SEC-005 AnalysisEngine")
print("====================")
print()

print("Priority Report")
print("---------------")

for item in sorted_report:
    print(f"{item['node']} : {item['risk']} ({item['score']})")

print()
print("High Risk Findings")
print("------------------")

if high_risk:

    for item in high_risk:
        print(f"{item['node']} ({item['score']})")

else:
    print("No high risk findings.")

print()
print("Top Findings")
print("------------")

for item in top_findings:
    print(f"{item['node']} : {item['score']}")

print()
print("====================")
print("End of Report")
print("====================")