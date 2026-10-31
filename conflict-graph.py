import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# 1. Read the dataset
df = pd.read_csv("synthetic_exam_scheduling_enrollments.csv")

# 2. Create an undirected graph
G = nx.Graph()

# 3. Add one vertex for each distinct subject offering
subjects = df[
    ["subject_code", "subject_name", "subject_type"]
].drop_duplicates()

for _, subject in subjects.iterrows():
    G.add_node(
        subject["subject_code"],
        name=subject["subject_name"],
        type=subject["subject_type"]
    )

# 4. Find the students enrolled in each subject
enrollments = df.groupby("subject_code")["student_id"].apply(set)

# 5. Connect subjects that share at least one student
subject_codes = subjects["subject_code"].tolist()

for i in range(len(subject_codes)):
    for j in range(i + 1, len(subject_codes)):
        subject_a = subject_codes[i]
        subject_b = subject_codes[j]

        common_students = (
            enrollments[subject_a] & enrollments[subject_b]
        )

        if common_students:
            G.add_edge(subject_a, subject_b)

# 6. Draw the graph
pos = nx.spring_layout(G, seed=42)

core_nodes = [
    node for node in G.nodes()
    if G.nodes[node]["type"] == "CORE"
]

elective_nodes = [
    node for node in G.nodes()
    if G.nodes[node]["type"] == "OPEN_ELECTIVE"
]

plt.figure(figsize=(16, 12))

nx.draw_networkx_edges(
    G, pos, alpha=0.3, width=0.8
)

nx.draw_networkx_nodes(
    G, pos, nodelist=core_nodes,
    node_color="#BFD7EA", node_size=700,
    edgecolors="#3D5A80", linewidths=1.2,
    label="Core subjects"
)

nx.draw_networkx_nodes(
    G, pos, nodelist=elective_nodes,
    node_color="#FFD6A5", node_size=900,
    edgecolors="#B5651D", linewidths=1.2,
    label="Open electives"
)

nx.draw_networkx_labels(
    G, pos, font_size=7, font_color="#1B1B1B"
)

plt.title("Exam Conflict Graph")
plt.legend()
plt.axis("off")
plt.tight_layout()

# 7. Save the graph
plt.savefig("conflict_graph.png", dpi=300, bbox_inches="tight")
plt.show()

print("Number of vertices:", G.number_of_nodes())
print("Number of edges:", G.number_of_edges())
print("Graph saved as conflict_graph.png")

