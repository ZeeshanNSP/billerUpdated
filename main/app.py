import json
from socket import timeout
import sys
import time
from datetime import datetime
import nv9biller
import printer as p
import time
from nv9biller import Biller
import _thread as thread
import threading 
import pymongo
from datetime import timedelta
from flask import Flask, render_template,redirect,request,jsonify, send_from_directory,session,abort
from flask_cors import CORS
from models import LOG,TRANSACTION,USER,PLAN
import threading



PORT_USED = "COM1"
app = Flask(__name__)
CORS(app)
biller = None
app.secret_key = 'NNSBILLER'

DBURL = "mongodb+srv://testUser:testUser@nv9-testing.9azuqdw.mongodb.net/?retryWrites=true&w=majority"
myclient = pymongo.MongoClient(DBURL)
mydb = myclient["NV9-Testing"]
users = mydb["users"]
transactions = mydb["transactions"]
logs = mydb["log"]
terminals = mydb["terminal"]
localConfig= None
#CRON JOBS
CRON_INTERVAL_DELAY = 5
CRON_CONFIG_DOWNLOADER = None
CRON_STACKER_UPLOADER = None

# Usefull Methods for operations
def initCRONS():
    global CRON_CONFIG_DOWNLOADER
    global CRON_STACKER_UPLOADER
    CRON_CONFIG_DOWNLOADER = set_interval(downloadConfig,CRON_INTERVAL_DELAY)
    CRON_STACKER_UPLOADER = set_interval(uploadStacker,CRON_INTERVAL_DELAY)

def LoadConfig():
    f = open("config/config.json",'r')
    global localConfig
    localConfig = json.load(f)
    f.close()

def updateConfig():
    f = open("config/config.json","w")
    f.write(json.dumps(localConfig))
    f.close()

def getLogFileName():
    now = datetime.now()
    dt_string = now.strftime("%d%m%Y")
    return dt_string

def downloadConfig():
    try:
        global localConfig
        query = { "TID": {"$eq":localConfig["serial"]} }
        t = terminals.find(query)
        for i in t:
            localConfig["status"] = i["config"]["status"]
         
        updateConfig()

    except:
        pass
    
def uploadStacker():
    try:
        f = open("config/counters.json","r")
        j  = json.load(f)
        query = { "TID": {"$eq":localConfig["serial"]} }
        updatedVal = { "$set": { "config.counter": j } }
        terminals.update_one(query,updatedVal)
    except:
        pass

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


#routes for the frontend and the biller machine
@app.route("/print-counters")
def printCounters():
    f = getCounters()
    p.printCounter(f)
    return "DONE"

@app.route("/cnt-rst")
def resetCounters():
    obj = {
        "5":0,
        "10":0,
        "20":0,
        "50":0,
        "100":0,
        "200":0,
        "500":0
    }
    f = open("config/counters.json","w")
    f.write(json.dumps(obj))
    f.close()
    return "Done"

@app.route("/get-counter")
def getCounters():
    f = open("config/counters.json","r")
    j  = json.load(f)
    TOTAL = 0
    for i in j:
        TOTAL = TOTAL + int(i) * j[i]
    j["total"] = TOTAL
    f.close()
    return j

def updateCounter(k):
    f = open("config/counters.json","r")
    j = json.load(f)
    f.close()
    prev = j[k]
    new = prev +1
    j[k] = new
    h = open("config/counters.json","w")
    h.write(json.dumps(j))
    h.close()

def NewLog(log):
    l = LOG()
    l.log  = log
    l.terminal = localConfig["serial"]
    logs.insert_one(l.toJson())
def NewTransaction(transaction):
    transaction.terminal = localConfig["serial"]
    transactions.insert_one(transaction.toJson())

def NewUser(user):
    try:
        users.insert_one(user.toJson())
    except:
        pass
@app.route("/ping-test")
def ping():
    import os
    ip = "8.8.8.8"
    response = os.popen(f"ping {ip}").read()
    res = {}
    if "Received = 4" in response:
        res["status"] = "successfull"
        res["log"] = response
    else:
        res["status"] = "unsuccessfull"
        res["log"] = response
    return res
