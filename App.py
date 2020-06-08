import os
import subprocess
from flask import Flask , render_template , request
from gtts import gTTS
import json

app = Flask(__name__)
true = 1
false = 0

def isTrue(stato):
    return stato > 0

def run_cmd(cmd,input):
    print("START run_cmd >> cmd:'"+cmd+"' input:'"+input+"'")
    if(isTrue(input)):
        return os.system(cmd)
    else:
        out = str(subprocess.check_output([cmd],shell=True,stderr=subprocess.PIPE))
        print("END run_cmd >> out:'"+out+"'")
        return out
    
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

def list_hosts_up(allFlg):
    print("START list_hosts_up >> allFlg:'"+allFlg+"'")
    out = run_cmd('nmap -v -sn 192.168.1.*',false)
    splitted = out.split('Host is up')
    final = []
    if(len(splitted) > 1):
            print("INFO list_hosts_up >> Ci sono circa "+len(splitted)+" hosts up")
            for val in splitted:
                str = val
                perc = str.rfind('192.168.1.')
                obj = str[perc: perc + 13].replace('n','').replace('\\','')
                if(len(obj) > 0):
                    print("INFO list_hosts_up >> "+obj+" is up")
                    final.append(check_identity(obj,None) if allFlg else obj)
    
    res = json.dumps(final)
    print("END list_hosts_up >> res:"res)
    return res

@app.route('/parla/<testo>')
def parla(testo):
    parla_txt(testo)
    return render_template('index.html')

@app.route('/sorveglia')
def sorveglia():
    
    return list_hosts_up(request.args.get('all'))

def check_identity(ip,allFlg):
    res = {}
    res['ip'] = ip
    out = run_cmd('sudo nmap -F '+ip,false).replace('"','')
    isDown = out.rfind("(0 hosts up)")
    if(isDown > 0):
        res['status'] = "OFFLINE"
    else:
        res['status'] = "ONLINE"
        wr = 'MAC Address: '
        wrl = len(wr)
        wf = len("XX:XX:XX:XX:XX:XX")
        wi = out.rfind(wr)
        res['mac'] = out[wi+wrl:wi+wrl+wf]
    if(allFlg):
        res['all'] = out
        
    return json.dumps(res)

@app.route('/sorveglia/<ip>')
def sorverglia_ip(ip):
    return check_identity(ip,request.args.get('all'))

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
