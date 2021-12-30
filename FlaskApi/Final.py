from flask import Flask,jsonify,request,send_file
from functools import wraps
import os
from flask_cors import CORS,cross_origin
import tabula
import random
from flask_pymongo import PyMongo
from bson.json_util import dumps
import pandas as pd
import re
from matplotlib import pyplot as plt
import jwt

app=Flask(__name__)

CORS(app)

app.config["MONGO_URI"]="mongodb://127.0.0.1:27017/Users"
app.config['SECRET_KEY'] = 'your secret key'

mongo=PyMongo(app)
UPLOAD_FOLDER = './inputs/'

upload2="./outputs/"
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'],algorithms=("HS256"))
            current_user = mongo.db.users.find_one({'email':data["public_id"]})
        except:
            return jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes
        return  f(current_user, *args, **kwargs)
  
    return decorated

def token_require(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        file=None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if "file" in request.files:
            file=request.files["file"]
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'],algorithms=("HS256"))
            current_user = mongo.db.users.find_one({'email':data["public_id"]})
        except:
            return jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes
        return  f(current_user,file, *args, **kwargs)
  
    return decorated
  
def getToken(User_ID):
    return jwt.encode({'sub':User_ID},app.config.get("SECRET_KEY"),algorithm="HS256")

if not(os.path.isdir(UPLOAD_FOLDER)):
    path=os.path.join('./','inputs')
    os.mkdir(path)
if not(os.path.isdir(upload2)):
    path=os.path.join('./','outputs')
    os.mkdir(path)
if not(os.path.isdir("./images")):
    path=os.path.join('./','images')
    os.mkdir(path)
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

@app.route("/getPie",methods=["GET"])
def getPie():
    data=mongo.db.images.find_one({"type":"pie"})
    #print(data)
    return send_file(data["path"],mimetype='image/png',as_attachment=True)
  
@app.route('/getBar',methods=['GET'])
@cross_origin()
@token_required
def getBar(user):
    data=mongo.db.images.find_one({"type":"bar"})
    print(data)
    return send_file(data["path"],mimetype='image/png',as_attachment=True)

@app.route("/getHist",methods=["GET"])
@cross_origin()
@token_required
def getHist(user):
    data=mongo.db.images.find_one({"type":"hist"})
    #data=list(data)
    print(data)
    return send_file(data["path"],mimetype='image/png',as_attachment=True)
@app.route('/Images',methods=["GET"])
@cross_origin()
@token_required
def getimg(user):   
    print("myimg")
    return send_file("./images/Screenshot_1638526552.png",mimetype='image/png')

@app.route("/",methods=["POST"])
@token_require
def ProcessData(name,file):
    r=random.randint(0,2000000)
    paths=""
    try:
        file=file
        if file:
           
            if(os.path.isfile('./inputs/'+file.filename)):
                paths="("+str(r)+")"+file.filename
                #print(paths)
                file.save(os.path.join('./inputs/',paths))  
                paths="./inputs/"+"("+str(r)+")"+file.filename               
            else:
                file.save(os.path.join('./inputs/', file.filename))
                paths='./inputs/'+file.filename
            #print(paths)
            result=data(paths)
            #print(file.filename)
            result.status_code=200
            return result
        else:
            resp=jsonify({"message":"Please upload a proper file"})
            resp.status_code=404
            return resp
    except:
        return jsonify({"message":"Some Error Occured please try after sometime"}),404
def data(file):
    rr=mongo.db.Records.drop()
    rrr=mongo.db.images.drop()
    r=random.Random()
    print(file.split("/")[2][-3:len(file.split('/')[2])])
    if(file.split("/")[2][-3:len(file.split('/')[2])]=='csv'):
        #file.save(file.split("/")[2])
        
        data=pd.read_csv(file,skipfooter=2,engine=('python'))
        dataa=data
        k=str(dataa)
        value=""
        name=""
        branch=""
        address=""
        if("Name:" in k):
            value=str(dataa.head(1))
            value=value.replace("\r"," ")
            vv=value.split("Branch Name:")
            #name=re.findall("^Name:*Branch Name$",value)
            #print(vv[0])
            name=vv[0].split(":")[1]
            name=name.replace("\\r","")
            value=value.replace(vv[0],'')
            vv=value.split("Communication Address")
            branch=vv[0].split(":")[1]
            branch=branch.replace("\\r","")
            #print(branch)
            value=value.replace(branch,'')
            vv=value.split("Address Last Updated On:")
            address=vv[0].split(":")[2] +vv[0].split(":")[3]
            address=address.replace("\\r"," ")
            #print(address)
            data=pd.read_csv(file,skipfooter=2,engine=('python'),skiprows=1)
        else:
            data=pd.read_csv(file,skipfooter=2,engine=('python'))
        data.drop(data.columns[data.columns.str.contains('unnamed',case = False)],axis = 1, inplace = True)
        data.replace(["Unnamed: 0","Unnamed: 1"],0,inplace=True)
        #print(data.head())
        data.fillna(0,inplace=True)
        data1=data.to_dict('records')
        #print(data.head())
        records=mongo.db.Records.insert_many(data1,ordered=(False))
        records=mongo.db.Records.find()
        #resp=dumps(records)
        #print(resp)
        data["Date"]=pd.to_datetime(data["Date"])
        trans=pd.DataFrame({"Transcation Type":data["Tran\rType"]})
        trans=trans.value_counts()
        labels=[x[0] for x in trans.keys()]
        values=[]
        for x in labels:
            values.append(trans[x])
        fig = plt.figure(figsize=(9,6))
        my_path = os.path.abspath("./images")
        data["Deposits"]=pd.to_numeric(data["Deposits"])
        plt.hist(data["Deposits"])
        plt.title("Number of times certain amount is debited")
        plt.xlabel("Deposit Amount")
        plt.ylabel("Count")
        plt.savefig(my_path+"/"+file.split("/")[2][0:-4]+"hist.png")
        plt.show()
        plt.bar(x=labels,height=values)
        plt.title("Number of Credits and Debits")
        plt.xlabel("Transcation Type")
        plt.ylabel("Count")
        plt.savefig(my_path+"/"+file.split("/")[2][0:-4]+"bar.png")
        plt.show()
        
        per = data.Date.dt.to_period("M") 
        listt=[]
        for i in per:
            if i not in listt:
                listt.append(i)
        data["Withdrawals"]=pd.to_numeric(data["Withdrawals"])
        g=data.groupby(per)
        g=g.sum()
        #print(g)
        withdraw=list(g["Withdrawals"])
        balance=list(g["Balance"])
        withdraw=[int(x) for x in withdraw]
        balance=[int(x) for x in balance]
        #print(withdraw)
        #print(balance)
        df = pd.DataFrame({
        'date': listt,
        'Withdrawals': withdraw,
        'Balance': balance,
        'Deposits':list(g["Deposits"])
        })
        df.plot(x="date", y=["Withdrawals","Deposits"], kind="bar")
        
        plt.savefig(my_path+"/"+file.split("/")[2][0:-4]+"pie.png")
        plt.show()
        bar=mongo.db.images.insert_one({"type":"bar","path":"./images/"+file.split("/")[2][0:-4]+"bar.png"})
        pie=mongo.db.images.insert_one({"type":"pie","path":"./images/"+file.split("/")[2][0:-4]+"pie.png"})
        hist=mongo.db.images.insert_one({"type":"hist","path":"./images/"+file.split("/")[2][0:-4]+"hist.png"})
        return jsonify({"name":name,"Branch":branch,"address":address})
    else:
        #print(file.split("/")[2][0:-4])
        dfs=tabula.read_pdf(file,pages="all")
        [d.to_csv("./outputs/"+file.split("/")[2][0:-4]+".csv",mode="a+", index=False) for d in dfs]
        data=pd.read_csv("./outputs/"+file.split("/")[2][0:-4]+".csv")
        dataa=data
        k=str(dataa)
        value=""
        name=""
        branch=""
        address=""
        if("Name:" in k):
            value=str(dataa.head(1))
            value=value.replace("\r"," ")
            vv=value.split("Branch Name:")
            name=re.findall("^Name:*Branch Name$",value)
            #print(vv[0])
            name=vv[0].split(":")[1]
            name=name.replace("\\r","")
            value=value.replace(vv[0],'')
            vv=value.split("Communication Address")
            branch=vv[0].split(":")[1]
            branch=branch.replace("\\r","")
            #print(branch)
            value=value.replace(branch,'')
            vv=value.split("Address Last Updated On:")
            address=vv[0].split(":")[2] +vv[0].split(":")[3]
            address=address.replace("\\r"," ")
            #print(address)
            data=pd.read_csv("./outputs/"+file.split("/")[2][0:-4]+".csv",skipfooter=2,engine=('python'),skiprows=1)
        else:
            data=pd.read_csv("./outputs/"+file.split("/")[2][0:-4]+".csv",skipfooter=2,engine=('python'))
       # print(value)
       
        data.drop(data.columns[data.columns.str.contains('unnamed',case = False)],axis = 1, inplace = True)
        data.fillna(0,inplace=True)
        data.replace(["Unnamed: 0","Unnamed: 1"],0,inplace=True)
        data1=data.to_dict('records')
        records=mongo.db.Records.insert_many(data1,ordered=(False))
        records=mongo.db.Records.find()
        resp=dumps(records)
        data["Date"]=pd.to_datetime(data["Date"])
        trans=pd.DataFrame({"Transcation Type":data["Tran\rType"]})
        trans=trans.value_counts()
        labels=[x[0] for x in trans.keys()]
        values=[]
        for x in labels:
            values.append(trans[x])
        
        #plt.show()
        fig = plt.figure(figsize=(9,6))
        my_path = os.path.abspath("./images")
        data["Deposits"]=pd.to_numeric(data["Deposits"])
        plt.hist(data["Deposits"])
        plt.title("Number of times certain amount is debited")
        plt.xlabel("Deposit Amount")
        plt.ylabel("Count")
        plt.savefig(my_path+"/"+file.split("/")[2][0:-4]+"hist.png")
        plt.show()
        plt.bar(x=labels,height=values)
        plt.title("Number of Credits and Debits")
        plt.xlabel("Transcation Type")
        plt.ylabel("Count")
        plt.savefig(my_path+"/"+file.split("/")[2][0:-4]+"bar.png")
        plt.show()
        per = data.Date.dt.to_period("M") 
        listt=[]
        for i in per:
            if i not in listt:
                listt.append(i)
        data["Withdrawals"]=pd.to_numeric(data["Withdrawals"])
        g=data.groupby(per)
        g=g.sum()
        #print(g)
        withdraw=list(g["Withdrawals"])
        balance=list(g["Balance"])
        withdraw=[int(x) for x in withdraw]
        balance=[int(x) for x in balance]
        #print(withdraw)
        #print(balance)
        df = pd.DataFrame({
        'date': listt,
        'Withdrawals': withdraw,
        'Balance': balance,
        'Deposits':list(g["Deposits"])
        })
        df.plot(x="date", y=["Withdrawals","Deposits"], kind="bar")
        
        plt.savefig(my_path+"/"+file.split("/")[2][0:-4]+"pie.png")
        plt.show()
        bar=mongo.db.images.insert_one({"type":"bar","path":"./images/"+file.split("/")[2][0:-4]+"bar.png"})
        pie=mongo.db.images.insert_one({"type":"pie","path":"./images/"+file.split("/")[2][0:-4]+"pie.png"})
        hist=mongo.db.images.insert_one({"type":"hist","path":"./images/"+file.split("/")[2][0:-4]+"hist.png"})
        return jsonify({"name":name,"Branch":branch,"address":address})
      
@app.route("/Login",methods=["POST"])
def Login():
    _json=request.json
    email=_json["email"]
    password=_json["password"]
    user=mongo.db.users.find_one({"email":email,"password":password})
    if user:
        token = jwt.encode({'public_id' : email}, app.config['SECRET_KEY'], "HS256")
        resp=jsonify({'email':user['email'],'password':" ","token":token})
        resp.status_code=200
        return resp
    else:
        resp=jsonify({"message":"not found"})
        resp.status_code=404
        return resp
@app.route("/Register",methods=["POST"])
def Register():
    _json=request.json
    name=_json["name"]
    pwd=_json["password"]
    email=_json["email"]
    phone=_json["phone"]
    address=_json["address"]
    user=mongo.db.users.find_one({"email":email})
    if user:
        resp=jsonify({"message":"User Already exists"})
        resp.status_code=404
        return resp
    else:
        id=mongo.db.users.insert_one({'name':name,'email':email,'password':pwd,'phone':phone,'address':address})
        resp=jsonify({'name':name,'email':email,'password':" ",'phone':phone,'address':address})
        resp.status_code=200
        return resp
if __name__=="__main__":
    app.run(port=(7000),debug=(False))