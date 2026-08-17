import pandas as pd
# Exercise 1 - Pandas Series
salaries = pd.Series([72000, 65000, 85000, 95000, 58000])
print(salaries)

# Exercise 2 - Read CSV
df = pd.read_csv("sales_data.csv")
print(df)
# Exercise 3 - Select a Series from DataFrame
salary_series = df["Salary"]
print(salary_series)

print(salary_series)
#Exercise 4 - Create a DataFrame

data = {
    "Product": ["Laptop", "Phone", "Tablet"],
    "Price": [1000, 700, 400]
}

product_df = pd.DataFrame(data)
# Exercise 5 - Read CSV first 5 rows

print(df.head(5))

# Exercise 6 - Read JSON
df = pd.read_json("employees.json")
print(df)
#Exercise 7 - Calculate average salary
average_salary = df["Salary"].mean()
print("Average salary:", average_salary)

# Exercise 8 - Highest and Lowest Salary
df = pd.read_csv("sales_data.csv")

highest_salary = df["Salary"].max()
lowest_salary = df["Salary"].min()

print("Highest Salary:", highest_salary)
print("Lowest Salary:", lowest_salary)
# Exercise 9 - Count Employees

employee_count = df["Name"].count()

print("Number of Employees:", employee_count)
# Exercise 11 - Check for Missing Data

print(df.isnull().sum())
# Exercise 12 - Create Missing Data

df.loc[2, "Salary"] = None

print(df)
# Exercise 13 - Filling Missing Value

df["Salary"] = df["Salary"].fillna(df["Salary"].mean())

print(df)
# Exercise 14 - Cleaning Wrong Format

df.loc[1, "Age"] = "thirty-five"

print(df["Age"])

df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
print(df["Age"])
# Exercise 15 - Cleaning Wrong Data

df.loc[1, "Age"] = 35

print(df["Age"])
# Exercise 16 - Removing Duplicates

df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

print("Rows before removing duplicate:", len(df))

df = df.drop_duplicates()

print("Rows after removing duplicate:", len(df))
# Exercise 17 - Correlation

correlation = df["Experience"].corr(df["Salary"])

print("Experience and Salary correlation:", correlation)
# Exercise 18 - Plotting

df.plot(x="Experience", y="Salary", kind="scatter")

import matplotlib.pyplot as plt

plt.show()








