import os 
import subprocess
from flask import Flask , render_template , request
from gtts import gTTS
import json
import sqlite3

app = Flask(__name__)
true = 1
false = 0
DB_NAME = "../db/home_control"


def isTrue(stato):
    return stato > 0

def run_cmd(cmd,input):
    if(isTrue(input)):
        return os.system(cmd)
    else:
        return str(subprocess.check_output([cmd],shell=True,stderr=subprocess.PIPE))
    
def format_amixer_output(out):
    perc = out.rfind('%')
    if(out[perc-3:perc-2] == '['):
        return out[perc-2:perc]
    elif(out[perc-3:perc-2] == ' '):
        return out[perc-1:perc]
    else:
        return out[perc-3:perc]
    
def format_temperatura_interna(out):
    return out[7:12]

def parla_txt(testo):
    tts = gTTS(text=testo, lang='it')
    tts.save('tts_out.mp3')
    subprocess.run(["omxplayer","tts_out.mp3"])

def find_my_ip():
    print("START find_my_ip >>")
    out = run_cmd('ifconfig',false)
    ipP = out.find('192.168.1.')
    print("INFO find_my_ip >> ipP: "+str(ipP))
    my_ip = out[ipP:ipP+len("192.168.1.255")]
    print("END find_my_ip >> my_ip: "+my_ip)
    
def create_connection(db_file):
    print("START create_connection >> db_file:"+db_file)
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    print("END create_connection >>")
    return conn
    
def get_all_users():
    print("START get_all_users >>")
    
    cur = create_connection(DB_NAME).cursor()
    cur.execute("SELECT * FROM USER")
    rows = cur.fetchall()
    #print("END get_all_users >> rows:"+rows)
    cur.close()
    return rows
    
def insert_new_user(user):
    print("START insert_new_user >>")   
    con = create_connection(DB_NAME)
    sql_insert ="INSERT INTI USER (ip,mac) VALUES ('"+user['ip']+"','"+user['mac']+"');"
    print("INFO insert_new_user >>"+sql_insert) 
    cur= con.cursor()
    count = cur.execute(sql_insert)
    con.commit()
    cursore.close()
    return count 

def search_identity(cur_user,all_users):
    for row in all_users:
        if(row[2] == cur_user['mac']):
            return row
    return insert_new_user(cur_user)

def extract_mac(out):
    print("START extract_mac >>"+out)
    wr = 'MAC Address: '
    wrl = len(wr)
    wf = len("XX:XX:XX:XX:XX:XX")
    wi = out.rfind(wr)
    mac = out[wi+wrl:wi+wrl+wf]
    print("INFO extract_mac >> mac: "+mac)
    if(mac[2:3] == ':'):
        return mac
    else:
        return ""

    
def check_identity(ip,my_ip,allFlg,all_users):
    res = {}
    res['ip'] = ip
    res['status'] = "ONLINE"
    
    if(my_ip == ip):
        return res

    out = run_cmd('sudo nmap -F '+ip,false).replace('"','')
    isDown = out.rfind("(0 hosts up)")
    if(isDown > 0):
        res['status'] = "OFFLINE"
    else:
        res['mac'] = extract_mac(out)
        res['row'] = search_identity(res,all_users)
        
    if(allFlg):
        res['all'] = out
    
    return res

def git_pull():
    print("START git_pull >> ")
    return run_cmd('sudo git pull',false)



def list_hosts_up(allFlg):
    out = run_cmd('nmap -v -sn 192.168.1.*',false)
    splitted = out.split('Host is up')
    my_ip = find_my_ip()
    
    final = []
    if(len(splitted) > 1):
            for val in splitted:
                str = val
                perc = str.rfind('192.168.1.')
                obj = str[perc: perc + 13].replace('n','').replace('\\','')
                if(len(obj) > 0):
                    final.append(check_identity(obj,my_ip,allFlg,get_all_users()))

    return json.dumps(final)

@app.route('/parla/<testo>')
def parla(testo):
    parla_txt(testo)
    return render_template('index.html')

@app.route('/sorveglia')
def sorveglia():
    return list_hosts_up(request.args.get('all'))	

@app.route('/sorveglia/<ip>')	
def sorverglia_ip(ip):	
    my_ip = ""	
    return json.dumps(check_identity(ip,my_ip,request.args.get('all')))

@app.route('/pull')	
def pull():	
    return git_pull()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/SETTINGS/')
def options():
#    print ('vol= '+request.args.get('volume'))
    if(request.args.get('volume')):
        volumeIn = run_cmd('amixer set PCM -- ' + request.args.get('volume') + '%',true)
    volume = format_amixer_output(run_cmd('amixer get PCM ',false))
    temperatura_interna = format_temperatura_interna(run_cmd('/opt/vc/bin/vcgencmd measure_temp',false))
    if(request.args.get('parole')):
        parla_txt(request.args.get('parole'))
    
    return render_template('options.html',volume=volume,name='SETTINGS',temperatura_interna=temperatura_interna)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