@app.route("/stacker_stat")
def stat():
    global biller
    if biller is None:
        try:
            biller =Biller(PORT_USED)
        except:
            return "Machine Connection Problem"
    else:
        obj = {
            "serial":biller.serial,
            "counter":getCounters(),
            "stacker_full":False
        }
        if biller.stacker() :
            obj["stacker_full"] = True
        return obj
def Init_Biller():
    global biller
    if biller is None:
        try:
            biller = Biller(PORT_USED)
        except:
            print("Machine Connection Problem")

@app.route("/jwpTimeOut",methods=["GET","POST"])
def TimeOut():
    global biller    
    if request.method == "GET":
        f = p.printerTimeout("30","05830021351","JWP","1125","5",{})
        return "2500"
    elif request.method == "POST":
        amt = request.form.get("amount")
        mobile = request.form.get("mobile")
        service = request.form.get("service")
        term = request.form.get("terminal")
        name = request.form.get("profile")
        pr = request.form.get("price")
        valid = request.form.get("validity")
        rem = request.form.get("remaining")
        print((amt,mobile,term,service,term,name,pr,valid))
        pl = PLAN()
        pl.price = pr
        pl.profile = name
        pl.validity = valid
        t = p.printerTimeout(amt,mobile,service,term,rem,pl.toJson())
        t["terminal"] = term
        transactions.insert_one(t)
        biller.disable()
        biller.display_disable()
        biller.channels_set(None)
        return "0025"


@app.route("/check_reciept/<reciept>",methods=["GET"])
def getDetailVerfication(reciept):
    query = {"receipt_id" : {"$eq":reciept}}
    r = transactions.find_one(query)
    res = {}
    if r is None:
        return res
    else:
        t= TRANSACTION()
        t.TID = r["TID"]
        t.date = r["date"]
        t.time = r["time"]
        t.receipt_id = r["receipt_id"]
        t.service = r["service"]
        t.phone = r["phone"]
        t.pending_amount = r["pending_amount"]
        t.total_payment = r["total_payment"]
        t.plan = r["plan"]
        if "terminal" in r:
            t.terminal = r["terminal"]
        if int(t.pending_amount) == 0:
            return res
        res = t.toJson()
        return res

@app.route("/testPagePrint")
def testPage():
    p.printFile("./assets/TESTPAGE.txt")
    return "done"


@app.route("/printLog")
def printLogFile():
    p.printFile("logs/"+getLogFileName()+".txt")
    return "DONE"

def acceptMoney(port):
    global biller
    amt = "0.00"
    print('-------------------')
    print('Biller test program')
    print('SN: {:08X}'.format(biller.serial))
    print('--------------------')
    print('Enabling biller...')
    biller.channels_set(biller.CH_ALL)

    biller.display_enable()
    biller.enable()
    while True:
        try:         
            events = biller.poll()
            for event in events:
                e =str(event)
                if "Credit ->" in e:
                    r = e.split("->")[1].strip()
                    amt =r
                    DisableBiller()
                    return amt
                #now = datetime.now()
                #dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                #print("["+dt_string+"]",event)
            
            time.sleep(0.2)
        except:
            print('Disabling biller...')
            biller.disable()
            biller.display_disable()
            biller.channels_set(None)
            break
    return amt




@app.route("/disable-biller")
def DisableBiller():
    global biller
    biller.disable(); 
    biller.display_disable() 
    biller.channels_set(None)
    return "DONE"

@app.route("/enable-biller")
def enableBiller():
    global biller
    biller.channels_set(biller.CH_ALL)
    biller.display_enable()   
    biller.enable()      
    return "DONE"
@app.route("/cash-accepter-jwp",methods=["GET"])
def JWPbillerPage():
    return render_template("cash-accepter-jwp.html")
@app.route("/jwp-money",methods = ["GET"])
def handleJWPMoney():
    return getJWP(PORT_USED)

