from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



load_dotenv()  # Load environment variables from .env

app = Flask(__name__) 
CORS(app) 

# MySQL configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

# Application Configuration
app_config = {
    'APP_URL': os.getenv('APP_URL'),
    'API_KEY': os.getenv('API_KEY'),
    'API_SECRET': os.getenv('API_SECRET'),
    'SECRET_KEY': os.getenv('SECRET_KEY')
}

mysql = MySQL(app)
 
@app.route('/testdb')
def test_db():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        return "DB Connected!"
    except Exception as e:
        return {"error": str(e)},400 
    

@app.route('/',methods=['GET'])
def home():
    data={"message":"welcome to react-world","name":"shirish"}
    return jsonify(data),200
    
# User signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')  #shirish
    email=data.get('email')
    password = data.get('password')
    
    hashed_password = generate_password_hash(password)
    print(email)
    #check if that user already exists or username  is already taken .............. then need to  create new user
    
    cursor1=mysql.connection.cursor()                                 
    cursor1.execute('SELECT username FROM users where username = %s',(username,))
    user=cursor1.fetchone()
    cursor1.close()
    print(user)
    if user!=None:
        return jsonify(message=" That user already exists.\nPlease click the login button")
    
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO users (username , password , org_password, email) VALUES (%s, %s ,%s, %s)', (username, hashed_password,password,email))
    mysql.connection.commit()
    cursor.close()

    return jsonify(message="User created successfully"), 200

# User login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        reg_password = data.get('password')
        
        # check for  authentication
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT username FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        print(user) 
        if user is None:
            return jsonify(message="User not found"), 200
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT org_password FROM users WHERE username = %s', (username,))
        passw = cursor.fetchone()
        cursor.close()
        print(passw[0]) 
        print(reg_password)
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT chk FROM users WHERE username = %s', (username,))
        ck = cursor.fetchone()
        cursor.close()
        print(ck)
        if user is not None and passw[0]==reg_password and ck[0]==0:
            cur=mysql.connection.cursor()
            cur.execute('update users set chk=1 where username = %s',(username,))
            mysql.connection.commit()
            cur.close()
            return jsonify(message="Login successful",cc="0"), 200
        elif user is not None and passw[0]==reg_password and ck[0]==1:
            return jsonify(message="Login successful",cc="1"), 200
        else:
            return jsonify(message="Incorrect ID or Pass"),400
    except Exception as e:
        return jsonify(message="Failed to LOgin", error=str(e)), 500
        

#complain  email
@app.route('/complain_box',methods=['POST'])
def complain_box():
    data=request.json
    quality=data.get('quality')                    #excellent good poor
    star=data.get('star')
    suggestion=data.get('suggestion')
    
    #details of sender and reciever  
    sender_email =  os.getenv('sender_m') 
    sender_password = os.getenv('sender_p')     
    subject = "Feedback and suggestions"
    recipient_email = 'rccremp@gmail.com'
    
    data_want_send=MIMEMultipart()
    data_want_send['From']=sender_email
    data_want_send['To']=recipient_email
    data_want_send['subject']=subject
    body=f"Feedback from anonymous customer is : \n Your app quality is :{quality} \n Anonymous person given you {star} stars \n Suggestion from Anonymous person is {suggestion} \n Thank you."
    data_want_send.attach(MIMEText(body,'plain'))
    
    
    try:
        # Connect to the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587) 
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, data_want_send.as_string())
        server.close()
        return jsonify(message="Email has been sent to registered email"), 200
    except Exception as e:
        return jsonify(message="Failed to send email. Please try again later.", error=str(e)), 500
    
    
    
    
# forget password
@app.route('/forget_pass',methods=['POST'])
def forget_pass():
    data=request.json
    print(data)
    email=data.get('email')
    print(email)
    
    cursor=mysql.connection.cursor()
    cursor.execute('Select org_password from users where email = %s',(email,))
    user_curr_pass=cursor.fetchone()
    cursor.close()
    
    print(user_curr_pass)
    
    if user_curr_pass!=None:
        org_password = user_curr_pass[0]
        
        # Email sending logic
        sender_email = os.getenv('sender_m')   # Replace with your email
        sender_password = os.getenv('sender_p')    # Replace with your email password
        subject = "Your Password Recovery Request"
        recipient_email = email 
        
        # Create email content
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] =  recipient_email
        message['Subject'] = subject
        body = f"Dear User,\n\nYour password is: {org_password}\n\nRegards,\nSupport Team"
        message.attach(MIMEText(body, 'plain'))
        
        try:
            # Connect to the SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)  # Use appropriate SMTP server and port
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
            server.close()
            return jsonify(message="Email has been sent to registered email"), 200
        except Exception as e:
            return jsonify(message="Failed to send email. Please try again later.", error=str(e)), 500
    else:
        return jsonify(message="mail id is not registered")
    
