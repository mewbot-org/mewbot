import http.server, cgi, pathlib

upload_page = bytes('''<!DOCTYPE html>
<html>
<head>
<title>File Upload</title>
<meta name="viewport" content="width=device-width, user-scalable=no" />
<style type="text/css">
body{
  background: rgba(0,0,0,0.9);
}
form{
  position: absolute;
  top: 50%;
  left: 50%;
  margin-top: -100px;
  margin-left: -250px;
  width: 500px;
  height: 200px;
  border: 4px dashed #fff;
}
form p{
  width: 100%;
  height: 100%;
  text-align: center;
  line-height: 170px;
  color: #ffffff;
  font-family: Arial;
}
form input{
  position: absolute;
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  outline: none;
  opacity: 0;
}
form button{
  margin: 0;
  color: #fff;
  background: #16a085;
  border: none;
  width: 508px;
  height: 35px;
  margin-top: -20px;
  margin-left: -4px;
  border-radius: 4px;
  border-bottom: 4px solid #117A60;
  transition: all .2s ease;
  outline: none;
}
form button:hover{
  background: #149174;
	color: #0C5645;
}
form button:active{
  border:0;
}
</style>
</head>
<body>
<h1>File Upload</h1>
<form action="upload" method="POST" enctype="multipart/form-data">
<input name="file_1" type="file" />
<br />
<p>Drag your files here or click in this area. Naming scheme MUST be followed for images. dex#+form#-.png</p>
<br />
<button type="submit">Upload</button>
<input type="submit" />
</form>
</body>
</html>''', 'utf-8')

def send_upload_page(handler):
    handler.send_response(http.HTTPStatus.OK)
    handler.send_header("Content-Type", 'text/html; charset=utf-8')
    handler.send_header("Content-Length", len(upload_page))
    handler.end_headers()
    handler.wfile.write(upload_page)

def receive_upload(handler):
    form = cgi.FieldStorage(fp=handler.rfile, headers=handler.headers, environ={'REQUEST_METHOD': 'POST'})
    
    if 'file_1' in form and form['file_1'].file and form['file_1'].filename:
        with open(pathlib.Path.cwd() / pathlib.Path(form['file_1'].filename).name, 'wb') as f:
            f.write(form['file_1'].file.read())

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/upload': send_upload_page(self)
        else: http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/upload':
            receive_upload(self)
            send_upload_page(self)
        else: self.send_error(http.HTTPStatus.NOT_FOUND, "Can only POST to /upload")

class CGIHTTPRequestHandler(http.server.CGIHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/upload': send_upload_page(self)
        else: http.server.CGIHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/upload':
            receive_upload(self)
            send_upload_page(self)
        else: http.server.CGIHTTPRequestHandler.do_POST(self)
