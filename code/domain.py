import os
import re

# Define default file paths
default_input_file = r"C:\Users\30752\Desktop\available_github_usernames_.txt"
output_dir = r"C:\Users\30752\OneDrive\Code-win\py-win\build"
script_dir = r"C:\Users\30752\OneDrive\Code-win\py-win\test"

# Get input file path from user
print("Enter input file path (press Enter to use default):")
user_input = input().strip()

# Handle different quote styles and empty input
if user_input:
    # Remove quotes if present
    user_input = user_input.strip('"\'')
    input_file = user_input
else:
    input_file = default_input_file

print(f"Using input file: {input_file}")

# Get custom pattern if any
print("Enter custom pattern (press Enter to skip):")
custom_pattern = input().strip()

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Define pattern functions
def is_aaaa(domain):
    # Check if domain follows AAAA pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return all(c == name[0] for c in name)
    return False

def is_aaab(domain):
    # Check if domain follows AAAB pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[0] == name[1] == name[2] and name[0] != name[3]
    return False

def is_aaba(domain):
    # Check if domain follows AABA pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[0] == name[1] == name[3] and name[0] != name[2]
    return False

def is_abaa(domain):
    # Check if domain follows ABAA pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[0] == name[2] == name[3] and name[0] != name[1]
    return False

def is_aabc(domain):
    # Check if domain follows AABC pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[0] == name[1] and name[0] != name[2] and name[2] != name[3]
    return False

def is_abbc(domain):
    # Check if domain follows ABBC pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[1] == name[2] and name[0] != name[1] and name[1] != name[3]
    return False

def is_abcc(domain):
    # Check if domain follows ABCC pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[2] == name[3] and name[0] != name[1] and name[0] != name[2]
    return False

def is_abac(domain):
    # Check if domain follows ABAC pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[0] == name[2] and name[1] != name[3] and name[0] != name[1]
    return False

def is_abca(domain):
    # Check if domain follows ABCA pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[0] == name[3] and name[0] != name[1] and name[1] != name[2]
    return False

def is_abcb(domain):
    # Check if domain follows ABCB pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[1] == name[3] and name[0] != name[1] and name[1] != name[2]
    return False

def is_aabb(domain):
    # Check if domain follows AABB pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[0] == name[1] and name[2] == name[3] and name[0] != name[2]
    return False

def is_abba(domain):
    # Check if domain follows ABBA pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[0] == name[3] and name[1] == name[2] and name[0] != name[1]
    return False

def is_abab(domain):
    # Check if domain follows ABAB pattern
    name = domain.split('.')[0]
    if len(name) == 4:
        return name[0] == name[2] and name[1] == name[3] and name[0] != name[1]
    return False

def is_custom_pattern(domain, pattern):
    # Check if domain matches custom pattern
    name = domain.split('.')[0]
    if len(name) != 4 or len(pattern) != 4:
        return False
    
    # Create a mapping of positions that should be equal
    equal_positions = {}
    for i in range(4):
        if pattern[i].isupper():
            # Find all positions with the same uppercase letter
            for j in range(4):
                if pattern[j] == pattern[i]:
                    if i not in equal_positions:
                        equal_positions[i] = []
                    equal_positions[i].append(j)
    
    # Check if specified lowercase letters match
    for i in range(4):
        if pattern[i].islower():
            if name[i] != pattern[i]:
                return False
    
    # Check if positions that should be equal are actually equal
    for pos, equal_to in equal_positions.items():
        for eq_pos in equal_to:
            if name[pos] != name[eq_pos]:
                return False
    
    return True

# Initialize pattern files dictionary
pattern_files = {}

