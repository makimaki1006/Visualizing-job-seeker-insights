# -*- coding: utf-8 -*-
"""Fix sys.stdout issue in generate_*.py files"""
import re
from pathlib import Path

# Files to fix
files_to_fix = [
    'generate_desired_area_pattern.py',
    'generate_mobility_pattern.py',
    'generate_qualification_detail.py',
    'generate_residence_flow.py'
]

old_pattern = r"sys\.stdout = io\.TextIOWrapper\(sys\.stdout\.buffer, encoding='utf-8'\)"
new_code = """try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (ValueError, AttributeError):
    # stdout already configured or not available
    pass"""

for filename in files_to_fix:
    filepath = Path(__file__).parent / filename
    if not filepath.exists():
        print(f"Skip {filename} (not found)")
        continue

    content = filepath.read_text(encoding='utf-8')

    # Replace the old pattern with new safe version
    new_content = re.sub(old_pattern, new_code, content)

    if new_content != content:
        filepath.write_text(new_content, encoding='utf-8')
        print(f"Fixed {filename}")
    else:
        print(f"No change needed for {filename}")

print("\nAll files processed.")
