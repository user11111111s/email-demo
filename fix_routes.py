import os

file_path = 'app/routes.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_conflict = False
keep_block = False

for line in lines:
    if line.startswith('<<<<<<< HEAD'):
        in_conflict = True
        keep_block = True
    elif line.startswith('======='):
        keep_block = False
    elif line.startswith('>>>>>>>'):
        in_conflict = False
    else:
        if not in_conflict:
            new_lines.append(line)
        elif keep_block:
            new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Conflicts resolved keeping HEAD.")
