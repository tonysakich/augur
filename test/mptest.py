import socket
import multiprocessing as mp
from augur.core import threads

def start_node(password):
    core = mp.Process(target=threads.main, args=(password,))
    core.daemon = True
    core.start()

def stop_node():
    if core.is_alive():
        core.terminate()

if __name__ == "__main__":
    password = "testpassword"
    host = "localhost"
    port = 8899
    c = mp.Process(target=threads.main, args=(password,))
    c.daemon = True
    c.start()
    if c.is_alive():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(5)
        s.connect((host, port))
