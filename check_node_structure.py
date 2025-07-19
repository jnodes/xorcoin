import ast

# Parse the node.py file to check its structure
try:
    with open('xorcoin/network/p2p/node.py', 'r') as f:
        content = f.read()
    
    # Try to parse it
    tree = ast.parse(content)
    
    # Find all class and method definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            print(f"Class: {node.name} at line {node.lineno}")
            # Find methods in this class
            for item in node.body:
                if isinstance(item, ast.FuncDef):
                    print(f"  Method: {item.name} at line {item.lineno}")
                    if item.name == "_handle_version":
                        print("    ✓ Found _handle_version!")
                        
except SyntaxError as e:
    print(f"Syntax error in file: {e}")
    print(f"Line {e.lineno}: {e.text}")
except Exception as e:
    print(f"Error: {e}")
    
# Also try importing to see what happens
try:
    import xorcoin.network.p2p.node as node_module
    if hasattr(node_module, 'P2PNode'):
        p2p_class = node_module.P2PNode
        print(f"\nP2PNode methods: {[m for m in dir(p2p_class) if m.startswith('_handle')]}")
except Exception as e:
    print(f"\nImport error: {e}")
