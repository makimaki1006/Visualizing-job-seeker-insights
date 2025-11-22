# -*- coding: utf-8 -*-
import pandas as pd

df = pd.read_csv('C:/Users/fuji1/OneDrive/Pythonスクリプト保管/out/results_20251119_073325.csv',
                 encoding='utf-8-sig', nrows=5)

print("=== Sample Data ===")
print(df[['prefecture', 'age_gender', 'location', 'desired_area', 'career', 'qualifications']].to_string())

print("\n=== Qualifications Detail ===")
for i, q in enumerate(df['qualifications'].head(5)):
    print(f"{i+1}. {q}")

print("\n=== Career Detail ===")
for i, c in enumerate(df['career'].head(5)):
    print(f"{i+1}. {c}")

print("\n=== Desired Area Detail ===")
for i, d in enumerate(df['desired_area'].head(5)):
    print(f"{i+1}. {d}")

print("\n=== Location Detail ===")
for i, l in enumerate(df['location'].head(5)):
    print(f"{i+1}. {l}")
