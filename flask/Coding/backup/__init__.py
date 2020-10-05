from flask import Flask, g, render_template, Markup, redirect, request, url_for, session, make_response, jsonify
import requests, json
import paramiko
import pymysql
import time

url = 'http://192.168.0.96:8080/client/api'
ubuntugcc='337d8f3c-0cf6-43f3-9908-bd831dd2d027'
ubuntupython='ae7b7ebc-8441-456f-afcc-c1956fb2fd48'
centosgcc='7825edab-7848-4203-9c30-e80651517faa'
centospython='9a298d9f-5c1f-49a7-972d-b307311ddfd8'

app = Flask(__name__)
# app.jinja_env.trim.blocks = True
status = 0
def getLoginStatus(username,password):
    login_data = {'command':'login', 'username':username, 'password': password, 'response':'json'}
    global user
    user = requests.Session()
    req = user.post(url, data=login_data)
    print(req.json())
    global status
    status = req.status_code
    return status
def logout():
    logout_data = {'command': 'logout'}
    global user
    req3 = user.post(url,data=logout_data)
    if(req3.status_code == 200):
        global status
        status = 0
        return redirect(url_for('mainDisplay'))
    else: return 'Something went wrong. Log out failed'
def adminLogin(username,password):
    login_data = {'command':'login', 'username':username, 'password': password, 'response':'json'}
    global admin
    admin = requests.Session()
    req = admin.post(url, data=login_data)
    print(req.json())

def CreateUser(email,firstname,lastname,password,username):
    createuser_data = {'command':'createUser','account':'admin','email':email,'firstname': firstname, 'lastname': lastname, 'username':username, 'password': password, 'response': 'json'}

    req1 = admin.post(url, data=createuser_data)
    global status
    status = req1.status_code
    return req1.status_code

def deploy(template):
    deploy_vm_data = {'command': 'deployVirtualMachine', 'serviceofferingid' : '6cef2eac-178d-4c6e-aee7-7172ef679894','templateid': template,'zoneid':'3f6a71a7-b5f8-4a10-aa2d-354b7b2bf7c5','response':'json'}
    global user
    req_dep_vm = user.post(url,data=deploy_vm_data)
    resp = req_dep_vm.json()
    res1 = resp['deployvirtualmachineresponse']
    res2 = res1 ['id']
    return res2

def getVMIp(vm_id):
    vm_data = {'command': 'listVirtualMachines', 'id' : vm_id,'response':'json'}
    global user
    req_vm = user.post(url,data=vm_data)
    resp = req_vm.json()
    res = resp['listvirtualmachinesresponse']
    res1 = res['virtualmachine']
    # print(res1[])
    res2 = res1[0]
    res3 = res2['nic']
    # print(res3)
    res4 = res3[0]
    res5 = res4['ipaddress']
    # print(res5)
    return res5

def expungeVm(vm_id):
    expunge_data = {'command': 'expungeVirtualMachine', 'id' : vm_id,'response':'json'}
    global user
    req_expunge_vm = user.post(url,data=expunge_data)
    return req_expunge_vm.status_code