@app.route('/update_pass',methods=['POST'])
def update_pass():
    data=request.json
    password=data.get('password')
    confirm_password=data.get('confirm_password')
    username=data.get('username')
    if username is None:
        return jsonify(message="username is mandotry"),400
    if password!=confirm_password:
        return jsonify(message="password not meet"),400
    cursor=mysql.connection.cursor()
    cursor.execute('update users set org_password = %s where username = %s',(password,username,))
    mysql.connection.commit()
    cursor.close()
    
    return jsonify(message="password updated succssfully"),200
 
 
@app.route('/rooms',methods=['GET'])            
def get_room_detail():
    cursor=mysql.connection.cursor()
    cursor.execute('Select * from rooms')
    room=cursor.fetchall()
    cursor.close()
    
    print(room)
    room_list=[]
    
    for i in room:
        room_list.append({
            "room_no":i[0],
            "status":i[1],
            "price":i[2]
        })
        
    return jsonify(message="room details are",rooms=room_list)
    
@app.route('/rooms/booked',methods=['GET'])
def get_book_room():
    cursor=mysql.connection.cursor()
    cursor.execute('select * from rooms where status = %s',('occupied',))
    room=cursor.fetchall()
    cursor.close()
    
    print(room)
    room_list=[]
    
    for i in room:
        room_list.append({
            "room_no":i[0],
            "status":i[1],
            "price":i[2]
        })
        
    return jsonify(message="all booked rooms are:",rooms=room_list,count=len(room_list))

@app.route('/rooms/vacant',methods=['GET'])
def get_vacant_room():
    cursor=mysql.connection.cursor()
    cursor.execute('select * from rooms where status = %s',('Vacant',))
    room=cursor.fetchall()
    cursor.close()
    
    print(room)
    room_list=[]
    
    for i in room:
        room_list.append({
            "room_no":i[0],
            "status":i[1],
            "price":i[2]
        })
        
    return jsonify(message="all available rooms are:",rooms=room_list,count=len(room_list))
   
@app.route('/rooms/add',methods=['POST'])
def add_room():
    data = request.json
    room_number = data.get('room_no')
    price = data.get('price')

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO rooms (room_id, status, price) VALUES (%s, 'vacant', %s)", (room_number, price))
    mysql.connection.commit()
    cursor.close()

    return jsonify(message="Room added successfully"), 200
    

@app.route('/getcoroom',methods=['GET'])
def get_co_room():
    cursor=mysql.connection.cursor()
    cursor.execute('select count(*) from rooms')
    count=cursor.fetchone()
    cursor.close()
    
    print(count)
    return jsonify(message="total count is:",count=count[0]),200

@app.route('/rooms/book',methods=['POST'])
def book_room():
    data=request.json
    room_no=data.get('room_no')
    
    cursor = mysql.connection.cursor()
    cursor.execute("update rooms set status = %s where room_id =%s ",('occupied',room_no,))
    mysql.connection.commit()
    cursor.close()
    
    return jsonify(message="room booked successfully"),200


#

@app.route('/rooms/delete',methods=['POST'])
def del_room():
    data=request.json
    room_no=data.get('room_no')
    
    cursor = mysql.connection.cursor()
    cursor.execute("update rooms set status = %s where room_id =%s ",('Vacant',room_no,))
    mysql.connection.commit()
    cursor.close()
    
    return jsonify(message="room successfully deleted"),200
    
@app.route('/admins', methods=['POST'])
def admins():
    print("Enter")
    data=request.json
    print("printdar",data)
    username=data.get('username')
    admin_pass=data.get('pass')
    email=data.get('email')

    cursor2 =mysql.connection.cursor()
    cursor2.execute('select username from adminlogin where username = %s',(username,))
    user=cursor2.fetchone()
    cursor2.close()
    print(user,"user is")
    if user !=None:
        return jsonify(message="username is already exist"),200
    
    cursor3=mysql.connection.cursor()
    cursor3.execute('INSERT INTO adminlogin (username , pass , email) VALUES (%s,%s, %s)', (username,admin_pass,email))
    mysql.connection.commit()
    cursor3.close()
    return jsonify(message='user created successfully'),200


@app.route('/admin_lgn',methods=['POST'])
def admin_lgn():
    data=request.json
    username=data.get('username')
    apas=data.get('pass')
    


    cursor=mysql.connection.cursor()
    cursor.execute('select username from adminlogin where username = %s',(username,))
    user=cursor.fetchone()
    cursor.close()
    print(user)
    if user is None:
        return jsonify(message='user not exist')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT pass FROM adminlogin WHERE username = %s', (username,))
    passw = cursor.fetchone()
    cursor.close()
    print(passw[0]) 
    if user is not None and passw[0]==apas:
        return jsonify(message="Login successful"), 200
    else:
        return jsonify(message="Incorrect ID or Pass"),400
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

