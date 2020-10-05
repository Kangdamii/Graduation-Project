from flask import Flask, g, render_template, Markup, redirect, request, url_for, session, make_response, jsonify
import requests, json
import paramiko
import pymysql
import time

url = 'http://192.168.0.96:8080/client/api'
ubuntugcc='f6ab5f55-2f54-41f9-a343-0f1ed22ba308'
ubuntupython='ffa7d3b6-6885-468b-9dab-0e94f400666a'
centosgcc='d2426789-2fe2-4ea0-afc8-83b16d9cf918'
centospython='0054f6ab-157d-44a0-8e7f-a4b8ef7c4f79'

smallcpu = '0aeff6df-3258-4183-a171-5b6fcecedbfc'
mediumcpu = '1e36dd0e-3ce8-40ff-969a-6b2edb2cefa4'

smalldisk = 'd197ee8b-6160-444e-84c1-abe5d22a67a8'
mediumdisk = '63bbeacd-3feb-45a9-ab14-106922d17df1'
largedisk = '20d988da-06cc-4c73-9c25-a6d7ac3bda42'

username = ''
loginflag=0
app = Flask(__name__)
# app.jinja_env.trim.blocks = True
status = 0
def getLoginStatus(username,password):
    login_data = {'command':'login', 'username':username, 'password': password, 'response':'json'}
    global user
    user = requests.Session()
    req = user.post(url, data=login_data)
    global status
    status = req.status_code
    global loginflag
    loginflag = 1
    return status
def logout():
    logout_data = {'command': 'logout'}
    global user
    global username
    req3 = user.post(url,data=logout_data)
    username = ''
    if(req3.status_code == 200):
        global status
        global loginflag
        status = 0
        loginflag = 0
        return redirect(url_for('mainDisplay', loginflag = loginflag))
    else: return 'Something went wrong. Log out failed'
def adminLogin(username,password):
    login_data = {'command':'login', 'username':username, 'password': password, 'response':'json'}
    global admin
    admin = requests.Session()
    req = admin.post(url, data=login_data)

def CreateUser(email,firstname,lastname,password,username):
    createuser_data = {'command':'createUser','account':'admin','email':email,'firstname': firstname, 'lastname': lastname, 'username':username, 'password': password, 'response': 'json'}

    req1 = admin.post(url, data=createuser_data)
    
    global status
    status = req1.status_code
    if(status == 200):
        return getLoginStatus(username,password)
    return req1.status_code

def deploy(template,diskid,cpu,vmname):
    deploy_vm_data = {'command': 'deployVirtualMachine', 'serviceofferingid' : cpu,'templateid': template, 'displayname': vmname,'zoneid':'38eae299-4ffc-41cc-b509-293e13cae010', ' diskofferingid':diskid,'response':'json'}
    global user
    req_dep_vm = user.post(url,data=deploy_vm_data)
    resp = req_dep_vm.json()
    res1 = resp['deployvirtualmachineresponse']
    res2 = res1 ['id']
    return res2

def getVMIp(vm_id):
    vm_data = {'command': 'listVirtualMachines', 'id' : vm_id,'response':'json'}
    global user
    res5 = 'none'
    req_vm = user.post(url,data=vm_data)
    resp = req_vm.json()
    res = resp['listvirtualmachinesresponse']
    res1 = res['virtualmachine']
    res2 = res1[0]
    state = res2['state']
    # print(state)
    if state == "Running":
        res3 = res2['nic']
        res4 = res3[0]
        res5 = res4['ipaddress']
    print("res5", res5)
    return res5

def expungeVm(vm_id):
    expunge_data = {'command': 'destroyVirtualMachine', 'id' : vm_id, 'expunge':'true', 'response':'json'}
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
            self.transport = paramiko.Transport((address, 22))
            self.transport.connect(username=username, password=password)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)  
            self.flag = True
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

    def show_code(self, path, file_name):
        try:
            ftp = self.sftp.open(path + '/' + file_name, 'r')
            result = ftp.read()
            ftp.flush()
            ftp.close()
        except Exception as e:
            print(str(e))

    def run_cfile(self, file_name):
        try:
            self.Shell.send("gcc " + file_name + " -o " + file_name + ".out\n")
            time.sleep(0.1)
            self.Shell.recv(65535).decode("utf-8")
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
sshServer = ""
ubuntuser = "root"
ubuntupw = "123456"
centosuser = "root"
centospw = "123456"
# connection = Ssh(sshServer, sshUsername, sshPassword)
# connection.open_shell()
db = pymysql.connect(host='192.168.0.96', user='root', passwd='', db='user_info', charset='utf8')
cursor = db.cursor()

