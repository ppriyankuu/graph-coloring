import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# 1. Read the dataset
df = pd.read_csv("synthetic_exam_scheduling_enrollments.csv")

# 2. Create a graph
G = nx.Graph()

# Use subject codes in a fixed order
subjects = (
    df[["subject_code", "subject_name"]]
    .drop_duplicates()
    .sort_values("subject_code")
)

codes = subjects["subject_code"].tolist()

# Add all vertices
G.add_nodes_from(codes)

# 3. Get the student list for every subject
enrollments = df.groupby("subject_code")["student_id"].apply(set)

# 4. Add edges for shared enrollments
for i in range(len(codes)):
    for j in range(i + 1, len(codes)):
        a = codes[i]
        b = codes[j]

        if enrollments[a] & enrollments[b]:
            G.add_edge(a, b)

# 5. Create the adjacency matrix
A = nx.to_numpy_array(
    G,
    nodelist=codes,
    dtype=int
)

matrix = pd.DataFrame(
    A,
    index=codes,
    columns=codes
)

# 6. Save the complete matrix to CSV
matrix.to_csv("adjacency_matrix.csv")

# 7. Print the matrix
print(matrix)

# 8. Draw the matrix with borders between cells and no colorbar
n = len(codes)

fig, ax = plt.subplots(figsize=(14, 12))

cmap = ListedColormap(["white", "steelblue"])
ax.imshow(A, cmap=cmap, interpolation="nearest")

# Labels at the cell centres
ax.set_xticks(range(n))
ax.set_yticks(range(n))
ax.set_xticklabels(codes, rotation=90, fontsize=6)
ax.set_yticklabels(codes, fontsize=6)

# Border lines between cells
ax.set_xticks([x - 0.5 for x in range(1, n)], minor=True)
ax.set_yticks([y - 0.5 for y in range(1, n)], minor=True)
ax.grid(which="minor", color="black", linestyle="-", linewidth=0.3)
ax.tick_params(which="minor", bottom=False, left=False)

ax.set_title("Adjacency Matrix of the Exam Conflict Graph")
ax.set_xlabel("Subject code")
ax.set_ylabel("Subject code")

plt.tight_layout()

# 9. Save the image
plt.savefig(
    "adjacency_matrix.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Matrix saved as adjacency_matrix.csv")
print("Matrix image saved as adjacency_matrix.png")
