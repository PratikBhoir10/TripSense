import pandas as pd

df = pd.read_csv("data/mumbai_places.csv")

# Basic shape and columns
print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())

# Check for missing values
print("\nMissing values per column:")
print(df.isnull().sum())

# Look at the category distribution
print("\nIndoor/Outdoor breakdown:")
print(df["indoor_outdoor"].value_counts())

print("\nBudget level breakdown:")
print(df["budget_level"].value_counts())

# Peek at one full row to see the description/tags format
print("\nSample place (full detail):")
print(df.iloc[0])

# Combine description + tags into one text field —
# this is what we'll feed into the embedding model in Step 3
df["combined_text"] = df["description"] + " " + df["category_tags"]
print("\nCombined text example:")
print(df["combined_text"].iloc[0])