@app.route('/',methods = ['GET','POST'])
def mainDisplay():
    adminLogin('admin','123456')
    global username
    global loginflag
    if request.method == 'POST':
        username = request.form['username']
        password= request.form['password']
        getLoginStatus(username,password)
    # elif('logout' in request.form):
    #     return logout()
    if(status == 0):
        return render_template('login.html', loginflag = loginflag)
    elif(status == 200):
        return redirect(url_for('afterlogin', loginflag=loginflag))

@app.route('/logout', methods=['GET', 'POST'])
def logoutPage():
    logout()
    global loginflag
    return redirect(url_for('mainDisplay', loginflag = loginflag))

@app.route('/afterlogin', methods=['GET', 'POST'])
def afterlogin(): 
    global password
    global fromid
    global teamid
    global invitelen
    global loginflag
    global username
    i = 0
    
    fromid=[]
    teamid=[]
    
    sql = '''
                SELECT from_id, team_id FROM invite where to_id = %s
        '''
    cursor.execute(sql, username)
    result = cursor.fetchall()
    for tup in result:
        fromid.insert(i, tup[0])
        teamid.insert(i, tup[1])
        i = i + 1
    invitelen=len(result)
    return render_template('afterlogin.html', username = username, fromid=fromid, teamid=teamid, invitelen=invitelen, loginflag = loginflag)


@app.route('/acceptinvite', methods = (['GET', 'POST']) )
def acceptinvite():
    i = 0
    idx=request.form['idx']
    global teamid
    global username
    acceptteam=teamid[int(idx)]
    userteamid=[]

    sql = '''
        DELETE FROM invite WHERE team_id = %s'''
    cursor.execute(sql, acceptteam)
    db.commit()
    
    sql2 = '''
        INSERT INTO team_users (user_id, team_id) VALUES (%s, %s)'''
    cursor.execute(sql2, (username, acceptteam))
    db.commit()

    sql3 = '''
                 SELECT team_id FROM team_users where user_id = %s
         '''
    cursor.execute(sql3, username)
    result = cursor.fetchall()
    for tup in result:
        userteamid.insert(i, tup[0])
        i = i + 1
    teamlen=len(result)
    return jsonify()

@app.route('/rejectinvite', methods = (['GET', 'POST']) )
def rejectinvite():
    idx=request.form['idx']
    global teamid
    rejectteam=teamid[int(idx)]
    sql = '''
        DELETE FROM invite WHERE team_id = %s'''
    cursor.execute(sql, rejectteam)
    db.commit()
    return jsonify()

@app.route('/register', methods = (['GET', 'POST']))
def registerPage():
    global username
    global loginflag
    if request.method == 'POST': 
        email = request.form['email']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        password= request.form['password']
        if(CreateUser(email,firstname,lastname,password,username)==200 ):
            loginflag = 1
            # return render_template('afterlogin.html', username = username, loginflag = loginflag)
            return redirect(url_for('afterlogin'))
        else:
            return 'Something went wrong. Try to register again'
    return render_template('register.html', loginflag = loginflag)

@app.route('/aftercreate', methods = (['GET', 'POST']))
def aftercreate():
    disk = request.form['disk']
    cpu = request.form['cpu']
    os = request.form['os']
    language = request.form['language']
    vmname = request.form['vmname']
    diskid=''
    cpuid=''
    template=''

    if disk =='small':
        diskid = smalldisk
    elif disk =='medium':
        diskid = mediumdisk
    elif disk == 'large':
        diskid = largedisk

    if cpu =='small':
        cpuid = smallcpu
    elif cpu=='medium':
        cpuid = mediumcpu

    if os == 'centos' and language =='ccpp':
        template=centosgcc
    elif os == 'ubuntu' and language =='ccpp':
        template=ubuntugcc
    elif os == 'centos' and language =='python':
        template=centospython
    elif os == 'ubuntu' and language =='python':
        template=ubuntupython

    vmid=deploy(template,diskid,cpuid, vmname)
    global username    
    u_id = username
    
    sql1 = '''
            INSERT INTO vm_info (name, user_id, os, lang, vm_id, vm_disk, vm_cpu) VALUES (%s, %s, %s, %s, %s, %s, %s)'''
    cursor.execute(sql1, (vmname, u_id, os, language, vmid, disk, cpu))
    db.commit()
    
    return redirect(url_for('infoPage', loginflag = loginflag, username = u_id))