class Ssh:
    Shell = None
    client = None
    transport = None
    ftp = None
    flag = False
    def __init__(self, address, username, password):
        print("Connecting to server on ip", str(address) + ".")
        self.client = paramiko.client.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        # self.client.connect(address, username=username, password=password)
        # self.transport = paramiko.Transport((address, 22))
        # self.transport.connect(username=username, password=password)
        # self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        try:
            self.client.connect(address, username=username, password=password)
            print("connect")
            self.transport = paramiko.Transport((address, 22))
            print("transport")
            self.transport.connect(username=username, password=password)
            print("trenasportconnect")
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)  
            print("sftp")
            self.flag = True
            print(self.flag)
        except Exception as e:
            self.flag = False

    def close_connection(self):
        try:
            self.client.close()
            self.sftp.close()
            self.transport.close()
        except Exception as e:
            print(str(e))

    def open_shell(self):
        try:
            self.Shell = self.client.invoke_shell()
        except Exception as e:
            print(str(e))

    def mv_dir(self, path):
        try:
            self.Shell.send("cd " + path + "\n")
        except Exception as e:
            print(str(e))

    def put_file(self, lpath, rpath, file_name):
        try:
            local_path = lpath + '/' + file_name
            remote_path = rpath + '/' + file_name
            self.sftp.put(remote_path, local_path)
        except Exception as e:
            print(str(e))

    def get_file(self, lpath, rpath, file_name):
        try:
            local_path = lpath + '/' + file_name
            remote_path = rpath + '/' + file_name
            self.sftp.get(remote_path, local_path)
        except Exception as e:
            print(str(e))

    def f_write(self, path, file_name, contents):
        try:
            ftp = self.sftp.open(path + '/' + file_name, "w")
            ftp.write(contents)
            ftp.flush()
            ftp.close()
        except Exception as e:
            print(str(e))

    def mkfile(self, path, file_name):
        try:
            self.Shell.send("cd " + path + '\n')
            self.Shell.send("touch " + file_name + "\n")
        except Exception as e:
            print(str(e))

    def chfname(self, path, oldname, newname):
        try:
            self.Shell.send("cd " + path + '\n')
            self.Shell.send("mv " + oldname + ' ' + newname + '\n')
        except Exception as e:
            print(str(e))

    def rmfile(self, path, file_name):
            try:
                self.Shell.send("cd " + path + '\n')
                self.Shell.send("rm -rf " + file_name + "\n")
            except Exception as e:
                print(str(e))
    def clear(self):
        try:
            self.Shell.send("clear"+"\n")
        except Exception as e:
            print(str(e))

    def show_code(self, path, file_name):
        try:
            ftp = self.sftp.open(path + '/' + file_name, 'r')
            result = ftp.read()
            print(result)
            ftp.flush()
            ftp.close()
        except Exception as e:
            print(str(e))

    def run_cfile(self, file_name):
        try:
            self.Shell.send("gcc " + file_name + " -o " + file_name + ".out\n")
            self.Shell.send("./" + file_name + ".out\n")
        except Exception as e:
            print(str(e))

    def run_pyfile(self, file_name):
        try:
            self.Shell.send("python " + file_name + "\n")
        except Exception as e:
            print(str(e))

    def send_command(self, command):
        try:
            self.Shell.send(command + '\n')
        except Exception as e:
            print(str(e))

    def print_result(self):
        try:
            output = self.Shell.recv(65535).decode("utf-8")
            return output
        except Exception as e:
            print(str(e))
sshUsername = "root"
sshPassword = "123456"
sshServer = ""
ubuntuser = "cloudstack"
ubuntupw = "123456"
centosuser = "root"
centospw = "whfdjqrhkwp"
# connection = Ssh(sshServer, sshUsername, sshPassword)
# connection.open_shell()
db = pymysql.connect(host='192.168.0.96', user='root', passwd='123456', db='user_info', charset='utf8')
cursor = db.cursor()

@app.route('/',methods = ['GET','POST'])
def mainDisplay():
    adminLogin('admin','123456')
    
    if (request.method == 'POST'):
        if ('register' in request.form):
            return redirect(url_for('registerPage'))
        elif ('login' in request.form):
            global username
            username = request.form['username']
            password= request.form['password']
            if(getLoginStatus(username,password)==200):
                return redirect(url_for('infoPage'))
        else: 
            return 'Something went wrong, please try again'
    return render_template('login.html')

@app.route('/register', methods = (['GET', 'POST']))
def registerPage():
    if request.method == 'POST': 
        email = request.form['email']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        password= request.form['password']
        if(CreateUser(email,firstname,lastname,password,username)==200 ):
            return redirect(url_for('infoPage'))
        else:
            return 'Something went wrong. Try to register again'
    return render_template('register.html')

