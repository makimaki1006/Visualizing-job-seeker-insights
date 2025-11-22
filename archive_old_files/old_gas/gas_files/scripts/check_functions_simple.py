import re, os

with open('MenuIntegration.gs', 'r', encoding='utf-8') as f:
    menu_content = f.read()

function_pattern = r"\.addItem\(['\"].*?['\"]\s*,\s*['\"](\w+)['\"]"
menu_functions = sorted(set(re.findall(function_pattern, menu_content)))

print(f"Menu functions: {len(menu_functions)}\n")

gas_files = [f for f in os.listdir('.') if f.endswith('.gs') and not '.bak' in f]
all_functions = {}

for gas_file in gas_files:
    try:
        with open(gas_file, 'r', encoding='utf-8') as f:
            content = f.read()
        func_defs = re.findall(r'^function\s+(\w+)\s*\(', content, re.MULTILINE)
        for func_name in func_defs:
            if func_name not in all_functions:
                all_functions[func_name] = []
            all_functions[func_name].append(gas_file)
    except:
        pass

missing = []
found = []

for func in menu_functions:
    if func in all_functions:
        found.append((func, all_functions[func]))
    else:
        missing.append(func)

print("FOUND ({}/{}):".format(len(found), len(menu_functions)))
for func, files in found:
    print("  {} -> {}".format(func, ', '.join(files)))

print("\nMISSING ({}/{}):".format(len(missing), len(menu_functions)))
for func in missing:
    print("  {}".format(func))

print("\nSummary: {:.1f}% complete".format(len(found)/len(menu_functions)*100))
