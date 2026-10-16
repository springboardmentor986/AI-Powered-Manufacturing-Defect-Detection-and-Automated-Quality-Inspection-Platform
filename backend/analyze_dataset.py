import pandas as pd

# Load our dataset summary
df = pd.read_csv("docs/dataset_summary.csv")

print("Dataset Analysis using Pandas")
print("-----------------------------")

print("\nDataset:")
print(df)

print("\nShape:")
print(df.shape)

print("\nColumn names:")
print(df.columns.tolist())
print("\nTraining Image Analysis")
print("-----------------------")

print("Most training images:")
print(df.loc[df["Train Images"].idxmax(), ["Category", "Train Images"]])

print("\nLeast training images:")
print(df.loc[df["Train Images"].idxmin(), ["Category", "Train Images"]])

print("\nAverage training images:")
print(df["Train Images"].mean())

print("\nMost test images:")
print(df.loc[df["Test Images"].idxmax(), ["Category", "Test Images"]])

print("\nLeast test images:")
print(df.loc[df["Test Images"].idxmin(), ["Category", "Test Images"]])
print("\nDefect Distribution Analysis")
print("----------------------------")

df["Defective Percentage"] = (
    df["Defective Test Images"] / df["Test Images"]
) * 100

print(
    df[["Category", "Test Images", "Defective Test Images",
        "Defective Percentage"]]
)

print("\nHighest defective percentage:")
print(
    df.loc[
        df["Defective Percentage"].idxmax(),
        ["Category", "Defective Percentage"]
    ]
)

print("\nLowest defective percentage:")
print(
    df.loc[
        df["Defective Percentage"].idxmin(),
        ["Category", "Defective Percentage"]
    ]
)