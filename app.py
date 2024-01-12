from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
import datetime
import pymongo


app = Flask(__name__)
app.config['SECRET_KEY'] = 'cosci57880'

socketio = SocketIO()
socketio.init_app(app)

online_user = []
room_user = {}
all_members = dict()
locked_groups = []
chat_log_all = []
chat_log_group = dict()
now_users = []

all_members = dict()
all_simu_group_info = [["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""],["","",""]]

tzone = datetime.timezone(datetime.timedelta(hours=8))
start_log_time = datetime.datetime.now(tz=tzone)
prev_log_time = datetime.datetime.now(tz=tzone)
mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["metaWeb"]
all_chat_collection = mongo_db["metaWebAllChat"]
group_chat_collection = mongo_db["metaWebGroupChat"]
grouping_msg_collection = mongo_db["metaWebGroupingMsg"]
locked_group_msg_collection = mongo_db["metaWebLockedGroupMsg"]


def check_group_position(data, simuNum):
    tmp_position = -1
    if simuNum == 0:
        for i in [0,1,2]:
            if all_simu_group_info[data.get("group")][i] == "":
                tmp_position = i
                break
    
    return tmp_position

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        now_users_str = ""
        global now_users
        if None in now_users:
            now_users = list(filter(None, now_users))
        if len(now_users) > 0:
            now_users_str = ("-=-").join(now_users)
        if 'username' in session:
            # return render_template('home.html', username=username, room=room)
            return redirect(url_for('home'))
        return render_template('index.html', now_users_str = now_users_str)
    else:
        username = request.form.get('username')
        room = request.form.get('room')
        now_users.append(username)
        session['username'] = username
        session['room'] = room
        if(room == None):
            session['room'] = "initial_room"
        socketio.emit('user enter act', {"user":username})
        # return render_template('home.html', username=username, room=room)
        return redirect(url_for('home'))

@app.route('/home/')
def home():
    if 'username' in session and 'room' in session:
        username = session['username']
        room = session['room']
        if(room == None):
            session['room'] = "initial_room"
            room = "initial_room"
        return render_template('home.html', username=username, room=room)
    else:
        # global now_users
        # if None in now_users:
        #     now_users = list(filter(None, now_users))
        # if len(now_users) > 0:
        #     now_users_str = ("-=-").join(now_users)
        # return render_template('index.html', now_users_str = now_users_str)
        return redirect(url_for('index'))


@app.route('/group/')
def group():
    print(session)
    if 'username' in session and 'room' in session:
        username = session['username']
        room = session['room']
        locked_groups_str = ""
        global locked_groups
        if None in locked_groups:
            locked_groups = list(filter(None, locked_groups))
        if len(locked_groups) == 1:
            locked_groups_str = str(locked_groups[0])
        elif len(locked_groups) >= 2:
            str_lock_groups = []
            for group in locked_groups:
                str_lock_groups.append(str(group))     
            locked_groups_str = "_".join(str_lock_groups)
        return render_template('group.html', username=username, room=room, all_simu_group_info=all_simu_group_info, locked_groups_str=locked_groups_str)
    else:
        # global now_users
        # if None in now_users:
        #     now_users = list(filter(None, now_users))
        # if len(now_users) > 0:
        #     now_users_str = ("-=-").join(now_users)
        # return render_template('index.html', now_users_str = now_users_str)
        return redirect(url_for('index'))    

@app.route('/test')
def testPage():
    return render_template({"test":"1127000"})


@app.route('/groupPage')
def groupPageNoPara():
    return redirect(url_for('group'))

@app.route('/groupPage/<groupname>')
def groupPage(groupname):
    if 'username' in session and 'room' in session:
        username = session['username']
        room = str(session['room']) + "_" + str(groupname)
        return render_template('groupPage.html', username=username, room=room, groupname=groupname)
    else:
        # global now_users
        # if None in now_users:
        #     now_users = list(filter(None, now_users))
        # if len(now_users) > 0:
        #     now_users_str = ("-=-").join(now_users)
        # return render_template('index.html', now_users_str = now_users_str)
        return redirect(url_for('index'))



@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    online_user.append(username)


@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')


@socketio.on('send msg')
def handle_message(data):
    print('sendMsg: ' + str(data))
    room = session.get('room')
    data['message'] = data.get('message').replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;')
    msg_log = dict()
    room_split = data.get('room').split('_')
    msg_log["user"] = data.get('user')
    msg_log["msg"] = data['message']
    msg_log["isoTime"] = datetime.datetime.now(tz=tzone).isoformat()
    msg_log["time"] = datetime.datetime.now(tz=tzone)
    if data.get('room') == 'initial_room':
        msg_log["room"] = "全體聊天室"
        all_chat_collection.insert_one(msg_log)
    elif room_split[0] == "initial" and room_split[1] == "room":
        msg_log["room"] = room_split[2]
        group_chat_collection.insert_one(msg_log)
    else:
        msg_log["room"] = ""
        all_chat_collection.insert_one(msg_log)
    msg_log.clear()
    socketio.emit('send msg', data, to=data.get('room'))

@socketio.on('lock group info')
def handle_lock_group(data):
    group = data.get('group')
    grouping_log = dict()
    locked_group_log = dict()
    if all_simu_group_info[group][0] != "" or all_simu_group_info[group][1] != "" or all_simu_group_info[group][2] != "":
        locked_groups.append(group)
        room = session.get('room')
        locked_group_members = all_simu_group_info[group]
        for name in locked_group_members:
            if name == "":
                break
            else:
                all_members.pop(name)

        print(f"group {group} locked. member:{all_simu_group_info[group]}")
        grouping_log["group_Info"] = all_simu_group_info
        grouping_log["isoTime"] = datetime.datetime.now(tz=tzone).isoformat()
        grouping_log["time"] = datetime.datetime.now(tz=tzone)
        grouping_msg_collection.insert_one(grouping_log)
        locked_group_log["group"] = group
        locked_group_log['member'] = all_simu_group_info[group]
        locked_group_log["isoTime"] = datetime.datetime.now(tz=tzone).isoformat()
        locked_group_log["time"] = datetime.datetime.now(tz=tzone)
        locked_group_msg_collection.insert_one(locked_group_log)

        socketio.emit('lock group', data, to=room)

    

@socketio.on('group info')
def handle_group_info(data):
    username = data.get('username')
    simuNum = data.get('simuNum')
    group = data.get('group')
    room = session.get('room')
    if group in locked_groups:
        return
    if simuNum == 0:
        if list(all_members.keys()).count(username) == 0:
            position = check_group_position(data, simuNum)
            if position == -1:
                socketio.emit('group full', {"user":username}, to=room)
            else:
                all_simu_group_info[group][position] = username
                all_members[username] = group
                data["position"] = position

                socketio.emit('add new Member', data, to=room)
        elif all_members[username] != group:
            prev_group = all_members[username]
            prev_position = all_simu_group_info[prev_group].index(username)
            position = check_group_position(data, simuNum)
            if position == -1:
                socketio.emit('group full', {"user":username}, to=room)
            else:
                all_simu_group_info[group][position] = username
                all_simu_group_info[prev_group][prev_position] = ""
                all_members[username] = group
                data["position"] = position

                socketio.emit('delete group Member', {"simuNum":simuNum, "group":prev_group, "position":prev_position}, to=room)
                socketio.emit('add new Member', data, to=room)

@socketio.on('join')
def on_join(data):
    username = data.get('username')
    room = data.get('room')
    try:
        room_user[room].append(username)
    except:
        room_user[room] = []
        room_user[room].append(username)

    join_room(room)
    socketio.emit('connect info', username + '加入房間', to=room)


@socketio.on('leave')
def on_leave(data):
    username = data.get('username')
    room = data.get('room')
    room_user[room].remove(username)
    leave_room(room)
    socketio.emit('connect info', username + '離開房間', to=room)


if __name__ == '__main__':
    # socketio.run(app, host='0.0.0.0', port=5000)
    socketio.run(app, host='0.0.0.0', port=3080)

#ip:140.115.53.202
