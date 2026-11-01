import re

def parse_single_line(line):
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*[\+\-\*\/\^!]', line) or re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', line):
        return ('EXPR', line)

    global_match = re.match(r'^GLOBAL\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$', line)
    if global_match:
        return ('GLOBAL', global_match.group(1), global_match.group(2).strip())

    var_match = re.match(r'^VAR\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$', line)
    if var_match:
        return ('VAR', var_match.group(1), var_match.group(2).strip())

    assign_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$', line)
    if assign_match:
        return ('ASSIGN', assign_match.group(1), assign_match.group(2).strip())
        
    clear_match = re.match(r'^clear\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)$', line)
    if clear_match:
        return ('CLEAR', clear_match.group(1).strip())
        
    alt_match = re.match(r'^alterate\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*,\s*(.+)\s*\)$', line)
    if alt_match:
        return ('ALTERATE', alt_match.group(1), alt_match.group(2).strip())
        
    out_match = re.match(r'^output\s*\((.*)\)$', line)
    if out_match:
        return ('OUTPUT', out_match.group(1).strip())
        
    wait_match = re.match(r'^wait\s*\((.*)\)$', line)
    if wait_match:
        return ('WAIT', wait_match.group(1).strip())
        
    return ('ERROR', line)

def parse_block(lines, index):
    block_instructions = []
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        
        if not line or line.startswith('#'):
            continue
            
        if line == ']':
            break
            
        rep_match = re.match(r'^repeat\s*\((.+)\)\s*\[$', line)
        if rep_match:
            count_raw = rep_match.group(1).strip()
            sub_block, index = parse_block(lines, index)
            block_instructions.append(('REPEAT', count_raw, sub_block))
            continue
            
        fore_match = re.match(r'^forever\s*\[$', line)
        if fore_match:
            sub_block, index = parse_block(lines, index)
            block_instructions.append(('FOREVER', sub_block))
            continue

        if_match = re.match(r'^IF\s*\((.+)\)\s*\[$', line)
        if if_match:
            cond = if_match.group(1).strip()
            sub_block, index = parse_block(lines, index)
            block_instructions.append(('IF', cond, sub_block))
            continue

        elseif_match = re.match(r'^ELSEIF\s*\((.+)\)\s*\[$', line)
        if elseif_match:
            cond = elseif_match.group(1).strip()
            sub_block, index = parse_block(lines, index)
            block_instructions.append(('ELSEIF', cond, sub_block))
            continue

        else_match = re.match(r'^ELSE\s*\[$', line)
        if else_match:
            sub_block, index = parse_block(lines, index)
            block_instructions.append(('ELSE', sub_block))
            continue
            
        table_match = re.match(r'^TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\[$', line)
        if table_match:
            table_name = table_match.group(1)
            sub_block, index = parse_block(lines, index)
            block_instructions.append(('TABLE_BLOCK', table_name, sub_block))
            continue

        kb_match = re.match(r'^(keyboard|keycode|oth)\s*\(([^)]+)\)\s*\[$', line)
        if kb_match:
            ev_type = kb_match.group(1).lower()
            ev_key = kb_match.group(2).strip().strip('"\'')
            sub_block, index = parse_block(lines, index)
            
            if ev_type == 'keyboard':
                if len(ev_key) != 1:
                    block_instructions.append(('ERROR', f"keyboard() requires exactly 1 character, got '{ev_key}'"))
                else:
                    block_instructions.append(('KEYBOARD', ev_key.lower(), sub_block))
            elif ev_type == 'keycode':
                if len(ev_key) < 1:
                    block_instructions.append(('ERROR', f"keycode() requires at least 1 character"))
                else:
                    block_instructions.append(('KEYCODE', ev_key.upper(), sub_block))
            elif ev_type == 'oth':
                if len(ev_key) < 1:
                    block_instructions.append(('ERROR', f"oth() requires a special key name"))
                else:
                    block_instructions.append(('OTH', ev_key.lower(), sub_block))
            continue
            
        block_instructions.append(parse_single_line(line))
        
    return block_instructions, index

def tokenize(code):
    lines = code.split('\n')
    instructions = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith('#'):
            continue
            
        rep_match = re.match(r'^repeat\s*\((.+)\)\s*\[$', line)
        if rep_match:
            count_raw = rep_match.group(1).strip()
            sub_block, i = parse_block(lines, i)
            instructions.append(('REPEAT', count_raw, sub_block))
            continue
            
        fore_match = re.match(r'^forever\s*\[$', line)
        if fore_match:
            sub_block, i = parse_block(lines, i)
            instructions.append(('FOREVER', sub_block))
            continue

        if_match = re.match(r'^IF\s*\((.+)\)\s*\[$', line)
        if if_match:
            cond = if_match.group(1).strip()
            sub_block, i = parse_block(lines, i)
            instructions.append(('IF', cond, sub_block))
            continue

        elseif_match = re.match(r'^ELSEIF\s*\((.+)\)\s*\[$', line)
        if elseif_match:
            cond = elseif_match.group(1).strip()
            sub_block, i = parse_block(lines, i)
            instructions.append(('ELSEIF', cond, sub_block))
            continue

        else_match = re.match(r'^ELSE\s*\[$', line)
        if else_match:
            sub_block, i = parse_block(lines, i)
            instructions.append(('ELSE', sub_block))
            continue
            
        table_match = re.match(r'^TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\[$', line)
        if table_match:
            table_name = table_match.group(1)
            sub_block, i = parse_block(lines, i)
            instructions.append(('TABLE_BLOCK', table_name, sub_block))
            continue

        kb_match = re.match(r'^(keyboard|keycode|oth)\s*\(([^)]+)\)\s*\[$', line)
        if kb_match:
            ev_type = kb_match.group(1).lower()
            ev_key = kb_match.group(2).strip().strip('"\'')
            sub_block, i = parse_block(lines, i)
            
            if ev_type == 'keyboard':
                if len(ev_key) != 1:
                    instructions.append(('ERROR', f"keyboard() requires exactly 1 character, got '{ev_key}'"))
                else:
                    instructions.append(('KEYBOARD', ev_key.lower(), sub_block))
            elif ev_type == 'keycode':
                if len(ev_key) < 1:
                    instructions.append(('ERROR', f"keycode() requires at least 1 character"))
                else:
                    instructions.append(('KEYCODE', ev_key.upper(), sub_block))
            elif ev_type == 'oth':
                if len(ev_key) < 1:
                    instructions.append(('ERROR', f"oth() requires a special key name"))
                else:
                    instructions.append(('OTH', ev_key.lower(), sub_block))
            continue
            
        instructions.append(parse_single_line(line))
        
    return instructions