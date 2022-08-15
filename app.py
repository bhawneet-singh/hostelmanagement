from flask import Flask,request ,session , jsonify,send_from_directory,render_template
from flask_mail import Message,Mail
from flask_session import Session
import sys,sqlite3

app = Flask(__name__)

# setting up email
app.config["MAIL_DEFAULT_SENDER"] = "hostalmanagement@hotmail.com"
app.config["MAIL_PASSWORD"] = "hostal@123"
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp-mail.outlook.com"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "hostalmanagement@hotmail.com"
mail = Mail(app)

#configuration 
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#static
@app.route("/")
def ret():
    return render_template("index.html")


@app.route("/<path:path>")
def static_dir(path):
    print(path)
    return send_from_directory("static",path)


# api
db = "database2.db"
@app.route("/api/login/",methods=["POST"])
def api():
    json = request.json
    if json["rollno"] and json["password"]:
        with sqlite3.connect(db) as conn:
                command = "SELECT PASSWORD FROM STUDENT WHERE ROLLNO=?"
                result = list(conn.execute(command,(json["rollno"],)))
                if len(result) > 0 and str(result[0][0]) == json["password"]:
                    session["name"] = json["rollno"]
                    return "",200
    return "",401

@app.route("/api/adminlogin/",methods=["POST"])
def api_admin_login():
    json = request.json
    if json["email"] and json["password"]:
        with sqlite3.connect(db) as conn:
            command = "SELECT PASSWORD FROM SUPERUSER WHERE EMAIL=?"
            result = list(conn.execute(command,(json["email"],)))
            if len(result) > 0 and str(result[0][0]) == json["password"]:
                session["a_name"] = json["email"]
                return "",200
    return "",401


@app.route("/api/logout/",methods=["POST"])
def greet():
    session["name"] = None
    return "",200


@app.route("/api/admin/logout/")
def admin_out():
    session["a_name"] = None
    return "",200


@app.route("/api/student/")
def api_home():
    if not session.get("name"):
        return "",307

    with sqlite3.connect(db) as conn:
        command = "SELECT NAME,FATHER,MOTHER,EMAIL,PHONE,DOB,PRIFILE_PHOTO,ROLLNO,MESHBILL,ADDRESS FROM STUDENT WHERE ROLLNO=?"
        result = list(conn.execute(command,(session["name"],)))[0]
    return jsonify({"name":result[0] , "father_name" : result[1],
                    "mother_name":result[2],"email":result[3],"phone":result[4],"dob":result[5],"file":result[6],"rollno":result[7],"bill":result[8],"address":result[9]})


@app.route("/api/admin/")
def api_admin():
    if session.get("a_name"):
        with sqlite3.connect(db) as conn:
            command = f"SELECT NAME,FATHER,MOTHER,EMAIL,PHONE,ROLLNO,MESHBILL,DOB,ADDRESS FROM STUDENT WHERE {request.args.get('key')} LIKE '%{request.args.get('value')}%' ORDER BY {request.args.get('key')};"
            result = conn.execute(command)
        return jsonify([ { "name":line[0],"father":line[1],"mother":line[2],"email":line[3],"phone":line[4],"rollno":line[5],"bill":line[6]} for line in result]) 
    return "",401


@app.route("/api/signup/session/")
def signup_session():
    if session.get("number"):
        return "",200
    return "",401


@app.route("/api/signup/data/",methods=["POST"])
def api_sigup():
    json = request.json
    if validate_user(json):
        with sqlite3.connect(db) as conn:
            command = "INSERT INTO STUDENT ( NAME,FATHER,MOTHER,EMAIL,PHONE,DOB,PRIFILE_PHOTO,ROLLNO,ADDRESS,PASSWORD ) VALUES(?,?,?,?,?,?,?,?,?,?)"
            conn.execute(command,(json["name"].title(),json["father_name"].title(),json["mother_name"].title(),json["email"],json["phone"],json["dob"],json["file"],session["number"],json["address"],json["password"]))
            conn.commit()
            session["number"] = None
            return "",200
    return "",404


@app.route("/api/admin/roll",methods=["GET"])
def rollno():
    if session.get("a_name"):
        if request.args.get("number"):
            with sqlite3.connect(db) as conn:
                command = "INSERT INTO ROLLNO VALUES(?);"
                conn.execute(command,(request.args.get("number"),))
                conn.commit()
        with sqlite3.connect(db) as conn:
            command = "SELECT * FROM ROLLNO;"
            result = list(conn.execute(command));
        return jsonify([{"number":line[0]} for line in result])
    return "",401


@app.route("/api/varify")
def varify():
    number = request.args.get("roll")
    session["number"] = number
    if number:
        with sqlite3.connect(db) as conn:
            command = "SELECT * FROM ROLLNO WHERE ROLLNO=?"
            result = list(conn.execute(command,(number,)))
            command = "SELECT * FROM STUDENT WHERE ROLLNO=?"
            result2 = list(conn.execute(command,(number,)))
            if len(result) > 0 and len(result2) == 0:
                return "",200
    return "",401


@app.route("/api/add")
def add_bill():
    bill = request.args.get("amount")
    rollno = request.args.get("rollno")
    if bill and rollno and session.get("a_name"):
        with sqlite3.connect(db) as conn:
            command = "UPDATE STUDENT SET MESHBILL=? WHERE ROLLNO=?;"
            conn.execute(command,(bill,rollno,))
            conn.commit()
            return "",200
    return "",404

@app.route("/api/send/")
def send_email():
    address = request.args.get("address")
    amount = request.args.get("amount")
    nofication =f"""<h1>Mesh Bill</h1>
    <p>Dear student, your mess bill for this mounth is ₹{amount}.Please pay before the due date.<p>
    <pre>
    Best regards
    supriya adhikari
    bhawneet singh</pre>
    """
    if address and session.get("a_name"):
        msg = Message("mesh bill notification",html=nofication,recipients=[address])
        mail.send(msg) 
        return "",200
    return "",401

def validate_user(json):
    return json["name"] and json["father_name"] and json["mother_name"] and json["email"] and json["phone"] and json["dob"] and json["address"] and json["file"] and json["password"]


if __name__ == "__main__":   
    if sys.argv[1] == "--createsuperuser":
        with sqlite3.connect(db) as conn:
            try:
                command = "CREATE TABLE IF NOT EXISTS SUPERUSER(EMAIL VARCHAR(255) PRIMARY KEY NOT NULL,PASSWORD INTEGER NOT NULL );"
                conn.execute(command)
                email = input("enter a email : ")
                password = input("create a password : ")
                c_password = input("confirm the same password : ")
                if not password == c_password:
                    print("password mismatch !")
                    sys.exit(1)
                command = "INSERT INTO SUPERUSER VALUES (?,?)"
                conn.execute(command,(email,password))
                conn.commit()
                print("super user create success !")
            except sqlite3.IntegrityError:
                print("email already exist !")