def getJWP(port):
    global biller
    notes_avail = [5,10,20,50,100,200,500]
    previous_status = ""
    amount_credited = "0.0"  
    allowed_notes =[biller.CH_0,biller.CH_1,biller.CH_2]
    #print('-------------------')
    print('Biller test program')
    print('SN: {:08X}'.format(biller.serial))
    #print('--------------------')
    #print('Enabling biller...')
    biller.channels_set(allowed_notes)
    biller.display_enable()   
    biller.enable() 
    f = open(getLogFileName()+".txt",'a')
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")  
    str_log = "["+dt_string+"] Ready"
    f.write(str_log+"\n")
    NewLog("Ready")
    while True:
        try:                    
            events = biller.poll()
            for event in events:
                e =str(event) 
                if e != previous_status:
                    previous_status = e
                    now = datetime.now()
                    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                    str_log = "["+dt_string+"] "+str(event)
                    NewLog(str(event))
                    print(str_log)
                    f.write(str_log+"\n")
                    
                    if "Credit" in e:
                        r = e.split("->")[1].split()                  
                        amount_credited = r[0]    
                        print("[AMOUNT  ]",amount_credited)               
                        updateCounter(amount_credited.split(".")[0])
                        DisableBiller()
                        f.close()
                        return amount_credited  
                else:               
                    pass
        except Exception as exp:
            print('Disabling biller...',exp)
            DisableBiller()
            return amount_credited
    DisableBiller()
    biller.channels_set(None)
    return amount_credited


@app.route("/cmdPrint",methods=["GET","POST"])
def testPr():
    commision_applied = ["du","du | extra minutes"]
    if request.method == "GET":
        p.printer("100","0583009340","du | extra hours","0125",True)
        return "152"
    elif request.method == "POST":
        amount = request.form.get("amount")
        mobile = request.form.get("number")
        service = request.form.get("company")
        print("[LOG DATA]",amount,mobile,service)
        c = False
        if service in commision_applied:
            c  = True
        p.printer(amount,mobile,service,"0125",c)
        return "521"

@app.route("/voucherPrint",methods=["GET","POST"])
def printVoucher():
    if request.method  ==  "GET":
        q =  p.voucher("338","11590","115645614515","30-Days","30","971583009341")
    elif request.method == "POST":
        vc = request.form.get("code")
        pl = request.form.get("profile")
        site = request.form.get("site")
        paid = request.form.get("amount")
        ph = request.form.get("phone")
        serial = "1122"
        q = p.voucher(site,serial,vc,pl,paid,ph)
        q["terminal"] = localConfig["serial"]
        transactions.insert_one(q)
        return "221"  

@app.route("/")
def index():
    if localConfig["status"] == "on":
        return render_template("index.html")
    else:
        return render_template("siteDown.html")
@app.route("/terminal")
def renderTerminalSettings():
    return render_template("terminal.html")
@app.route("/pin")
def renderinPage():
    return render_template("pin.html")
@app.route("/timeout")
def sendTimeout():
    return render_template("timeout.html")
@app.route("/reciept")
def recieptDetail():
    return render_template("reciept.html")
@app.route('/accept-money')
def hello_world():
    moneyaccepted = acceptMoney(PORT_USED)
    return moneyaccepted
@app.route("/plan",methods= ["GET"])
def plansPage():
    return render_template("plan.html")
@app.route("/jwp",methods=["GET"])
def jwp():
    return render_template("jwp.html")
@app.route("/re")
def recieptHandler():
    return render_template("re.html")


#Routes for the css,js and other image assets
@app.route("/assets/<path:path>")
def sendAssets(path):
    return send_from_directory("assets/",path)
@app.route("/css/<path:path>")
def sendCss(path):
    return send_from_directory("css/",path)
@app.route("/js/<path:path>")
def sendJS(path):
    return send_from_directory("js/",path)
@app.route("/lib/<path:path>")
def sendLibs(path):
    return send_from_directory("lib/",path)


def AppRun():
    app.debug = True
    app.run(host="0.0.0.0",port=443, use_reloader=False,ssl_context=("localhost+2.pem","localhost+2-key.pem"))
if __name__ == '__main__':    
    LoadConfig()

    threading.Thread(Init_Biller()).start()
    print("Waiting for Biller to INIT")
    while biller is None:
        Init_Biller()
        time.sleep(0.5)
    if biller is not None:
        if localConfig["serial"]  == "":
            localConfig["serial"] = biller.serial
            updateConfig()
        print("Init Biller Success")
        initCRONS()
        threading.Thread(AppRun()).start()
        
        
        
    

