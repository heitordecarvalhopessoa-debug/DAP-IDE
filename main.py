from src.python.lexer import tokenize
from src.python.interpreter import DAPInterpreter
from src.python.ide_ui import DAPIDE

def main():
    def run_dap_code(code, output_callback, check_stop, register_interpreter):
        try:
            instructions = tokenize(code)
            interpreter = DAPInterpreter(output_callback=output_callback, check_stop_callback=check_stop)
            register_interpreter(interpreter)
            interpreter.run(instructions)
        except Exception as e:
            output_callback(f"[System Error]: {e}")

    ide = DAPIDE(run_callback_factory=run_dap_code)
    ide.mainloop()

if __name__ == "__main__":
    main()