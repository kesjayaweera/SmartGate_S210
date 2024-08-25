import cv2
import http.server
import socketserver
import io as python_io
from PIL import Image
import threading

#
# HTTP Server Handler. 
#

#Global variable to store the latest frame
latest_frame = None

#This class is to create a multi-threaded server that can handle multiple client requests concurrently
class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads      = True

class HTTPHandler(http.server.BaseHTTPRequestHandler):
    #On GET request
    def do_GET(self):
        #--- Main page request. ---
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            #self.wfile.write(b'<html><body><img src="/stream" width="600" height="400"></body></html>')
            self.wfile.write(Read_Web_Page('../web/index.html'))
        
        #--- Camera stream request. ---
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()

            try:
                while True:
                    if latest_frame is not None:
                        _, jpeg = cv2.imencode('.jpg', latest_frame)
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', len(jpeg))
                        self.end_headers()
                        self.wfile.write(jpeg.tobytes())
                        self.wfile.write(b'\r\n')

            except Exception as e:
                print(f"[-] Streaming error: {str(e)}")

#Set the frame to be passed to web server
def set_latest_frame(frame):
    global latest_frame
    latest_frame = frame

#Read HTML web page from file
def Read_Web_Page(html_path):
    try:
        with open(html_path, 'rb') as file:
            return file.read()
    except:
        return b"Error: File path could not be found"

#Initialize and run server listener
def Initialize_Server(port=8000):
    #with socketserver.TCPServer(("", port), HTTPHandler) as httpd:
    #    print('[+] Running server under port {port}')
    #    httpd.serve_forever()

    server = ThreadedHTTPServer(("", port), HTTPHandler)
    print(f'[+] Running server under port {port}')
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server

def Shutdown_Server(server):
    print("[+] Shutting down the server...")
    server.shutdown()
    server.server_close()