@app.route('/aftercreate', methods = (['GET', 'POST']))
def aftercreate():
    os = request.form['os']
    language = request.form['language']
    template=''
    if os == 'centos' and language =='ccpp':
        template=centosgcc
    elif os == 'ubuntu' and language =='ccpp':
        template=ubuntugcc
    elif os == 'centos' and language =='python':
        template=centospython
    elif os == 'ubuntu' and language =='python':
        template=ubuntupython

    vmid=deploy(template)
    global username    
    u_id = username
    
    sql1 = '''
            INSERT INTO vm_info (user_id, os, lang, vm_id) VALUES (%s, %s, %s, %s)'''
    cursor.execute(sql1, (u_id, os, language, vmid))
    db.commit()
    
    return redirect(url_for('infoPage'))

@app.route('/info', methods = (['GET','POST']))
def infoPage():
    global username
    i = 0
    u_os = []
    u_lang = []
    u_vm = []
    u_vmid = []
    sql2 = '''
            SELECT user_id, os, lang, vm_ip, vm_id FROM vm_info where user_id = %s
        '''
    cursor.execute(sql2, username)
    result = cursor.fetchall()
    for tup in result:
        if tup[0] == username:
            u_os.insert(i, tup[1])
            u_lang.insert(i, tup[2])
            u_vm.insert(i,tup[3])
            u_vmid.insert(i,tup[4])
            i = i + 1
    #db.close()
    result_len = len(result)
    return render_template('info.html', u_id=username, os=u_os, language=u_lang, len=result_len, vm_ip = u_vm, vm_id=u_vmid)
@app.route('/getip', methods = (['GET','POST']))
def getip():
    vmid = request.form['vm_id']
    #global vm_ip
    vm_ip = getVMIp(vmid)
    sql = '''
                UPDATE vm_info SET vm_ip = %s WHERE vm_id = %s '''
    cursor.execute(sql, (vm_ip, vmid))
    db.commit()
    return jsonify(result = vm_ip)
@app.route('/create', methods = (['GET', 'POST']))
def createPage():
    if(request.method == 'POST'):
        if('logout' in request.form):
            return logout()
    if (status==200):
        return render_template('create.html')
    else: return 'Error. You are not logged in'

@app.route('/ttest')
def ttest():
    return render_template('ttest.html')

# @app.route('/ttest2', methods = ['GET', 'POST'])
# def ttest2():
#     if(request.method == 'POST'):
#         i = request.form['vm']
#         print(i)
#         return i
@app.route('/editor', methods = ['GET','POST'])
def editorPage():
    
    j=0
    global username
    u_id = username
    idlist=[]
    if ("delete" in request.form):
        idx=request.form['vm']
        sql = '''
                SELECT vm_id FROM vm_info where user_id = %s
            '''
        cursor.execute(sql, u_id)
        result3 = cursor.fetchall()
        for tup in result3:
            idlist.insert(j,tup[0])
            print(idlist[j])
            j = j + 1
        deleteid=idlist[int(idx)]
        sql1 = '''
                DELETE FROM vm_info WHERE vm_id = %s
            '''
        cursor.execute(sql1, deleteid)
        db.commit()

        expungeVm(deleteid)

        return redirect(url_for('infoPage'))
    elif ("start" in request.form):
        idx=request.form['vm']
        i=0
        global vlang
        global code_result
        global code

        u_os=[]
        u_vm =[]
        u_lang=[]
        flist=[]
        code_result = ''
        code = ''
        
        sql = '''
                SELECT os, lang, vm_ip FROM vm_info where user_id = %s
            '''
        cursor.execute(sql, u_id)
        result = cursor.fetchall()
        for tup in result:
            u_os.insert(i, tup[0])
            u_lang.insert(i,tup[1])
            u_vm.insert(i,tup[2])
            i = i + 1
        vip = u_vm[int(idx)]
        vos = u_os[int(idx)] 
        vlang = u_lang[int(idx)]
        if vos == 'ubuntu':
            user = ubuntuser
            pw = ubuntupw
            print("ubuntuos")
        elif vos == 'centos':
            user = centosuser
            pw = centospw  
            print("centosos")
            print(user,pw)
        global connection
        connection = Ssh(vip, user, pw)
        print(connection.flag)
        if connection.flag == False:
            return redirect(url_for('infoPage'))

        connection.open_shell()
        print("test")
        sql1 = '''
                SELECT fname FROM user_code where user_id = %s
            '''
        cursor.execute(sql1, u_id)
        result1 = cursor.fetchall()
        for tup in result1:
            flist.insert(j,tup[0])
            print(flist[j])
            j = j + 1
        flen=len(flist)
        if('logout' in request.form):
            return logout()
        if (status!=200):
            return 'Error. You are not logged in'
        else:
            return render_template('editor.html',uid=username, files=flist, flen=flen)
    elif("create" in request.form):
        return redirect(url_for('createPage'))


