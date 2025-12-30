#!/usr/bin/env python3
"""
Apply tab navigation patch to IgTabHostFragmentFactory.

This script patches the A00 method (or equivalent) to intercept tab loading
and redirect disabled tabs (Reels, Explore) to the DMs tab.
"""

import sys
import re

def find_method_start(content, method_signature_pattern):
    """Find the start of a method matching the pattern."""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if re.search(method_signature_pattern, line):
            return i
    return -1

def patch_tab_factory(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'Feurstagram' in content or 'FeurConfig' in content:
        print(f"  Already patched: {filepath}")
        return True
    
    # Find the method that uses "fragment_clips" - this is the tab loading method
    # We need to find where p2 (the fragment name) is first used
    
    # Look for the pattern: move-object/from16 vX, p2 followed by fragment checks
    # We'll insert our patch right after "move-object/from16 vX, p2"
    
    # Pattern: method uses p2 as fragment name parameter
    pattern = r'(move-object/from16\s+v\d+,\s+p2\s*\n)'
    
    match = re.search(pattern, content)
    if not match:
        # Try alternate pattern
        pattern = r'(move-object\s+v\d+,\s+p2\s*\n)'
        match = re.search(pattern, content)
    
    if not match:
        print(f"  Error: Could not find fragment parameter handling in {filepath}")
        return False
    
    # Extract the register used for p2
    move_line = match.group(1)
    reg_match = re.search(r'v(\d+)', move_line)
    if not reg_match:
        print(f"  Error: Could not extract register from: {move_line}")
        return False
    
    reg_num = reg_match.group(1)
    v_reg = f"v{reg_num}"
    
    # Create the patch code
    patch = f'''
    # Feurstagram: Check if this tab should be disabled and redirect to DMs
    # Check for fragment_clips (Reels)
    const-string/jumbo v0, "fragment_clips"
    invoke-virtual {{{v_reg}, v0}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :df_check_explore
    invoke-static {{}}, Lcom/feurstagram/FeurConfig;->isReelsDisabled()Z
    move-result v0
    if-eqz v0, :df_continue
    const-string/jumbo {v_reg}, "fragment_direct_tab"
    goto :df_continue

    :df_check_explore
    # Check for fragment_search (Explore)
    const-string/jumbo v0, "fragment_search"
    invoke-virtual {{{v_reg}, v0}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :df_continue
    invoke-static {{}}, Lcom/feurstagram/FeurConfig;->isExploreDisabled()Z
    move-result v0
    if-eqz v0, :df_continue
    const-string/jumbo {v_reg}, "fragment_direct_tab"

    :df_continue
'''
    
    # Insert the patch after the move instruction
    patched_content = content.replace(match.group(1), match.group(1) + patch)
    
    with open(filepath, 'w') as f:
        f.write(patched_content)
    
    print(f"  Patched: {filepath}")
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: apply_tab_patch.py <IgTabHostFragmentFactory.smali>")
        sys.exit(1)
    
    if not patch_tab_factory(sys.argv[1]):
        sys.exit(1)
