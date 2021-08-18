
from flask import Flask, render_template,url_for
from firebase_admin import db
from data import lignes, techniciens,admins
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin.auth import UserRecord
import uuid
import json
import os
import requests
from datetime import datetime
from datetime import timedelta


from configparser import ConfigParser
file='config.ini'
config =ConfigParser()
config.read(file)

cred = credentials.Certificate(config['database']['cred_variable'])
firebase_admin.initialize_app(cred,{
    'databaseURL': config['database']['databaseURL']
})
rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FIREBASE_WEB_API_KEY=config['database']['FIREBASE_WEB_API_KEY']

# db.reference("/lignes").set(lignes)
# db.reference("/techniciens").set(techniciens)
# db.reference("/admins").set(admins)



app = Flask(__name__)
# creating a user
@app.route('/login/signup/<mail>/<pswrd>/<t>/<nom>/<matricule>')
def create_user(mail,pswrd,t,nom,matricule):
     uuidOne = uuid.uuid1()
     if t=='user':
         
         newuid='u-'+str(uuidOne)
         # liste_tech=db.reference("/techniciens").get()
         # for value in liste_tech.values():
         #     if ( matricule in value):
         auth.create_user(email=mail, uid=newuid, password=pswrd)
     elif t=='admin':
         
           newuid='a-'+str(uuidOne)
           liste_ad=db.reference("/admins").get()
           for value in liste_ad.values():
            if ( matricule in value):
              auth.create_user(email=mail, uid=newuid, password=pswrd)
            
     return render_template('login.html')
#log in   
def sign_in(email: str, password: str, return_secure_token: bool = True):
    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": return_secure_token
    })

    r = requests.post(rest_api_url,
                      params={"key": FIREBASE_WEB_API_KEY},
                      data=payload)
    return r.json()
#technicien login
@app.route("/login/user/<mail>/<pw>")   
def login_user(mail,pw,return_secure_token:bool =True):
    result=sign_in(mail,pw,return_secure_token)
    print(result)
    try:
       result['error']['code']
       e='invalid passwoed or email'
       return render_template('login.html',error=e)
    except :
       if result['localId'][0]=='u':
        return render_template('technicien.html')
       elif result['localId'][0]=='a':
        return render_template('admin.html') 
#admin login
@app.route("/login/admin/<mail>/<pw>")   
def login_admin(mail,pw,return_secure_token:bool =True):
    result=sign_in(mail,pw,return_secure_token)
    print(result)
    try:
       result['error']['code']
       err=True
       return render_template('login.html',e=err)
    except :
        if result['localId'][0]=='a':
           return render_template('admin.html')  
        elif result['localId'][0]=='u':
          return render_template('technicien.html')
#loading login page  
@app.route("/")
def login():
    return render_template('login.html')
#loading signup page 
@app.route('/login/signup')
def signup():
    return render_template('signup.html')
#loading technicien interfaace
@app.route('/login/technicien')
def technicien():
    return render_template('technicien.html',key='choisir une ligne')  
#returning data
@app.route('/technicien/<key>')
def techlist(key):
    liste_ps=db.reference("/lignes/"+key+"/postes").get()
    liste_pr=db.reference("/lignes/"+key+"/produits").get()
    listet=db.reference("/techniciens").get()
    return render_template('technicien.html',liste_ps=liste_ps, liste_pr= liste_pr, key=key,listet=listet)


@app.route('/technicien/<key>/<ps>/<pr>/<tech>/<des>/<piece>/<startdate>/<starttime>/<finishdate>/<finishtime>/<happ>/<rq>')
def interv(key,ps,pr,tech,des,piece,startdate,starttime,finishdate,finishtime,happ,rq):
    inter=db.reference("/intervention").get()   
    uuidOne = uuid.uuid1()
    try:   
        inter[str(uuidOne)]={}
    except:
        inter={}
        inter[str(uuidOne)]={}
    inter[str(uuidOne)]['ligne']=key 
    inter[str(uuidOne)]['poste']=ps
    inter[str(uuidOne)]['produit']=pr
    inter[str(uuidOne)]['intervenant']=tech
    inter[str(uuidOne)]['description']=des
    inter[str(uuidOne)]['piece']=piece
    FMT='%H:%M'
    d=datetime.strptime(finishtime,FMT)-datetime.strptime(starttime,FMT)
    if d.days<0:
     d=timedelta(days=0,seconds=d.seconds)
    print(d)
    v=True
    inter[str(uuidOne)]['duré']=str(d)
    inter[str(uuidOne)]['start_date']=startdate
    inter[str(uuidOne)]['start_time']=starttime
    inter[str(uuidOne)]['finish_date']=finishdate
    inter[str(uuidOne)]['finish_time']=finishtime
    inter[str(uuidOne)]['heure_appel']=happ
    inter[str(uuidOne)]['remarque']=rq
    db.reference("/intervention").set(inter)
    return render_template('technicien.html',dure=d,valid=v)
#loading admin interface 
@app.route('/login/admin')
def admin():
    return render_template('admin.html')  
#loading home page
@app.route('/admin/home')
def home():
    return render_template('home.html') 
#loading techniciens page+ its data
@app.route('/admin/home/techniciens')
def techniciens():
    Tliste=db.reference("/techniciens").get()
    return render_template('techniciens.html',Tliste=Tliste) 
