import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# List all participant csvs you want
csv_files = [
    "exports/record_VCURIOSITY_1.csv",
    "exports/record_VCURIOSITY_2.csv",
    "exports/record_VCURIOSITY_3.csv",
    "exports/record_VCURIOSITY_4.csv",
    "exports/record_VCURIOSITY_5.csv",
    "exports/record_VCURIOSITY_6.csv",
    "exports/record_VCURIOSITY_7.csv",
    "exports/record_VCURIOSITY_8.csv",
    "exports/record_VCURIOSITY_9.csv",
    "exports/record_VCURIOSITY_10.csv",
    "exports/record_VCURIOSITY_11.csv",
    "exports/record_VCURIOSITY_12.csv",
    "exports/record_VCURIOSITY_13.csv",
    "exports/record_VCURIOSITY_14.csv",
    "exports/record_VCURIOSITY_15.csv",
    "exports/record_VCURIOSITY_16.csv",
    "exports/record_VCURIOSITY_17.csv",
    "exports/record_VCURIOSITY_18.csv",
    "exports/record_VCURIOSITY_19.csv",
    "exports/record_VCURIOSITY_20.csv",
    "exports/record_VCURIOSITY_21.csv",
    "exports/record_VCURIOSITY_22.csv"
]

MODEL_NAME = "Set_11_elong_glossy_3.glb"

plt.figure(figsize=(9,5)) #Creates a blank plot of size 9 inches wide × 5 inches high

MAX_STEPS = 90

for file in csv_files:
    df = pd.read_csv(file)
    df = df[(df["model"] == MODEL_NAME) & (df["actionId"] != -1)]
    if "t_start_ms" in df.columns:
        df = df.sort_values("t_start_ms") # Sort by timestamp if available
    
    if df.empty:
        continue
    
    x = np.arange(1, len(df)+1)
    y = df["actionId"].astype(int).to_numpy()
    plt.plot(x, y, 
             marker="o", # Use circle markers
             linewidth=1.2, # Line thickness
             alpha=0.03, # Transparency 
             label=file.split("/")[-1],# legend label = filename only (no folder path)
             color="blue")

plt.yticks([0,1,2,3], ["Up (0)", "Down (1)", "Left (2)", "Right (3)"])
plt.xlabel("Step index")
plt.ylabel("Action")
plt.title(f"Action trajectories overlaid\nModel: {MODEL_NAME}")
plt.legend(loc="upper right", fontsize=6)
plt.grid(True, alpha=0.3)# Add grid with some transparency
plt.tight_layout()#makes sure labels don’t overlap the figure edges
plt.show()# Display the plot
