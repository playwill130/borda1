import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
import threading
import os
import hashlib
import base64

# Função para calcular o checksum de um arquivo
def compute_checksum(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

# Função para obter os arquivos locais com seus checksums
def list_local_files():
    local_files = {}
    for filename in os.listdir('.'):
        if os.path.isfile(filename):
            checksum = compute_checksum(filename)
            local_files[filename] = checksum
    return local_files

# Função para registrar um nó no nó de borda
def register_node_with_edge(edge_host, edge_port, node_host, node_port):
    with xmlrpc.client.ServerProxy(f'http://{edge_host}:{edge_port}/') as proxy:
        local_files = list_local_files()
        proxy.register_node(node_host, node_port, local_files)
        for filename, checksum in local_files.items():
            proxy.register_file(node_host, node_port, filename, checksum)

# Função para baixar um arquivo de outro nó
def download_file_from_peer(node_host, node_port, filename):
    try:
        with xmlrpc.client.ServerProxy(f'http://{node_host}:{node_port}/') as proxy:
            file_data = proxy.download(filename)
            file_bytes = base64.b64decode(file_data)
            with open(filename, 'wb') as f:
                f.write(file_bytes)
            return f"Arquivo '{filename}' baixado com sucesso."
    except xmlrpc.client.Fault as fault:
        return f"Erro XML-RPC: {fault.faultString} (código: {fault.faultCode})"
    except xmlrpc.client.ProtocolError as err:
        return f"Erro de protocolo: {err.errmsg}"
    except Exception as e:
        return f"Ocorreu um erro: {e}"

# Função para tratar a solicitação de download de arquivo
def handle_download_request(filename):
    print(f"Solicitação de download recebida para o arquivo: {filename}")
    return download_file(filename)

# Função para iniciar um nó regular
def start_regular_node(node_host, node_port, edge_host, edge_port):
    server = SimpleXMLRPCServer((node_host, node_port), allow_none=True)
    
    def download_file(filename):
        if os.path.isfile(filename):
            with open(filename, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        else:
            raise FileNotFoundError(f"Arquivo '{filename}' não encontrado neste nó.")

    server.register_function(download_file, "download")
    
    threading.Thread(target=server.serve_forever).start()
    register_node_with_edge(edge_host, edge_port, node_host, node_port)
    print(f"Nó executando em {node_host}:{node_port}")

if __name__ == "__main__":
    node_host = 'localhost'
    node_port = 8002
    edge_host = 'localhost'
    edge_port = 8000
    start_regular_node(node_host, node_port, edge_host, edge_port)

    while True:
        filename = input("Digite o nome do arquivo para baixar (ou 'sair' para finalizar): ")
        if filename.lower() == 'sair':
            break
        
        try:
            with xmlrpc.client.ServerProxy(f'http://{edge_host}:{edge_port}/') as proxy:
                node_info = proxy.find_node_with_file(filename)
                if node_info:
                    peer_host, peer_port = node_info
                    print(f"Arquivo '{filename}' encontrado no nó {peer_host}:{peer_port}. Baixando...")
                    result = download_file_from_peer(peer_host, peer_port, filename)
                    print(result)
                else:
                    print(f"Arquivo '{filename}' não encontrado na rede.")
        except Exception as e:
            print(f"Erro ao comunicar com o nó de borda: {e}")