#loading lignes page+ its data
@app.route('/admin/home/lignes')
def lignes():
    Lliste=db.reference("/lignes").get()
    return render_template('lignes.html',Lliste=Lliste) 
# adding a new technicen
@app.route('/admin/home/techniciens/<nom>/<matricule>') 
def addtech(nom,matricule):
    liste_tech=db.reference("/techniciens").get()
    liste_tech[nom]=matricule
    db.reference("/techniciens").set(liste_tech)
    return render_template('techniciens.html')
# deleting a technicien
@app.route('/admin/home/techniciens/<deleted>')
def deltech(deleted):
    liste_tech=db.reference("/techniciens").get()
    liste_tech.pop(deleted) 
    db.reference("/techniciens").set(liste_tech)
    return render_template('techniciens.html')       
#adding a new ligne
@app.route('/admin/home/lignes/add/<nomligne>') 
def addligne(nomligne):
    liste_l=db.reference("/lignes").get()
    liste_l[nomligne]={'postes':[''],'produits':['']}
    db.reference("/lignes").set(liste_l)
    return render_template('lignes.html' )
#deleting a ligne
@app.route('/admin/home/lignes/delete/<deletedl>')
def delligne(deletedl):
    liste_l=db.reference("/lignes").get()
    liste_l.pop(deletedl)
    db.reference("/lignes").set(liste_l)
    return render_template('lignes.html' )
 #adding a poste   
@app.route('/admin/home/lignes/poste/<nl>/<np>')
def addposte(nl,np):
    liste_ps=db.reference("/lignes/"+nl+"/postes").get()
    liste_ps.append(np)
    db.reference("/lignes/"+nl+"/postes").set(liste_ps)
    return render_template('lignes.html' )
 # the list of choosen ligne 
@app.route('/admin/home/lignes/delp/<c>')
def choice(c):
    listpost=db.reference('/lignes/'+c+'/postes').get()
    return render_template('lignes.html',listp=listpost)
#deleting a poste
@app.route('/admin/home/lignes/delp/<nline>/<npost>')
def delposte(nline,npost):
    liste_ps=db.reference("/lignes/"+nline+"/postes").get()
    liste_ps.remove(npost)
    db.reference("/lignes/"+nline+"/postes").set(liste_ps)
    return render_template('lignes.html' ) 
 #adding a produit   
@app.route('/admin/home/lignes/produit/<nl1>/<np1>')
def addproduit(nl1,np1):
    liste_pr=db.reference("/lignes/"+nl1+"/produits").get()
    liste_pr.append(np1)
    db.reference("/lignes/"+nl1+"/produits").set(liste_pr)
    return render_template('lignes.html' )
 # the list of choosen ligne 
@app.route('/admin/home/lignes/delprd/<c1>')
def choice1(c1):
    listproduit=db.reference('/lignes/'+c1+'/produits').get()
    return render_template('lignes.html',listpr= listproduit)
#deleting a produit
@app.route('/admin/home/lignes/delprd/<nline1>/<npr>')
def delproduit(nline1,npr):
    liste_pr=db.reference("/lignes/"+nline1+"/produits").get()
    liste_pr.remove(npr)
    db.reference("/lignes/"+nline1+"/produits").set(liste_pr)
    return render_template('lignes.html' ) 

#loading intervention page
@app.route('/admin/home/intervention')
def intervention():
    return render_template('intervention.html')
         
def toDays(date):
  l=date.split("-")
  return int(l[0])*365+int(l[1])*30+int(l[2])

@app.route('/admin/home/intervention/<start>/<finish>')
def get_inter_bydate(finish,start):
  inter=db.reference("/intervention").get()
  l,ps,pr,interv,des,piece,rq,dr,ds,df,ts,tf,hp=[],[],[],[],[],[],[],[],[],[],[],[],[]
  for element in inter.values(): 

    if toDays(element['start_date'])>= toDays(start) and toDays(element['finish_date'])<=toDays(finish): 
     
        l.append(element['ligne'])  
        ps.append(element['poste'])
        pr.append(element['produit'])
        interv.append(element['intervenant'])
        des.append(element['description'])
        piece.append(element['piece'])
        rq.append(element['remarque'])
        dr.append(element['duré'])
        ds.append(element['start_date'])
        df.append(element['finish_date'])
        ts.append(element['start_time'])
        tf.append(element['finish_time'])
        hp.append(element['heure_appel'])
        val=True 
  return render_template('intervention.html',v2=val,l=l,ps=ps,pr=pr,interv=interv,des=des,piece=piece,rq=rq,dr=dr,ds=ds,df=df,ts=ts,
                         tf=tf,hp=hp)
@app.route('/admin/home/profile/')
def profile():
     aliste=db.reference("/admins").get()
     return render_template('profile.html',aliste=aliste) 


@app.route('/admin/home/profile/<nom>/<matricule>')
def addadmin(nom,matricule):
    liste_ad=db.reference("/admins").get()
    liste_ad[nom]=matricule
    db.reference("/admins").set(liste_ad)
    return render_template('profile.html')

@app.route('/admin/home/profile/<deleted>')
def deladmin(deleted):
    liste_ad=db.reference("/admins").get()
    liste_ad.pop(deleted) 
    db.reference("/admins").set(liste_ad)
    return render_template('profile.html')       


if __name__ == '__main__':
    app.run()
