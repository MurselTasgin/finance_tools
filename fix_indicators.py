#!/usr/bin/env python3
"""Fix indicator files by adding get_asset_types() method correctly"""

import os
import re

def fix_file(filepath, asset_type):
    """Fix a single file by adding get_asset_types() method"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Skip if already has get_asset_types implemented
    if 'def get_asset_types(self)' in content and 'return [' + asset_type + ']' in content:
        return 0
    
    lines = content.split('\n')
    new_lines = []
    
    in_broken_section = False
    required_col_added = False
    
    for i, line in enumerate(lines):
        # Check if this line has the broken get_asset_types
        if 'def get_asset_types' in line and not required_col_added:
            # We need to look back and find get_required_columns
            in_broken_section = True
            continue
        
        if in_broken_section and 'def get_parameter_schema' in line:
            # We found the parameter schema, now insert correctly
            new_lines.append("")
            new_lines.append(f"    def get_asset_types(self) -> List[str]:")
            new_lines.append(f"        \"\"\"{asset_type.capitalize()}-specific indicator\"\"")
            new_lines.append(f"        return ['{asset_type}']")
            new_lines.append("")
            in_broken_section = False
            required_col_added = True
            
        # Skip broken lines
        if in_broken_section:
            if line.strip().startswith('"""'):
                continue
            if line.strip().startswith('return'):
                continue
            
        new_lines.append(line)
        
        # Check if we just added get_required_columns and haven't added asset types yet
        if 'def get_required_columns(self)' in line and not required_col_added:
            # Check next few lines
            lookahead = 3
            found_return = False
            for j in range(i+1, min(i+lookahead+1, len(lines))):
                if lines[j].strip().startswith('return ['):
                    found_return = True
                    break
            if found_return and i + lookahead < len(lines):
                # Insert after the return statement
                idx = new_lines.index(line)
                new_lines.append("")
                new_lines.append(f"    def get_asset_types(self) -> List[str]:")
                new_lines.append(f"        \"\"\"{asset_type.capitalize()}-specific indicator\"\"")
                new_lines.append(f"        return ['{asset_type}']")
                required_col_added = True
    
    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    return 1

# Fix stock indicators
stock_dir = "finance_tools/analysis/indicators/implementations/stock"
etf_dir = "finance_tools/analysis/indicators/implementations/etf"

fixed = 0
for file in os.listdir(stock_dir):
    if file.endswith('.py') and file != '__init__.py':
        file_path = os.path.join(stock_dir, file)
        fixed += fix_file(file_path, 'stock')
        print(f"Fixed {file_path}")

for file in os.listdir(etf_dir):
    if file.endswith('.py') and file != '__init__.py':
        file_path = os.path.join(etf_dir, file)
        fixed += fix_file(file_path, 'etf')
        print(f"Fixed {file_path}")

print(f"Fixed {fixed} files")

