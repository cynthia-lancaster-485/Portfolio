#!usr/bin/python
import socket
import sys
import signal
from optparse import OptionParser
import urllib.parse
from time import *
import threading
from datetime import datetime

#Stores cached items
cache = {
    "URL": b"bytes"
}
# Stores blocked websites

blockList = ["test"]
cacheEnabled = False
blockingEnabled = False
timestamp = 1528797322
today = datetime.fromtimestamp(timestamp)
dateFormat = today.strftime("%a, %b %d %Y %H:%M:%S")
def ctrl_c_pressed(signal, frame): 
    sys.exit(0)
# Start of program execution
# Parse out the command line server address and port number to listen to
parser = OptionParser()
parser.add_option('-p', type='int', dest='serverPort')
parser.add_option('-a', type='string', dest='serverAddress')
(options, args) = parser.parse_args()
port = options.serverPort
address = options.serverAddress
if address is None:
    address = 'localhost'
if port is None:
    port = 2100
#Checks header for errors
def headerErrorCheck(headerData, client_socket):
    if(headerData[0]=="POST" or headerData[0]=="HEAD" or headerData[0]=="PUT" or headerData[0]=="DELETE"):
        commandError = (f"HTTP/1.0 501 Not Implemented\r\n")
        client_socket.sendall(commandError.encode())
        client_socket.close()
        return
    if(headerData[0]!='GET'):
        commandError = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(commandError.encode())
        client_socket.close()
        return
    if((len(headerData) < 3) or headerData[2]!='HTTP/1.0'):
        headerError = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(headerError.encode())
        client_socket.close()
        return
#hanfles requests for enabling and disabling the cahce and blocking
def handle_proxy_req(client_socket, urlData):
    global cacheEnabled
    global blockingEnabled
    if(urlData.path=="/proxy/cache/enable"):
        cacheEnabled = True
        error = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(error.encode())
        client_socket.close()
        return True
    if(urlData.path=="/proxy/cache/disable"):
        cacheEnabled = False
        error = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(error.encode())
        client_socket.close()
        return True
    if(urlData.path=="/proxy/cache/flush"):
        cache.clear()
        error = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(error.encode())
        client_socket.close()
        return True
    if(urlData.path=="/proxy/blocklist/enable"):
        blockingEnabled = True
        error = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(error.encode())
        client_socket.close()
        return True
    if(urlData.path=="/proxy/blocklist/disable"):
        blockingEnabled = False
        error = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(error.encode())
        client_socket.close()
        return
    if(urlData.path=="/proxy/blocklist/flush"):
        blockList.clear()
        error = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(error.encode())
        client_socket.close()
        return True
#handles block list operations
def handle_blocking_req(urlData, client_socket, origin, newPort):
    if("/proxy/blocklist/add/" in urlData.path):
        blockLines = urlData.path.split("/", 4)
        if(blockLines[4] not in blockList):
            blockList.append(blockLines[4])
        addBlocking = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(addBlocking.encode())
        client_socket.close()
        origin.close()
        return True
    if("/proxy/blocklist/remove/" in urlData.path):
        blockLines = urlData.path.split("/", 4)
        if(blockLines[4] in blockList):
            blockList.remove(blockLines[4])
        removeBlocking = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(removeBlocking.encode())
        client_socket.close()
        origin.close()
        return True
    if("/proxy/blocklist/flush/" in urlData.path):
        blockList.clear()
        flushBlocking = (f"HTTP/1.0 400 Bad Request\r\n")
        client_socket.sendall(flushBlocking.encode())
        client_socket.close()
        origin.close()
        return True
    for block in blockList: 
        if(blockingEnabled and (urlData.hostname.count(block) or str(newPort)==block or urlData.hostname + ":" + str(newPort)==block)):
            Blocking = (f"HTTP/1.0 403 Forbidden\r\n")
            client_socket.sendall(Blocking.encode())
            client_socket.close()
            origin.close()
            return True