@app.route('/info', methods = (['GET','POST']))
def infoPage():
    # if('logout' in request.form):
    #     return logout()
    # elif (status!=200):
    #     return 'Error. You are not logged in'
    global username
    i = 0
    u_name=[]
    u_os = []
    u_lang = []
    u_vmid = []
    u_vmcpu= []
    u_vmdisk = []

    sql2 = '''
            SELECT user_id, name, os, lang, vm_id, vm_cpu, vm_disk FROM vm_info where user_id = %s
        '''
    cursor.execute(sql2, username)
    result = cursor.fetchall()
    for tup in result:
        if tup[0] == username:
            u_name.insert(i,tup[1])
            u_os.insert(i, tup[2])
            u_lang.insert(i, tup[3])
            u_vmid.insert(i,tup[4])
            u_vmcpu.insert(i,tup[5])
            u_vmdisk.insert(i,tup[6])
            i = i + 1
    #db.close()
    print(result)
    result_len = len(result)
    return render_template('info.html', u_id=username, name=u_name, os=u_os, language=u_lang, len=result_len, vm_id=u_vmid, cpu = u_vmcpu, disk=u_vmdisk, loginflag = loginflag, username = username)

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
    global username
    if(request.method == 'POST'):
        if('logout' in request.form):
            return logout()
    if (status==200):
        return render_template('create.html', loginflag = loginflag, username = username)
    else: return 'Error. You are not logged in'

@app.route('/teamlist', methods = (['GET', 'POST']))
def teamlist():
    i = 0
    global username
    teamlist=[]
    descriptionlist=[]
    memberlist=[]
    masterlist=[]
    sql1 = '''
                SELECT ti.team_id, description, master FROM team_info ti, team_users tu where tu.user_id = %s and ti.team_id=tu.team_id      
            '''                                                                
    cursor.execute(sql1, username)
    result1 = cursor.fetchall()
    for tup in result1:
        teamlist.insert(i,tup[0])
        descriptionlist.insert(i,tup[1])
        masterlist.insert(i,tup[2])
        i = i + 1
    teamlen=len(result1)
    
    i = 0
    sql2 = ''' SELECT team_id, count(tu.user_id) as member FROM team_users tu GROUP BY team_id '''
    cursor.execute(sql2)
    result2 = cursor.fetchall()
    
    for tup in result2:
        for t in teamlist: 
            idx = teamlist.index(t)
            if tup[0] == t:
                memberlist.insert(idx,tup[1])
                i = i + 1 
    return render_template('teamlist.html', teamlist=teamlist, descriptionlist=descriptionlist, masterlist=masterlist, memberlist=memberlist, teamlen=teamlen, loginflag = loginflag, username = username)

