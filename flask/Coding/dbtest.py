import pymysql
import paramiko
db  = pymysql.connect(host='192.168.0.96', user='root', passwd='', db='user_info', charset='utf8')
cursor = db.cursor()

flist=[]
i=0
sql = '''
            SELECT master FROM team_info where team_id = 'test'         
        '''
cursor.execute(sql)                            #if username == master
result = cursor.fetchall()
master=result[0]
print(master)
for tup in result:
     u_ip = tup[0]
     print(u_ip)
db.close()
