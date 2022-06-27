from pyexpat.errors import messages
import re
import uuid
from django.dispatch import receiver
from flask import Flask,redirect,url_for,render_template,request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@Enare6653839@localhost/exquitec'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = "exquitec key"
db = SQLAlchemy(app)

users_messages =  db.Table('users-messages',
    db.Column("user_id", db.Integer, db.ForeignKey('users.id')),
    db.Column("message_id", db.Integer, db.ForeignKey('messages.id'))
)


class Users(db.Model):
    """Model for user accounts."""

    id = db.Column(db.Integer,
                   primary_key=True)
    username = db.Column(db.String(50),
                         nullable=False,
                         unique=True)
    password = db.Column(db.String(200),
                         primary_key=False,
                         unique=False,
                         nullable=False)
    uuid = db.Column(db.String(100),
                         nullable=False,
                         unique=True)
    msg = db.relationship("Messages", secondary = users_messages, backref = "participants")
    
    def __repr__(self):
        return '<User {}>'.format(self.username)

class Messages(db.Model):
    id = db.Column(db.Integer,
                   primary_key=True)
    message = db.Column(db.String(500),
                         nullable=False,
                         unique=False)  
    recived_at = db.Column(db.DateTime, unique=False,
                           nullable=False, default=datetime.utcnow())
    sender =  db.Column(db.String(100),
                         nullable=False)
    receiver = db.Column(db.String(100),
                       nullable=False)
    read = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return '<message {}, {}>'.format(self.message, self.recived_at)



@app.post('/')
def home():
    print(request.headers)
    username = request.form.get('username', None)
    password = request.form.get('password', None)
    form = request.form.get('form', 'login')
    if username == None or password == None or username.strip() == '' or password == '':  # no password or user name
        flash("username or password field left empty")
        return render_template('login.html')
    elif form == 'login': #user login success
        user = Users.query.filter_by(username=username, password=password).first()
        if user == None:
            flash('username or password incorrect')
            return render_template('login.html')
        return redirect(f'/chat={user.uuid}')
    elif form == 'signup':
        user = Users.query.filter_by(username=username).first()
        if user == None:#no user
            db.session.add(
                Users(username=username, password=password, uuid=str(uuid.uuid4())))
            db.session.commit()
            user = Users.query.filter_by(
            username=username, password=password).first()
            return redirect(f'/chat={user.uuid}')
        else: #username already exist
            flash('username already exist')
            return render_template('login.html')
    else:
        return redirect('/')
@app.get('/')
def index():
    return render_template('login.html')


@app.route("/chat=<uuid>", methods=['GET', 'POST'])
def chat(uuid):
    user = Users.query.filter_by(uuid=uuid).first()
    if user == None:
        return redirect('/')
    else:
        freinds = []
        unread = {}
        for msg in user.msg:
            for participant in msg.participants:
                if participant != user:
                    unread[participant.username] = 0
                    if {'username': participant.username, 'uuid': participant.uuid} not in freinds:
                         freinds.append({'username' : participant.username, 'uuid': participant.uuid,})                                   
                    if msg.read == False:
                        unread[participant.username] += 1   

        return render_template('chat.html', freinds=list(freinds), uuid=user.uuid, unread=unread, url = request.host_url )
        
@app.post('/post-<uuid>')
def post(uuid):
    user = Users.query.filter_by(uuid=uuid).first()
    reciever_form = request.form.get('reciever', None)
    msg = request.form.get('message', None)
    if reciever_form == None:
        user = None # so as to use the if below
    else:
        reciever = Users.query.filter_by(uuid=reciever_form).first()
    if user == None or reciever == None or msg == None or msg.strip() == '':
        return "error : message not sent", 404
    else : 
        msg = Messages(message=msg, sender=uuid, receiver=reciever.uuid)
        msg.participants.append(user)
        msg.participants.append(reciever)
        db.session.add(msg)
        db.session.commit()
        return "success", 200


@app.get('/unread-<uuid>/<fruuid>')
def get_unread_msg(uuid,fruuid):
    unread_messages = Messages.query.filter_by(read=False, sender=uuid, receiver=fruuid).all(
    ) + Messages.query.filter_by(read=False, sender=fruuid, receiver=uuid).all()
    messages = []
    for message in unread_messages:
        if fruuid == message.receiver:
            message.read=True
        messages.append({"message": message.message,
                        "recived_at": message.recived_at, "sender": message.sender, })
    messages = sorted(messages, key=lambda item: item['recived_at'])
    db.session.commit()
    return render_template('message.html', messages=messages, user=uuid)


@app.get('/read-<uuid>/<fruuid>')
def get_msg(uuid, fruuid):
    messages = []
    messagesDb = Messages.query.filter_by(read=True, sender=uuid, receiver=fruuid).all(
    ) + Messages.query.filter_by(read=True, sender=fruuid, receiver=uuid).all()

    for message in messagesDb:
        messages.append({"message": message.message,
                        "recived_at": message.recived_at, "sender": message.sender, })
     
    messages = sorted(messages, key=lambda item: item['recived_at'])
    command = f"<div id='loader' hx-trigger='every 1s' hx-get='/unread-{uuid}/{fruuid}' class='' hx-target='#loader' hx-swap='beforebegin'></div>"
    return render_template('message.html', command=command, messages=messages, user=uuid,  read = True)

@app.post('/add-<uuid>/')
def add_freind(uuid):
    new = request.form.get("new")
    if new != None or new.strip() != '':
        freind = Users.query.filter_by(username=new).first()
        user = Users.query.filter_by(uuid=uuid).first()
        msg = Messages(message='cmd: add freind', sender=user.uuid, receiver = freind.uuid,read=True)
        msg.participants.append(user)
        msg.participants.append(freind)
        db.session.add(msg)
        db.session.commit()
        return redirect(f"/chat={uuid}")
    else:
        return redirect(f"/chat={uuid}")
    


if __name__ == '__main__':
    #DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run(port=5005,debug=True, host='0.0.0.0')