@app.route('/runcode', methods=['GET', 'POST'])
def runcode():
    global code_result
    global code
    code_result = ''
    code=''
    fname = request.form['filename']
    print(fname)
    code = request.form['code']
    print(code)
    connection.f_write('/home', fname, code)
    if vlang=='ccpp':
        print(vlang)
        connection.rmfile('/home',fname+'.out')
        connection.print_result()
        connection.run_cfile(fname)
        time.sleep(1)
        code_result = connection.print_result()
    elif vlang =='python':
        print(vlang)
        connection.print_result()
        connection.run_pyfile(fname)
        time.sleep(1)
        code_result = connection.print_result()
    # connection.close_connection()
    sql = '''
            UPDATE user_code SET code = %s WHERE fname = %s '''
    cursor.execute(sql, (code, fname))
    db.commit()
    return jsonify(result = code_result)

@app.route('/showcode', methods=['GET', 'POST'])
def showcode():
    fname = request.form['filename']
    sql = '''
            SELECT code FROM user_code WHERE fname = %s '''
    cursor.execute(sql, fname)
    result = cursor.fetchall()
    return jsonify(result = result)

@app.route('/addfile', methods=['GET', 'POST'])
def addfile():
    global username
    global connection
    uid = username
    flist=[]
    j=0
    fname = request.form['filename']

    sql2 = '''
            SELECT fname FROM user_code WHERE user_id = %s '''
    cursor.execute(sql2,username)
    result=cursor.fetchall()
    for tup in result:
        flist.insert(j,tup[0])
        j = j + 1
    if fname in flist:
        canCreate = 0
    else:
        canCreate = 1
        sql = '''
                        INSERT INTO user_code (fname, user_id) VALUES (%s, %s)'''
        cursor.execute(sql, (fname, uid))
        db.commit()
        connection.mkfile('/home', fname)
        connection.print_result()
    return jsonify(canCreate = canCreate)

@app.route('/renamefile', methods=['GET', 'POST'])
def renamefile():
    global username
    uid = username
    fname = request.form['filename']
    newname = request.form['newname']
    j=0
    flist=[]
    sql2 = '''
                SELECT fname FROM user_code WHERE user_id = %s '''
    cursor.execute(sql2,username)
    result=cursor.fetchall()
    for tup in result:
        flist.insert(j,tup[0])
        j = j + 1
    if newname in flist:
        canCreate = 0
    else:
        canCreate = 1
        sql = '''
                        UPDATE user_code SET fname = %s WHERE fname = %s '''
        cursor.execute(sql, (newname, fname))
        db.commit()
        connection.chfname('/home', fname, newname)
        connection.print_result()
    return jsonify(canCreate = canCreate)

@app.route('/removefile', methods=['GET', 'POST'])
def removefile():
    global username
    uid = username
    fname = request.form['filename']
    sql = '''
                    DELETE FROM user_code WHERE fname = %s   '''
    cursor.execute(sql, fname)
    db.commit()
    connection.rmfile('/home', fname)
    connection.print_result()
    return jsonify()

if(__name__)=='__main__':
    app.run(debug=True)
# @app.before_request

# def before_request():
#     print("before_request")
#     g.str = "한글"

# @app.route("/tmpl")
# def t():
#     tit = Markup("<strong>Title<strong>")
#     mu = Markup("<h1>iii = <i>%s</i></h1>")
#     h = mu % "Italic"
#     print("h=", h)
#     return render_template('index.html', title = tit, mu = h)

# @app.route("/")
# def helloworld():
#     return "Hello Flask World!"

# @app.route("/gg")
# def helloworld2():
#     return "Hello Flask World!" + getattr(g, 'str', '111')