@app.route('/team', methods = (['GET', 'POST']))
def teamPage():
    global username
    if request.method == "POST":
        uteamid = request.form['teamName[]']
    else:
        uteamid = request.args.get('teamName')
    desc = ''
    masterid = ''
    userlist = []
    postsubjectlist = []
    postcontentslist = []
    postwriterlist = []
    vmname = []
    vmid = []
    vmos = []
    vmlang = []
    vmdisk = []
    vmcpu = []

    i=0
    sql1 = '''
                SELECT user_id FROM team_users where team_id = %s       
            '''                  
    print(uteamid)                                                      #select user id in team
    cursor.execute(sql1, uteamid)
    result1 = cursor.fetchall()
    for tup in result1:
        userlist.insert(i,tup[0])
        i = i + 1
    ulen=len(result1)

    i = 0
    sql2 = '''
                    SELECT subject,contents,writer FROM post where team_id = %s
                '''                                                         #select post in team
    cursor.execute(sql2, uteamid)
    result2 = cursor.fetchall()
    plen=len(result2)
    for tup in result2:
        postsubjectlist.insert(i, tup[0])
        postcontentslist.insert(i, tup[1])
        postwriterlist.insert(i, tup[2])
        i = i + 1
    i = 0

    sql3 = '''
                    SELECT name,vm_id, os, lang, vm_disk, vm_cpu FROM teamvminfo where team_id = %s
                '''                                                          #select team's vm information 
    cursor.execute(sql3, uteamid)
    result3 = cursor.fetchall()
    for tup in result3:
        vmname.insert(i,tup[0])
        vmid.insert(i,tup[1])
        vmos.insert(i,tup[2])
        vmlang.insert(i,tup[3])
        vmdisk.insert(i,tup[4])
        vmcpu.insert(i,tup[5])
        i = i + 1
    vlen=len(result3)

    i = 0
    sql4 = '''
                    SELECT description FROM team_info where team_id = %s
                '''                                                          #select team's vm information 
    cursor.execute(sql4, uteamid)
    result4 = cursor.fetchall()
    for tup in result4:
        desc = tup[0]

    sql5 = '''
                    SELECT master FROM team_info where team_id = %s
                '''                                                          #select master
    cursor.execute(sql5, uteamid)
    result5 = cursor.fetchall()
    for tup in result5:
        masterid = tup[0]
    print(vmid)
    return render_template('team.html',masterid=masterid, userlist=userlist,ulen=ulen,subjectlist=postsubjectlist,contentslist=postcontentslist, writerlist=postwriterlist, plen=plen,vmname=vmname,vmid=vmid,vmos=vmos,vmlang=vmlang,vmdisk=vmdisk,vmcpu=vmcpu,vlen=vlen,teamname = uteamid, desc=desc, loginflag = loginflag, username = username)

@app.route('/addteam', methods=['GET','POST'])       #add teamid,description,master to team_info db
def addteam():
    global username
    teamname=request.form['teamName']
    teamdescription=request.form['teamDescription']
    sql = '''
            INSERT INTO team_users (user_id, team_id) VALUES (%s, %s)
        '''
    cursor.execute(sql, (username, teamname))  
    db.commit()   
    sql2 = '''
            INSERT INTO team_info (team_id, description, master) VALUES (%s, %s, %s)
        '''
    cursor.execute(sql2, (teamname, teamdescription, username))  
    db.commit()  
    # return jsonify()
    return redirect(url_for('teamlist'))

@app.route('/deleteteam', methods=['GET','POST'])       #delete teamid,description,master to team_info db
def deleteteam():
    global username
    teamname=request.form['teamName']
    sql = '''
            SELECT master FROM team_info where team_id = %s         
        '''
    cursor.execute(sql,teamname)                            #if username == master
    result = cursor.fetchall()
    for tup in result:
        master = tup[0]

    if master == username:
        sql2 = '''  
                DELETE FROM team_info WHERE team_id = %s        
            '''
        cursor.execute(sql2, teamname)                          #delete from user_info db
        db.commit()                         
        sql3 = '''
                DELETE FROM team_users WHERE team_id = %s       
            '''
        cursor.execute(sql3, teamname)                          #delete from team_users db
        db.commit()
        sql3 = '''
                DELETE FROM teamvminfo WHERE team_id = %s
            '''
        cursor.execute(sql3, teamname)                              #delete all team vm
        db.commit()    
    return jsonify()


@app.route('/addpost', methods=['GET','POST'])        #add post to db('post' table)
def addpost():
    global username
    teamName = request.form['teamName']
    subject = request.form['subject']
    context = request.form['context']
    writer = request.form['writer']
    sql = '''
            INSERT INTO post (contents, subject, team_id, writer) VALUES (%s, %s, %s, %s)
        '''
    cursor.execute(sql, (context, subject , teamName, writer))  
    db.commit()     
    return jsonify()