try:
    # Read the input file and process domains
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            domain = line.strip()
            if not domain:
                continue
            
            # Check custom pattern if specified
            if custom_pattern:
                if is_custom_pattern(domain, custom_pattern):
                    custom_filename = f'custom_{custom_pattern}_domains.txt'
                    if custom_filename not in pattern_files:
                        pattern_files[custom_filename] = open(os.path.join(output_dir, custom_filename), 'w', encoding='utf-8')
                    pattern_files[custom_filename].write(domain + '\n')
            
            # Check each pattern and create files only if matches are found
            if is_aaaa(domain):
                if 'aaaa' not in pattern_files:
                    pattern_files['aaaa'] = open(os.path.join(output_dir, 'aaaa_domains.txt'), 'w', encoding='utf-8')
                pattern_files['aaaa'].write(domain + '\n')
                
            if is_aaab(domain):
                if 'aaab' not in pattern_files:
                    pattern_files['aaab'] = open(os.path.join(output_dir, 'aaab_domains.txt'), 'w', encoding='utf-8')
                pattern_files['aaab'].write(domain + '\n')
                
            if is_aaba(domain):
                if 'aaba' not in pattern_files:
                    pattern_files['aaba'] = open(os.path.join(output_dir, 'aaba_domains.txt'), 'w', encoding='utf-8')
                pattern_files['aaba'].write(domain + '\n')
                
            if is_abaa(domain):
                if 'abaa' not in pattern_files:
                    pattern_files['abaa'] = open(os.path.join(output_dir, 'abaa_domains.txt'), 'w', encoding='utf-8')
                pattern_files['abaa'].write(domain + '\n')
                
            if is_aabc(domain):
                if 'aabc' not in pattern_files:
                    pattern_files['aabc'] = open(os.path.join(output_dir, 'aabc_domains.txt'), 'w', encoding='utf-8')
                pattern_files['aabc'].write(domain + '\n')
                
            if is_abbc(domain):
                if 'abbc' not in pattern_files:
                    pattern_files['abbc'] = open(os.path.join(output_dir, 'abbc_domains.txt'), 'w', encoding='utf-8')
                pattern_files['abbc'].write(domain + '\n')
                
            if is_abcc(domain):
                if 'abcc' not in pattern_files:
                    pattern_files['abcc'] = open(os.path.join(output_dir, 'abcc_domains.txt'), 'w', encoding='utf-8')
                pattern_files['abcc'].write(domain + '\n')
                
            if is_abac(domain):
                if 'abac' not in pattern_files:
                    pattern_files['abac'] = open(os.path.join(output_dir, 'abac_domains.txt'), 'w', encoding='utf-8')
                pattern_files['abac'].write(domain + '\n')
                
            if is_abca(domain):
                if 'abca' not in pattern_files:
                    pattern_files['abca'] = open(os.path.join(output_dir, 'abca_domains.txt'), 'w', encoding='utf-8')
                pattern_files['abca'].write(domain + '\n')
                
            if is_abcb(domain):
                if 'abcb' not in pattern_files:
                    pattern_files['abcb'] = open(os.path.join(output_dir, 'abcb_domains.txt'), 'w', encoding='utf-8')
                pattern_files['abcb'].write(domain + '\n')

            if is_aabb(domain):
                if 'aabb' not in pattern_files:
                    pattern_files['aabb'] = open(os.path.join(output_dir, 'aabb_domains.txt'), 'w', encoding='utf-8')
                pattern_files['aabb'].write(domain + '\n')

            if is_abba(domain):
                if 'abba' not in pattern_files:
                    pattern_files['abba'] = open(os.path.join(output_dir, 'abba_domains.txt'), 'w', encoding='utf-8')
                pattern_files['abba'].write(domain + '\n')

            if is_abab(domain):
                if 'abab' not in pattern_files:
                    pattern_files['abab'] = open(os.path.join(output_dir, 'abab_domains.txt'), 'w', encoding='utf-8')
                pattern_files['abab'].write(domain + '\n')
    
    # Print summary
    print("Domain filtering complete. Results saved to build directory.")

finally:
    # Close all files
    for file in pattern_files.values():
        file.close()
