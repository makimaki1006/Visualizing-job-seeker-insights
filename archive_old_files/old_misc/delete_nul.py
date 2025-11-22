# -*- coding: utf-8 -*-
import os
import glob

os.chdir(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project")

nul_files = glob.glob('**/nul', recursive=True)
deleted = 0
errors = []

for f in nul_files:
    try:
        full_path = os.path.abspath(f)
        # Use extended path format
        extended_path = "\\\\?\\" + full_path
        os.remove(extended_path)
        deleted += 1
    except Exception as e:
        errors.append(f"{f}: {e}")

print(f"Deleted {deleted}/{len(nul_files)} nul files")
if errors:
    print("Errors:")
    for err in errors[:10]:
        print(f"  {err}")