@app.route('/deletepost', methods=['GET', 'POST'])
def deletepost():
    global username
    idx = request.form['dIDX']
    teamName = request.form['teamName']
    postsubjectlist = []
    contentslist = []
    writerlist = []
    writer = ''
    i = 0
    sql1 = '''
            SELECT subject, contents, writer FROM post where team_id = %s
            '''                                                         
    cursor.execute(sql1, teamName)
    result1 = cursor.fetchall()
    for tup in result1:
        postsubjectlist.insert(i, tup[0])
        contentslist.insert(i,tup[1])
        writerlist.insert(i, tup[2])
        i = i + 1
    subject = postsubjectlist[int(idx)]
    contents = contentslist[int(idx)]
    writer = writerlist[int(idx)]    

    if writer == username:
        sql2 = '''  
                    DELETE FROM post WHERE subject = %s and contents = %s and writer = %s     
                '''
        cursor.execute(sql2, (subject,contents,writer))                         
        db.commit()  
        return jsonify(result = subject)

@app.route('/invite', methods=['GET','POST'])            #add user to db('team users'table)
def invite():
    global username
    print("invite")
    # to_id = request.args.get('userID')
    # teamName = request.args.get('teamName')
    to_id = request.form['userID']
    teamName = request.form['teamName']
    sql1 = '''
            INSERT INTO invite (from_id, to_id, team_id) VALUES (%s, %s, %s)
            '''
    cursor.execute(sql1, (username, to_id, teamName))
    db.commit() 
    return jsonify() 

@app.route('/deleteUser',methods=['GET','POST'])        #delete user in team
def deleteUser():
    teamUser = request.form['teamUser']
    teamName = request.form['teamName']
    print(teamUser)
    print(teamName)
    master = ''
    sql = '''
            SELECT master FROM team_info where team_id = %s         
        '''
    cursor.execute(sql,teamName)                            
    result = cursor.fetchall()
    for tup in result:
        master = tup[0]

    if master == username:
        sql2 = '''  
                DELETE FROM team_users WHERE user_id = %s        
            '''
        cursor.execute(sql2, teamUser)                          
        db.commit()                         
        return jsonify()


@app.route('/teamvmcreate', methods=['GET', 'POST'])
def teamvmcreate():
    global username
    team_name = request.form['teamName']
    return render_template('teamvmcreate.html', team_name = team_name, loginflag = loginflag, username = username)

@app.route('/teamvmDelete', methods=['GET', 'POST'])        #delete vm by ajax
def teamvmDelete():
    global username
    vmID = request.form['vmID']
    sql = '''
            select ti.master from team_info ti, teamvminfo tvi where tvi.vm_id = %s and tvi.team_id =ti.team_id
        '''
    cursor.execute(sql,vmID) 
    result = cursor.fetchall()
    for tup in result:
        master = tup[0]
    print(master)
    print(username)
    if master == username:
        sql2 = '''
                DELETE FROM teamvminfo WHERE vm_id = %s
            '''
        cursor.execute(sql2, vmID)  
        db.commit()
        expungeVm(vmID)
    return jsonify()


@app.route('/afterteamvmcreate', methods=['GET','POST'])          #add vm information to db(teavminfo table)
def afterteamcreate():
    global username
    uteamid=request.form['teamName']
    cpu = request.form['cpu']
    disk = request.form['disk']
    os = request.form['os']
    language = request.form['language']
    name = request.form['vmname']
    template = ''
    diskid = ''
    cpuid = ''

    if disk =='small':
        diskid = smalldisk
    elif disk =='medium':
        diskid = mediumdisk
    elif disk == 'large':
        diskid = largedisk

    if cpu =='small':
        cpuid = smallcpu
    elif cpu=='medium':
        cpuid = mediumcpu

    if os == 'centos' and language =='ccpp':
        template=centosgcc
    elif os == 'ubuntu' and language =='ccpp':
        template=ubuntugcc
    elif os == 'centos' and language =='python':
        template=centospython
    elif os == 'ubuntu' and language =='python':
        template=ubuntupython

    vmid=deploy(template,diskid,cpuid, name) 
    sql1 = '''
            INSERT INTO teamvminfo (team_id, vm_id, os, lang, vm_disk, vm_cpu, name) VALUES (%s, %s, %s, %s, %s, %s, %s)'''
    cursor.execute(sql1, (uteamid, vmid, os, language, disk, cpu, name))
    db.commit()         
    # if request.method == 'POST':
    return redirect(url_for("teamPage", teamName = uteamid, loginflag = loginflag, username = username))


