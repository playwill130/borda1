import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
import threading
import os
import hashlib
import base64

def calculate_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def get_local_files():
    files = {}
    for file in os.listdir('.'):
        if os.path.isfile(file):
            checksum = calculate_checksum(file)
            files[file] = checksum
    return files

def register_with_edge_node(edge_node_host, edge_node_port, node_host, node_port):
    with xmlrpc.client.ServerProxy(f'http://{edge_node_host}:{edge_node_port}/') as proxy:
        local_files = get_local_files()
        proxy.register_node(node_host, node_port, local_files)
        for file, checksum in local_files.items():
            proxy.register_file(node_host, node_port, file, checksum)

def download_file_from_node(node_host, node_port, filename):
    try:
        with xmlrpc.client.ServerProxy(f'http://{node_host}:{node_port}/') as proxy:
            file_data = proxy.download(filename)
            file_data_bytes = base64.b64decode(file_data)
            with open(filename, 'wb') as f:
                f.write(file_data_bytes)
            return f"File '{filename}' downloaded successfully."
    except xmlrpc.client.Fault as fault:
        return f"XML-RPC Fault: {fault.faultString} (code: {fault.faultCode})"
    except xmlrpc.client.ProtocolError as err:
        return f"A protocol error occurred: {err.errmsg}"
    except Exception as e:
        return f"An error occurred: {e}"

def handle_download_request(filename):
    print(f"Received download request for file: {filename}")
    return download_file(filename)

def start_node(node_host, node_port, edge_node_host, edge_node_port):
    server = SimpleXMLRPCServer((node_host, node_port), allow_none=True)
    
    def download_file(filename):
        if os.path.isfile(filename):
            with open(filename, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        else:
            raise FileNotFoundError(f"File '{filename}' not found on this node.")

    server.register_function(download_file, "download")
    
    threading.Thread(target=server.serve_forever).start()
    register_with_edge_node(edge_node_host, edge_node_port, node_host, node_port)
    print(f"Node running on {node_host}:{node_port}")

if __name__ == "__main__":
    node_host = 'localhost'
    node_port = 8001
    edge_node_host = 'localhost'
    edge_node_port = 8000
    start_node(node_host, node_port, edge_node_host, edge_node_port)

    while True:
        filename = input("Enter the name of the file to download (or 'exit' to quit): ")
        if filename.lower() == 'exit':
            break
        
        try:
            with xmlrpc.client.ServerProxy(f'http://{edge_node_host}:{edge_node_port}/') as proxy:
                node_info = proxy.find_node_with_file(filename)
                if node_info:
                    node_host, node_port = node_info
                    print(f"File '{filename}' found at node {node_host}:{node_port}. Downloading...")
                    result = download_file_from_node(node_host, node_port, filename)
                    print(result)
                else:
                    print(f"File '{filename}' not found in the network.")
        except Exception as e:
            print(f"Error communicating with edge node: {e}")
