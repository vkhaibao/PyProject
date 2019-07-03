from werkzeug.utils import secure_filename
from jinja2 import Environment,FileSystemLoader
from flask import Flask,Blueprint,render_template,jsonify,request
import time
import os
import base64
 
env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
upload = Blueprint('upload',__name__)

UPLOAD_FOLDER='/usr/etc'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = set(['txt','png','jpg','xls','JPG','PNG','xlsx','gif','GIF','pdf'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS
  
@upload.route('/upload',methods=['POST','GET'],strict_slashes=False)
def upload():
    global re
    file_dir=os.path.join(basedir,app.config['UPLOAD_FOLDER'])
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    f=request.files['file_change']
    if f and allowed_file(f.filename):
        fname=secure_filename(f.filename)
        ext = fname.rsplit('.',1)[1]
        unix_time = int(time.time())
        new_filename=str(unix_time)+'.'+ext
        f.save(os.path.join(file_dir,new_filename))
                
        return "{\"Result\":true}" 
    else:
        return "{\"Result\":false}" 