@app.route('/editor', methods = ['GET','POST'])
def editorPage():
    j = 0
    global username
    global vlang
    global vos
    global code_result
    global code
    global vip
    global connection
    # if (username =='' or username == None):
    #     return "You are not logged in"
    u_id = username
    idlist=[]
    if("create" in request.form):
        return redirect(url_for('createPage', loginflag = loginflag, username = username))
    elif ("delete" in request.form):
        vmid=request.form['vm[]']
        sql1 = '''
                DELETE FROM vm_info WHERE vm_id = %s
            '''
        cursor.execute(sql1, vmid)
        db.commit()
        expungeVm(vmid)
        return redirect(url_for('infoPage', loginflag = loginflag, username = username))
    elif ("deleteteamvm" in request.form):
        teamname = request.form['teamname']
        vmID = request.form['vm[]']
        sql = '''
                select ti.master from team_info ti, teamvminfo tvi where tvi.vm_id = %s and tvi.team_id =ti.team_id
            '''
        cursor.execute(sql,vmID) 
        result = cursor.fetchall()
        for tup in result:
            master = tup[0]
        print(master)
        print(username)
        if master == username:
            sql2 = '''
                    DELETE FROM teamvminfo WHERE vm_id = %s
                '''
            cursor.execute(sql2, vmID)  
            db.commit()
            expungeVm(vmID)
        return redirect(url_for('teamPage',teamName=teamname, loginflag = loginflag, username = username))
    
    else:
        global vlang
        u_lang = ''
        u_os= ''
        u_ip='none'
        user=''
        pw= ''
        u_id = username
        code_result = ''
        code = ''
        flist = []
        vminfo = request.form['info']
        if vminfo == 'private': 
            vmid=request.form['vm[]']

            sql = '''
                    SELECT os, lang, vm_ip FROM vm_info where vm_id = %s
                '''
            cursor.execute(sql, vmid)
            result = cursor.fetchall()
            for tup in result:
                u_os = tup[0]
                u_lang = tup[1]
                u_ip = tup[2]
            vlang = u_lang
            vos=u_os
            if u_os == 'ubuntu':
                user = ubuntuser
                pw = ubuntupw
            elif u_os == 'centos':
                user = centosuser
                pw = centospw 
    
            if u_ip == 'none' or u_ip == None:
                # while True:
                u_ip = getVMIp(vmid)
                if u_ip == 'none':
                    time.sleep(3)
                    return render_template('loading.html',vmid=vmid,vminfo=vminfo)
                        # break
                sql = '''
                            UPDATE vm_info SET vm_ip = %s WHERE vm_id = %s '''
                cursor.execute(sql, (u_ip, vmid))
                db.commit()
            vip = u_ip

            # global connection
            connection = Ssh(u_ip, user, pw)
            # time.sleep(3)
            if connection.flag == False:
                time.sleep(2.5)
                return render_template('loading.html',vmid=vmid,vminfo=vminfo)

            connection.open_shell()
            sql1 = '''
                    SELECT fname FROM user_code where user_id = %s and vm_ip = %s
                '''
            cursor.execute(sql1,(u_id, u_ip))
            result1 = cursor.fetchall()
            for tup in result1:
                flist.insert(j,tup[0])
                j = j + 1
            flen=len(flist)
            return render_template('editor.html',uid=username, flist=flist, flen=flen, loginflag = loginflag, username = username)
        elif vminfo == "public":
            print("enter test")
            vmid=request.form['vm[]']

            sql = '''
                    SELECT os, lang, vm_ip FROM teamvminfo where vm_id = %s
                '''
            cursor.execute(sql, vmid)
            result = cursor.fetchall()
            for tup in result:
                u_os = tup[0]
                u_lang = tup[1]
                u_ip = tup[2]
            vlang = u_lang
            vos=u_os
            if u_os == 'ubuntu':
                user = ubuntuser
                pw = ubuntupw
            elif u_os == 'centos':
                user = centosuser
                pw = centospw 
    
            if u_ip == 'none' or u_ip == None:
                # while True:
                u_ip = getVMIp(vmid)
                if u_ip == 'none':
                    time.sleep(3)
                    return render_template('loading.html',vmid=vmid,vminfo=vminfo)
                        # break
                sql = '''
                            UPDATE teamvminfo SET vm_ip = %s WHERE vm_id = %s '''
                cursor.execute(sql, (u_ip, vmid))
                db.commit()
            vip = u_ip

            # global connection
            connection = Ssh(u_ip, user, pw)
            # time.sleep(3)
            if connection.flag == False:
                time.sleep(2.5)
                return render_template('loading.html',vmid=vmid,vminfo=vminfo)

            connection.open_shell()
            sql1 = '''
                    SELECT fname FROM user_code where vm_ip = %s
                '''
            cursor.execute(sql1, u_ip)
            result1 = cursor.fetchall()
            for tup in result1:
                flist.insert(j,tup[0])
                j = j + 1
            flen=len(flist)
            return render_template('editor.html',uid=username, flist=flist, flen=flen, loginflag = loginflag, username = username)
        
