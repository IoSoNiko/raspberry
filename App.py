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

def extract_mac(txt):
   wr = 'MAC Address: '
   wrl = len(wr)
   wf = len("XX:XX:XX:XX:XX:XX")
   wi = txt.rfind(wr)
   return txt[wi+wrl:wi+wrl+wf] 
    
def check_identity(ip,allFlg):
    response = {}
    response['ip'] = ip
    out = run_cmd('sudo nmap -F '+ip,false).replace('"','')
    isDown = out.rfind('(0 hosts up)')
    
    if(isTrue(isDown)):
        response['status'] = "OFFLINE"
    else:
        response['status'] = "ONLINE"
        response['mac'] = extract_mac(out)
        
    if(allFlg):
        response['all'] = out
    
    return response

def list_hosts_up():
    out = run_cmd('nmap -v -sn 192.168.1.*',false)
    splitted = out.split('Host is up')
    final = []
    if(len(splitted) > 1):
            for val in splitted:
                str = val
                perc = str.rfind('192.168.1.')
                obj = str[perc: perc + 13].replace('n','').replace('\\','')
                if(len(obj) > 0):
                    final.append(obj)

    return json.dumps(final)

@app.route('/parla/<testo>')
def parla(testo):
    parla_txt(testo)
    return render_template('index.html')

@app.route('/sorveglia')
def sorveglia():
    return list_hosts_up()

@app.route('/sorveglia/<ip>')
def sorverglia_ip(ip):
    return check_identity(ip,request.args.get('ALL'))

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
