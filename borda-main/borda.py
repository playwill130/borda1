from xmlrpc.server import SimpleXMLRPCServer
import threading
import xmlrpc.client
import time

# Dicionários para armazenar informações dos nós e arquivos
node_registry = {}
file_registry = {}

# Função para registrar um nó com seus arquivos
def register_node(host, port, node_files):
    node_registry[(host, port)] = node_files
    return True

# Função para adicionar um arquivo ao registro
def register_file(host, port, filename, checksum):
    if filename not in file_registry:
        file_registry[filename] = []
    file_registry[filename].append((host, port, checksum))
    return True

# Função para buscar informações sobre um arquivo
def locate_file(filename):
    return file_registry.get(filename, [])

# Função que verifica periodicamente os arquivos nos nós
def periodic_check():
    while True:
        print("Verificando arquivos nos nós:")
        for (host, port), node_files in node_registry.items():
            print(f"Nó em {host}:{port} possui os arquivos:")
            for filename, checksum in node_files.items():
                print(f"- {filename}")
        print("")
        time.sleep(5)  # Intervalo de verificação de 5 segundos

# Função para encontrar um nó que possui um arquivo específico
def find_node_with_file(filename):
    for (host, port), node_files in node_registry.items():
        if filename in node_files:
            return (host, port)
    return None

# Função para iniciar o nó de borda
def start_edge_node(host, port):
    server = SimpleXMLRPCServer((host, port), allow_none=True)
    server.register_function(register_node, "register_node")
    server.register_function(register_file, "register_file")
    server.register_function(locate_file, "locate_file")
    server.register_function(find_node_with_file, "find_node_with_file")
    
    threading.Thread(target=server.serve_forever).start()
    threading.Thread(target=periodic_check).start()  # Thread para verificação periódica
    print(f"Nó de borda executando em {host}:{port}")

if __name__ == "__main__":
    edge_node_host = 'localhost'
    edge_node_port = 8000
    start_edge_node(edge_node_host, edge_node_port)
    input("Pressione Enter para finalizar...\n")
