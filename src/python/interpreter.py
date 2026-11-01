import re
import time
import math
import random

class DAPInterpreter:
    def __init__(self, output_callback, check_stop_callback):
        self.variables = {}
        self.globals = set()
        self.output_callback = output_callback
        self.check_stop_callback = check_stop_callback
        self.key_listeners = []
        self.last_condition_met = False

    def check_interruption(self):
        if self.check_stop_callback and self.check_stop_callback():
            raise InterruptedError("[Execution stopped by user]")

    def evaluate_expression(self, expr_str):
        self.check_interruption()
        expr_str = expr_str.strip()

        if expr_str in self.variables and isinstance(self.variables[expr_str], dict):
            return self.variables[expr_str]

        func_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)$', expr_str)
        if func_match:
            tipo_func = func_match.group(1).lower()
            inner_val = func_match.group(2).strip()
            
            if tipo_func == 'float':
                try:
                    return float(inner_val)
                except ValueError:
                    return f"[Error: '{inner_val}' is not a valid float]"
                    
            elif tipo_func == 'bool':
                if inner_val.lower() == 'true':
                    return True
                elif inner_val.lower() == 'false':
                    return False
                return f"[Error: '{inner_val}' is not a valid bool]"
                
            elif tipo_func in ('st', 'str'):
                if (inner_val.startswith('"') and inner_val.endswith('"')) or (inner_val.startswith("'") and inner_val.endswith("'")):
                    return str(inner_val[1:-1])
                return str(inner_val)
                
            elif tipo_func == 'char':
                clean_char = inner_val.strip("'\"")
                if len(clean_char) >= 1:
                    return str(clean_char[0])
                return "[Error: invalid char()]"
                
            elif tipo_func == 'null':
                return None

            elif tipo_func == 'random':
                parts = [p.strip() for p in inner_val.split(',')]
                if len(parts) == 2:
                    try:
                        vmin = int(self.evaluate_expression(parts[0]))
                        vmax = int(self.evaluate_expression(parts[1]))
                        return random.randint(vmin, vmax)
                    except Exception:
                        return "[Error: random() requires valid integer bounds]"
                return "[Error: random() requires two arguments]"

        try:
            return float(expr_str)
        except ValueError:
            pass

        if expr_str.lower() == 'true':
            return True
        if expr_str.lower() == 'false':
            return False
        if expr_str.lower() == 'null':
            return None

        if (expr_str.startswith('"') and expr_str.endswith('"')) or (expr_str.startswith("'") and expr_str.endswith("'")):
            return str(expr_str[1:-1])

        eval_str = expr_str
        eval_str = re.sub(r'([a-zA-Z_]\w*|\d+(\.\d+)?)!', r'math.factorial(int(\1))', eval_str)
        eval_str = eval_str.replace('^', '**')
        eval_str = eval_str.replace('=>', '>=')

        eval_str = re.sub(r'\bAND\b', 'and', eval_str)
        eval_str = re.sub(r'\bOR\b', 'or', eval_str)
        eval_str = re.sub(r'\bNOT\b', 'not', eval_str)
        eval_str = re.sub(r'\bXOR\b', '!=', eval_str)
        eval_str = re.sub(r'\bNAND\b', 'not and', eval_str)
        eval_str = re.sub(r'\bNOR\b', 'not or', eval_str)
        eval_str = re.sub(r'\bXNOR\b', '==', eval_str)

        tokens = re.findall(r'[a-zA-Z_]\w*', eval_str)
        for token in sorted(tokens, key=len, reverse=True):
            if token in self.variables and not isinstance(self.variables[token], dict):
                val = self.variables[token]
                if isinstance(val, (int, float, str, bool)):
                    if isinstance(val, str):
                        eval_str = re.sub(r'\b' + token + r'\b', f"'{val}'", eval_str)
                    else:
                        eval_str = re.sub(r'\b' + token + r'\b', str(val), eval_str)

        try:
            result = eval(eval_str, {"__builtins__": None}, {"math": math, "factorial": math.factorial})
            if isinstance(result, (int, float, bool, str)):
                return result
            return float(result) if isinstance(result, (int, float)) else result
        except Exception:
            pass

        if expr_str in self.variables:
            return self.variables[expr_str]

        return f"[Error: Invalid expression or unknown value '{expr_str}']"

    def execute_block(self, instructions):
        for inst in instructions:
            self.check_interruption()
            tipo = inst[0]
            
            if tipo == 'GLOBAL':
                name = inst[1]
                raw_val = inst[2]
                if name in self.globals or name in self.variables:
                    self.output_callback(f"[Runtime Error]: GLOBAL variable '{name}' cannot be redefined.")
                else:
                    self.variables[name] = self.evaluate_expression(raw_val)
                    self.globals.add(name)

            elif tipo == 'VAR':
                name = inst[1]
                raw_val = inst[2]
                if name in self.globals:
                    self.output_callback(f"[Runtime Error]: Cannot overwrite GLOBAL variable '{name}' with VAR.")
                else:
                    self.variables[name] = self.evaluate_expression(raw_val)

            elif tipo == 'ASSIGN':
                name = inst[1]
                raw_val = inst[2]
                if name in self.globals:
                    self.output_callback(f"[Runtime Error]: Cannot overwrite GLOBAL variable '{name}'.")
                else:
                    self.variables[name] = self.evaluate_expression(raw_val)

            elif tipo == 'CLEAR':
                name = inst[1]
                if name in self.variables:
                    if name in self.globals:
                        self.output_callback(f"[Runtime Error]: Cannot clear GLOBAL variable '{name}'.")
                    else:
                        self.variables[name] = None
                else:
                    self.output_callback(f"[Runtime Error]: Variable '{name}' does not exist.")
                
            elif tipo == 'TABLE_BLOCK':
                name = inst[1]
                block = inst[2]
                table_dict = {}
                for sub_inst in block:
                    self.check_interruption()
                    sub_tipo = sub_inst[0]
                    if sub_tipo in ('VAR', 'GLOBAL', 'ASSIGN'):
                        sub_name = sub_inst[1]
                        sub_val = self.evaluate_expression(sub_inst[2])
                        table_dict[sub_name] = sub_val
                    elif sub_tipo == 'TABLE_BLOCK':
                        sub_name = sub_inst[1]
                        sub_block = sub_inst[2]
                        dummy_interp = DAPInterpreter(lambda x: None, self.check_stop_callback)
                        dummy_interp.execute_block(sub_block)
                        table_dict[sub_name] = dummy_interp.variables
                if name in self.globals:
                    self.output_callback(f"[Runtime Error]: Cannot overwrite GLOBAL variable '{name}'.")
                else:
                    self.variables[name] = table_dict

            elif tipo == 'ALTERATE':
                name = inst[1]
                raw_val = inst[2]
                if name in self.globals:
                    self.output_callback(f"[Runtime Error]: Cannot alter GLOBAL variable '{name}'.")
                elif name in self.variables:
                    self.variables[name] = self.evaluate_expression(raw_val)
                else:
                    self.output_callback(f"[Runtime Error]: Variable '{name}' does not exist.")
                
            elif tipo == 'OUTPUT':
                raw_val = inst[1]
                evaluated_val = self.evaluate_expression(raw_val)
                self.output_callback(str(evaluated_val))
                
            elif tipo == 'EXPR':
                expr_str = inst[1]
                m = re.match(r'^([a-zA-Z_]\w*)\s*([\+\-\*\/\^!].*)$', expr_str)
                if m:
                    var_name = m.group(1)
                    if var_name in self.variables:
                        res = self.evaluate_expression(expr_str)
                        if var_name in self.globals:
                            self.output_callback(f"[Runtime Error]: Cannot alter GLOBAL variable '{var_name}'.")
                        else:
                            self.variables[var_name] = res
                    else:
                        self.evaluate_expression(expr_str)
                else:
                    self.evaluate_expression(expr_str)
                
            elif tipo == 'WAIT':
                raw_val = inst[1]
                evaluated_val = self.evaluate_expression(raw_val)
                try:
                    seconds = float(evaluated_val)
                    elapsed = 0.0
                    while elapsed < seconds:
                        self.check_interruption()
                        time.sleep(0.05)
                        elapsed += 0.05
                except InterruptedError:
                    raise
                except Exception:
                    self.output_callback("[Runtime Error]: wait() requires a valid number of seconds.")
                
            elif tipo == 'REPEAT':
                count_raw = inst[1]
                block = inst[2]
                evaluated_count = self.evaluate_expression(count_raw)
                try:
                    limit = int(evaluated_count)
                    for _ in range(limit):
                        self.execute_block(block)
                except InterruptedError:
                    raise
                except Exception:
                    self.output_callback("[Runtime Error]: repeat() requires a valid number.")
                
            elif tipo == 'FOREVER':
                block = inst[1]
                while True:
                    self.check_interruption()
                    self.execute_block(block)
                    time.sleep(0.01)

            elif tipo == 'IF':
                cond_raw = inst[1]
                block = inst[2]
                res = self.evaluate_expression(cond_raw)
                if bool(res):
                    self.execute_block(block)
                    self.last_condition_met = True
                else:
                    self.last_condition_met = False

            elif tipo == 'ELSEIF':
                if not self.last_condition_met:
                    cond_raw = inst[1]
                    block = inst[2]
                    res = self.evaluate_expression(cond_raw)
                    if bool(res):
                        self.execute_block(block)
                        self.last_condition_met = True
                    else:
                        self.last_condition_met = False

            elif tipo == 'ELSE':
                if not self.last_condition_met:
                    block = inst[1]
                    self.execute_block(block)
                    self.last_condition_met = True

            elif tipo in ('KEYBOARD', 'KEYCODE', 'OTH'):
                target_key = inst[1]
                block = inst[2]
                self.key_listeners.append((tipo, target_key, block))
                
            elif tipo == 'ERROR':
                self.output_callback(f"[Syntax Error]: {inst[1]}")

    def run(self, instructions):
        self.variables.clear()
        self.globals.clear()
        self.key_listeners.clear()
        self.last_condition_met = False
        try:
            self.execute_block(instructions)
        except InterruptedError as e:
            self.output_callback(str(e))