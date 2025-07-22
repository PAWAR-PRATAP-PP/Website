from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from sqlalchemy import create_engine, text

app = Flask(__name__)


MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'Pawar'


def create_database(name,license_key):
    db_name = f"{name.strip().replace(' ', '').lower()}_{license_key.strip().lower()}"
    #db_name = f"Python_{license_key.strip().lower()}"
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    conn.commit()
    cursor.close()
    conn.close()
    return db_name


def initialize_schema(db_name):
    engine = create_engine(f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/adatsoft")
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS client_info (
            license_key INT(5)  PRIMARY KEY,
            name VARCHAR(100),
            mobile VARCHAR(15),
            email TEXT(25),
            address TEXT,
            pin_code VARCHAR(10),
            gst_number VARCHAR(20)
        )
        """))
        conn.commit()


def insert_client_data(db_name, data):
    engine = create_engine(f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/adatsoft")

    with engine.connect() as conn:
        
        result = conn.execute(text("SELECT 1 FROM client_info WHERE license_key = :license_key"), {'license_key': data['license_key']})
        existing = result.fetchone()
        if existing:
            return False  

        
        conn.execute(text("""
            INSERT INTO client_info (license_key, name, mobile, email, address, pin_code, gst_number)
            VALUES (:license_key, :name, :mobile, :email, :address, :pin_code, :gst_number)
        """), data)
        conn.commit()
        return True


from sqlalchemy import create_engine, text
'''
def user_create(data):
    engine = create_engine(f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/adatsoft")
    
    username = data['license_key']
    password = f"{data['name'].strip().replace(' ', '').lower()}@{data['license_key']}"

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO user (uname, pass)
            VALUES (:uname, :pass)
        """), {"uname": username, "pass": password})
        
        conn.commit()

'''



'''--------------------------------------------------------------------------------------------------------'''
'''Creating  Tables under the license no'''
def schema(db_name):
    engine = create_engine(f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{db_name}")
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user (
            license_key VARCHAR(255) PRIMARY KEY,
            uname VARCHAR(100),
            pass VARCHAR(100)
        )
        """))
        conn.commit()


def user_create(data,db_name):
    engine = create_engine(f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{db_name}")
    
    license_key= data['license_key']
    username = data['license_key']
    password = f"{data['name'].strip().replace(' ', '').lower()}@{data['license_key']}"

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO user (license_key,uname, pass)
            VALUES (:license_key,:uname, :pass)
        """), {"license_key":license_key,"uname": username, "pass": password})
        
        conn.commit()



@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        
        license_key = request.form.get('license_key')
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        gst_number = request.form.get('gst_number')

        
        if not all([license_key, name, mobile, email]):
            return render_template('register.html', error="Please fill in all required fields.")

        try:
            
            db_name = create_database(name, license_key)
            initialize_schema(db_name)
            schema(db_name)

           
            if not insert_client_data(db_name, {
                'license_key': license_key,
                'name': name,
                'mobile': mobile,
                'email': email,
                'address': address,
                'pin_code': pin_code,
                'gst_number': gst_number
            }):
                return render_template('register.html', error="License key already exists!")

            
            user_create({
                'license_key': license_key,
                'name': name,
                'mobile': mobile,
                'email': email,
                'address': address,
                'pin_code': pin_code,
                'gst_number': gst_number
            }, db_name)

            return f"Database '{db_name}' created and client info saved successfully."

        except Exception as e:
            return render_template('register.html', error=f"An error occurred: {str(e)}")

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)