@app.route('/loading', methods=['GET', 'POST'])
def loading():
    # vmid = request.args.get('vmid')
    return render_template('loading.html')

@app.route('/runcode', methods=['GET', 'POST'])
def runcode():
    global code_result
    global code
    global connection
    code_result = ''
    code=''
    fname = request.form['filename']
    code = request.form['code']
    connection.f_write('/home', fname, code)
    connection.send_command('cd /home')
    if vlang=='ccpp':
        connection.rmfile('/home',fname+'.out')
        connection.run_cfile(fname) 
        time.sleep(1)
        code_result = connection.print_result()
    elif vlang =='python':
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

@app.route('/sendCommand', methods=['GET', 'POST'])
def sendComand():
    command = request.form['command']
    connection.send_command(command)
    time.sleep(0.1)
    result = connection.print_result()
    return jsonify(result=result)


@app.route('/showcode', methods=['GET', 'POST'])
def showcode():
    fname = request.form['filename']
    sql = '''
            SELECT code FROM user_code WHERE fname = %s '''
    cursor.execute(sql, fname)
    result = cursor.fetchall()
    return jsonify(result = result)

@app.route('/addfile', methods =['GET', 'POST'])
def addfile():
    global username
    global connection
    global vip
    uid = username
    flist=[]
    j=0
    fname = request.form['filename']

    sql2 = '''
            SELECT fname FROM user_code WHERE user_id = %s and vm_ip = %s'''
    cursor.execute(sql2,(username,vip))
    result=cursor.fetchall()
    for tup in result:
        flist.insert(j,tup[0])
        j = j + 1
    if fname in flist:
        canCreate = 0
    else:
        canCreate = 1
        sql = '''
                        INSERT INTO user_code (fname, user_id, vm_ip) VALUES (%s, %s, %s)'''
        cursor.execute(sql, (fname, uid, vip))
        db.commit()
        connection.mkfile('/home', fname)
        connection.print_result()
    return jsonify(canCreate = canCreate)

@app.route('/renamefile', methods=['GET', 'POST'])
def renamefile():
    global username
    global vip
    uid = username
    fname = request.form['filename']
    newname = request.form['newname']
    j=0
    flist=[]
    sql2 = '''
                SELECT fname FROM user_code WHERE user_id = %s and vm_ip = %s '''
    cursor.execute(sql2,(username,vip))
    result=cursor.fetchall()
    for tup in result:
        flist.insert(j,tup[0])
        j = j + 1
    if newname in flist:
        canCreate = 0
    else:
        canCreate = 1
        sql = '''
                        UPDATE user_code SET fname = %s WHERE fname = %s and vm_ip = %s'''
        cursor.execute(sql, (newname, fname, vip))
        db.commit()
        connection.chfname('/home', fname, newname)
        connection.print_result()
    return jsonify(canCreate = canCreate)

@app.route('/removefile', methods=['GET', 'POST'])
def removefile():
    global username
    global vip
    uid = username
    fname = request.form['filename']
    sql = '''
                    DELETE FROM user_code WHERE fname = %s  and vm_ip = %s '''
    cursor.execute(sql, (fname,vip))
    db.commit()
    connection.rmfile('/home', fname)
    connection.print_result()
    return jsonify()
@app.route('/etest',methods=['GET','POST'])
def etest():
    return render_template('test_editor.html')
if(__name__)=='__main__':
    app.run(host='0.0.0.0', debug=True)
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


