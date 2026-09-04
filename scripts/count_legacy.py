import re
with open('systems/stack_manager.py', encoding='utf-8') as f:
    source = f.read()

start = source.find('def _ejecutar_accion(')
body = source[start:]

actions = re.findall(r'(?:if|elif)\s+accion\s*==\s*"(\w+)"', body)
actions += re.findall(r'elif\s+accion\s+in\s*\([^)]*"(\w+)"', body)

print(f'Acciones en elif legacy: {len(actions)}')
for a in sorted(set(actions)):
    print(f'  - {a}')