#Handles each client that comes in
def handle_client(client_socket, client_addr):
    # recv request
    # parse request
    # fetch data from origin
    # send response
    content = ""
    urlData = ""
    newPort = 0
    lastModified = ""
    #Receives all the data from the client
    while True:
        recievingData = client_socket.recv(1024).decode()
        print(recievingData)
        content += recievingData
        if("\r\n\r\n" in content):
            break
    #We split the data from the client into lines, and then check the header data to create a request
    lines = content.split('\r\n')
    headerData = lines[0].split(" ")
    headerErrorCheck(headerData, client_socket)
    #Parsing the URL
    urlData = urllib.parse.urlparse(headerData[1], scheme='', allow_fragments=True)
    if(handle_proxy_req(client_socket, urlData)):
        return
    newPort = urlData.port
    #parsing through the other headers to store the data correctly 
    extraHeader = ""
    for headder_lines in lines[1: ]:
        if(headder_lines==""):
            continue
        header = headder_lines.split(": ", 1)
        if(header[0].endswith(" ")):
            headerError = (f"HTTP/1.0 400 Bad Request\r\n")
            client_socket.sendall(headerError.encode())
            client_socket.close()
            return
        if((len(header)!=2 and len(header)>0)):
            headerError = (f"HTTP/1.0 400 Bad Request\r\n")
            client_socket.sendall(headerError.encode())
            client_socket.close()
            return
        extraHeader += headder_lines + "\r\n"
        if("Connection: keep-alive" in extraHeader):
            extraHeader = extraHeader.replace("Connection: keep-alive", "Connection: close", 1)
    dataR = f"GET {urlData.path} HTTP/1.0\r\nHost: {urlData.netloc}{extraHeader}\r\nLast-Modified: {dateFormat}\r\nConnection: close\r\n\r\n" 
    print(dataR)
    if not urlData.port:
        newPort = 80
    else:
        newPort = urlData.port
    with  socket.socket(socket.AF_INET, socket.SOCK_STREAM) as origin:
        if(urlData.hostname==None or urlData.scheme!='http' or urlData.netloc==None or urlData.path==''):
            error = (f"HTTP/1.0 400 Bad Request\r\n")
            client_socket.sendall(error.encode())
            client_socket.close()
            origin.close()
            return 
        else:
            #Handle blocking 
            if(handle_blocking_req(urlData, client_socket, origin, newPort)):
                return
            origin.connect((urlData.hostname, newPort))
            #Handles caching if needed
            if(cacheEnabled and dataR in cache):
                splitHeader = cache[dataR].split(b"\r\n")
                for headerLine in splitHeader:
                    if(headerLine.count(b'Last-Modified:')):
                        lastModified = headerLine.decode()[15:]
                        break
                if(len(lastModified) > 0):
                    #updatedReq = dataR[: dataR.find('\r\n')] + "\r\nIf-Modified-Since: " + lastModified + dataR[dataR.find('\r\n'):]
                    updatedReq = f"GET {urlData.path} HTTP/1.0\r\nHost: {urlData.netloc}{extraHeader}\r\nIf-Modified-Since: {lastModified}\r\nConnection: close\r\n\r\n" 
                    origin.sendall(updatedReq.encode())
                originBytes = b""
                while True:
                    temp = origin.recv(4096)
                    originBytes += temp
                    if(temp==b""):
                        break 
                if(b'200 OK' in originBytes):
                    cache.update({updatedReq: originBytes})
                else :
                    client_socket.sendall(cache[dataR])
                    origin.close()
                    client_socket.close()
                    return
            #Sends request to server and recevies data back to send to the client
            origin.sendall(dataR.encode())
            originBytes = b""
            while True:
                temp = origin.recv(4096)
                originBytes += temp
                if(temp==b""):
                    break     
            if not originBytes:
                origin.close()
                client_socket.close()
                return
            while len(originBytes)==4096:
                originBytes += recievingData
            if(cacheEnabled):
                cache.update({dataR: originBytes})
            client_socket.sendall(originBytes)
            origin.close()
            client_socket.close()
    print('Client request handled')


# Set up signal handling (ctrl-c)
signal.signal(signal.SIGINT, ctrl_c_pressed)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:

    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    skt.bind((address, port))
    skt.listen()
    print(f"Listening on {(address, port)}")
    while True:
        clientSocket, addr = skt.accept()
        print(f"Connection on {addr} has been established")
        #sets up a thread for each client
        threading.Thread(target=handle_client, args=(clientSocket, addr)).start()
    