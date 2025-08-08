import datetime
from functools import wraps
import io
import os
import PyPDF2
from flask import Flask, Response, json, jsonify, render_template, render_template_string, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, session
import requests
import json
from sqlalchemy import text
from collections import defaultdict
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt





app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Upload Config
UPLOAD_FOLDER = 'b'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Pawar@localhost/adatsoft'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(80), unique=True, nullable=False)
    _pass = db.Column('pass', db.String(128), nullable=False)

    def set_password(self, password):
        self._pass = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self._pass, password)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), db.ForeignKey('user.uname'), nullable=False)

class Bill(db.Model):
    __tablename__ = 'bill'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bill_no = db.Column(db.Integer, unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    from_location = db.Column(db.String(100), nullable=False)
    to_location = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    vehicle_no = db.Column(db.String(50), nullable=False)
    discount = db.Column(db.Float, default=0)
    labor_charges = db.Column(db.Float, default=0)
    bill_amount = db.Column(db.Float, default=0)
    grand_total = db.Column(db.Float, default=0)

    # Relationship to BillItem, referencing the primary key 'id' of Bill
    items = db.relationship(
        'BillItem',
        backref='bill',
        cascade='all, delete-orphan',
        passive_deletes=True
    )


class BillItem(db.Model):
    __tablename__ = 'bill_item'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bill_id = db.Column(
        db.Integer,
        db.ForeignKey('bill.id', ondelete='CASCADE'),
        nullable=False
    )
    item_name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(30), nullable=False)
    qty = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)

class Customer(db.Model):
    acno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)

# Create tables
with app.app_context():
    db.create_all()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('⚠️ You must be logged in.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html', username=session['username'])

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', username=session['username'])

@app.route('/projects')
@login_required
def projects():
    resumes = Resume.query.filter_by(username=session['username']).all()
    return render_template('projects.html', username=session['username'], resumes=resumes)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', username=session['username'])

@app.route('/cust-list')
def cust_lst():
    customers = Customer.query.all()
    return render_template('custLst.html', customers=customers)

@app.route('/add-cust', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone')

        if Customer.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('add_customer'))

        new_customer = Customer(name=name, email=email, phone=phone)
        db.session.add(new_customer)
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('cust_lst'))

    
    return render_template('masterSetup.html',username=session['username'])

@app.route('/edit/<int:cust_id>', methods=['GET', 'POST'])
def edit_customer(cust_id):
    customer = Customer.query.get_or_404(cust_id)

    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        db.session.commit()
        return redirect(url_for('cust_lst'))

    return render_template('masterSetup.html', customer=customer)


@app.route('/chat_bot')
def chat_bot():
    ip_address = "http://192.168.1.75:5001"
    return render_template_string('''
        <button id="open-ip">Open IP Address</button>
        <script>
            const ipAddress = "{{ ip }}";
            document.getElementById('open-ip').addEventListener('click', function() {
                window.open(ipAddress, '_blank');
            });
        </script>
    ''', ip=ip_address)

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():

    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('⚠️ No file part found.')
            return render_template('projects.html', username=session['username'])

        file = request.files['resume']

        if file.filename == '':
            flash('⚠️ No selected file.')
            return render_template('projects.html', username=session['username'])
        
        UPLOAD_FOLDER = r"D:\\website\\uploads" 
        file_name = file.filename
        save_path = os.path.join(UPLOAD_FOLDER, file.filename)
        if os.path.exists(save_path):
            os.remove(save_path)
        file.save(save_path)
        file_name = save_path
        data = {
            'file_path': file_name,
            'rrfid': '07a5252b-b0f7-4660-8854-6ead4154b70e'
        }

        response = requests.post(
            "http://127.0.0.1:5000/resume_parser",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data)
        )

        try:
            response.raise_for_status()
            parsed_data = response.json()
            return render_template('ResumeDtl.html', data=parsed_data)

        except requests.exceptions.RequestException as e:
            return f"An error occurred: {e}"
        
@app.route('/resume_parser')
@login_required
def resume_parser():
    return render_template('ResumeParse.html', username=session['username'])

@app.route('/transport')
@login_required
def transport():
    return render_template('Trasport.html', username=session['username'])


@app.route('/today_customer_chart')
@login_required
def today_customer_chart():
    today = datetime.today().date()

    result = (
        db.session.query(
            Bill.customer_name,
            db.func.sum(Bill.grand_total).label('total_amount')
        )
        .filter(Bill.date == today)
        .group_by(Bill.customer_name)
        .all()
    )
    
    customers = [row.customer_name for row in result]
    amounts = [row.total_amount for row in result]

    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(customers, amounts, color='mediumslateblue', edgecolor='black', alpha=0.8)
    
    
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),  
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9,
                    color='black')
    
    ax.set_title("Today's Customer-wise Billing", fontsize=16, fontweight='bold', color='darkblue')
    ax.set_ylabel('Bill Amount', fontsize=12)
    ax.set_xlabel('Customers', fontsize=12)
    
    ax.set_xticks(range(len(customers)))
    ax.set_xticklabels(customers, rotation=45, ha='right', fontsize=10)

    
    
    fig.tight_layout()
    
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', facecolor='whitesmoke')
    img.seek(0)
    plt.close(fig)

    return Response(img.getvalue(), mimetype='image/png')



@app.route('/vehicle_chart')
@login_required
def vehicle_chart():
    today = datetime.today().date()

    result = (
        db.session.query(
            Bill.vehicle_no,
            db.func.sum(Bill.grand_total).label('total_amount')
        )
        .filter(Bill.date == today)
        .group_by(Bill.vehicle_no)
        .all()
    )
  
    vehicles = [row.vehicle_no for row in result]
    amounts = [row.total_amount for row in result]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(vehicles, amounts, color='mediumslateblue', edgecolor='black', alpha=0.8)

    ax.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9,
                    color='black')

    ax.set_title("Today's Vehicle-wise Billing", fontsize=16, fontweight='bold', color='darkblue')
    ax.set_ylabel('Total Freight', fontsize=12)
    ax.set_xlabel('Vehicles', fontsize=12)

    ax.set_xticks(range(len(vehicles)))  
    ax.set_xticklabels(vehicles, rotation=45, ha='right', fontsize=10)

    fig.tight_layout()

    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', facecolor='whitesmoke')
    img.seek(0)
    plt.close(fig)

    return Response(img.getvalue(), mimetype='image/png')



def get_next_billno():
    last_bill = (
        db.session.query(Bill)
        .order_by(Bill.bill_no.desc())
        .first()
    )

    try:
        next_number = int(last_bill.bill_no) + 1 if last_bill and str(last_bill.bill_no).isdigit() else 1
    except ValueError:
        next_number = 1

    return f"{next_number:05d}"

@app.route('/check_customer', methods=['POST'])
def check_customer():
    data = request.get_json()
    customer_name = data.get('customer_name')
    customer = Customer.query.filter_by(name=customer_name).first()
    return jsonify({'exists': bool(customer)})

@app.route('/check_location', methods=['POST'])
def check_location():
    data = request.get_json()
    location = data.get('location')  

    
    location = db.session.execute(
        text("SELECT 1 FROM locmst WHERE LOCNDESC = :location"),
        {"location": location}
    ).fetchone()

    return jsonify({'exists': bool(location)})

# @app.route('/check_item', methods=['POST'])
# def check_item():
#     data = request.get_json()
#     item_name = data.get('item_name')  

    
#     item = db.session.execute(
#         text("SELECT 1 FROM prodct WHERE item_name = :item_name"),
#         {"item_name": item_name}
#     ).fetchone()

#     return jsonify({'exists': bool(item)})

@app.route('/add-bill', methods=['GET', 'POST'])
@login_required
def add_bill():
    customers = Customer.query.order_by(Customer.name).all()
    locmst=db.session.execute(text("SELECT * FROM locmst ORDER BY ID")).fetchall()
    veh=db.session.execute(text("SELECT * FROM vehicle")).fetchall()
    product=db.session.execute(text("SELECT * FROM prodct")).fetchall()
    if request.method == 'POST':
        try:
            bill_no = request.form['bill_no']
            customer_name = request.form['customer_name']
            #locmst=request.form['from_location']
            # if customer_name:
            #     customer = db.session.execute(
            #         text("SELECT acno FROM Customer WHERE name=:customer_name"),
            #         {"customer_name": customer_name}
            #     ).fetchall()
            #     customer=str(customer)
            bill = Bill(
                id=bill_no,
                bill_no=bill_no,
                date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
                from_location=request.form['from_location'],
                to_location=request.form['to_location'],
                customer_name=customer_name,                    
                vehicle_no=request.form['vehicle_no'],
                discount=float(request.form.get('discount') or 0),
                labor_charges=float(request.form.get('labor_charges') or 0),
                bill_amount=float(request.form.get('bill_amount') or 0),
                grand_total=float(request.form.get('grand_total') or 0),
            )
            
            db.session.add(bill)
            db.session.flush()

            item_names = request.form.getlist('item_name[]')
            units = request.form.getlist('unit[]')
            qtys = request.form.getlist('qty[]')
            rates = request.form.getlist('rate[]')
            amounts = request.form.getlist('amount[]')

            last_item = db.session.query(BillItem).order_by(BillItem.id.desc()).first()
            next_id = 1 if not last_item else last_item.id + 1

            for i in range(len(item_names)):
                item = BillItem(
                    id=next_id,
                    bill_id=bill.id,
                    item_name=item_names[i],
                    unit=units[i],
                    qty=float(qtys[i]),
                    rate=float(rates[i]),
                    amount=float(amounts[i])
                )
                db.session.add(item)
                next_id += 1

            db.session.commit()
            flash("Bill saved successfully!", "success")
            return redirect(url_for('add_bill'))

        except Exception as e:
            db.session.rollback()
            return f"An error occurred: {str(e)}", 400


    return render_template(
        'bill_entry.html',
        bill_no=get_next_billno(),
        today=datetime.now().strftime('%Y-%m-%d'),
        username=session['username'],
        customers=customers,
        locmst=locmst,
        veh=veh,
        product=product
    )

@app.route('/bills')
@login_required
def list_bills():
    customer_query = request.args.get('customer', '', type=str).strip()

    query = Bill.query
    if customer_query:
        query = query.filter(Bill.customer_name.ilike(f"%{customer_query}%"))

    bills = query.order_by(Bill.bill_no.desc()).all()  

    return render_template('bill_list.html', bills=bills, search_query=customer_query,username=session['username'])


@app.route('/edit_bill/<bill_no>', methods=['GET', 'POST'])
@login_required
def edit_bill(bill_no):
    if 'username' not in session:
        return redirect(url_for('login'))
    bill = Bill.query.filter_by(bill_no=bill_no).first_or_404()
    customers = Customer.query.order_by(Customer.name).all()
    product=db.session.execute(text("SELECT * FROM prodct")).fetchall()
    if request.method == 'POST':
        bill.date = request.form['date']
        bill.from_location = request.form['from_location']
        bill.to_location = request.form['to_location']
        bill.customer_name = request.form['customer_name']
        bill.vehicle_no = request.form['vehicle_no']
        bill.discount = float(request.form.get('discount', 0) or 0)
        bill.labor_charges = float(request.form.get('labor_charges', 0) or 0)
        bill.bill_amount = float(request.form.get('bill_amount', 0) or 0)
        bill.grand_total = float(request.form.get('grand_total', 0) or 0)

        # Get items data from form
        item_ids = request.form.getlist('item_id[]')
        item_names = request.form.getlist('item_name[]')
        units = request.form.getlist('unit[]')
        qtys = request.form.getlist('qty[]')
        rates = request.form.getlist('rate[]')
        amounts = request.form.getlist('amount[]')

        

        submitted_item_ids = []

        for item_id, name, unit, qty, rate, amount in zip(item_ids, item_names, units, qtys, rates, amounts):
            try:
                if item_id and item_id.strip() != '0':
                    #item = BillItem.query.get(int(item_id))
                    item = db.session.get(BillItem, int(item_id)) 
                    if item and item.bill_id == bill.id:
                        
                        item.item_name = name
                        item.unit = unit
                        item.qty = int(float(qty))
                        item.rate = float(rate)
                        item.amount = float(amount)
                        submitted_item_ids.append(item.id)
                else:
                   
                    new_item = BillItem(
                        bill_id=bill.id,
                        item_name=name,
                        unit=unit,
                        qty=int(qty),
                        rate=float(rate),
                        amount=float(amount)
                    )
                    db.session.add(new_item)
                    db.session.commit()
            except ValueError as e:
                print(f"Error parsing item data: {e}")

        

        db.session.commit()
        flash(f'Bill {bill_no} Updated successfully.', 'success')
        return redirect(url_for('add_bill'))

    # GET request - show form
    items = BillItem.query.filter_by(bill_id=bill.id).all()
    return render_template(
    'bill_entry.html',
    bill=bill,
    items=items,
    edit_mode=True,
    username=session['username'],
    customers=customers,
    product=product
)




@app.route('/delete-bill/<bill_no>', methods=['POST'])
def delete_bill(bill_no):
    if 'username' not in session:
        return redirect(url_for('login'))
    bill = Bill.query.filter_by(bill_no=bill_no).first()
    if bill:
        db.session.delete(bill)
        db.session.commit()
        flash(f'Bill {bill_no} deleted successfully.', 'success')
    else:
        flash('Bill not found.', 'error')
    return redirect(url_for('list_bills'))

@app.route('/vehicle-report')
@login_required
def vehicle_report():

    vehicle_data = (
        db.session.query(
            Bill.vehicle_no,
            db.func.count(Bill.bill_no).label('total_bills'),
            db.func.sum(Bill.grand_total).label('total_amount')
        )
        .group_by(Bill.vehicle_no)
        .all()
    )

    return render_template('vehicleReport.html', vehicle_data=vehicle_data,username=session['username'])




@app.route('/veh-cust-repo')
def vehicle_cust_repo():
    today = datetime.today().strftime('%Y-%m-%d')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    veh_no = request.args.get('veh_no')  
    grouped_data = defaultdict(list)

    if start_date and end_date:
        try:
            if veh_no:
                
                # query = text("""
                #     SELECT bill_no, vehicle_no, customer_name, grand_total, `date` AS bill_date
                #     FROM bill
                #     WHERE `date` BETWEEN :start_date AND :end_date
                #     AND vehicle_no = :veh_no
                #     ORDER BY vehicle_no
                # """)
                query = text("""
                                SELECT 
                                    b.bill_no, 
                                    b.vehicle_no, 
                                    b.customer_name, 
                                    b.grand_total, 
                                    b.`date` AS bill_date,
                                    SUM(bi.qty) AS total_qty
                                FROM bill b
                                JOIN bill_item bi ON b.bill_no = bi.bill_id
                                WHERE b.`date` BETWEEN :start_date AND :end_date
                                AND b.vehicle_no = :veh_no
                                GROUP BY b.bill_no, b.vehicle_no, b.customer_name, b.grand_total, b.`date`
                                ORDER BY b.vehicle_no
                            """)

                params = {
                    'start_date': start_date,
                    'end_date': end_date,
                    'veh_no': veh_no
                }
            else:
                
                # query = text("""
                #     SELECT bill_no, vehicle_no, customer_name, grand_total, `date` AS bill_date
                #     FROM bill
                #     WHERE `date` BETWEEN :start_date AND :end_date
                #     ORDER BY vehicle_no
                # """)
                query = text("""
                                SELECT 
                                    b.bill_no, 
                                    b.vehicle_no, 
                                    b.customer_name, 
                                    b.grand_total, 
                                    b.`date` AS bill_date,
                                    SUM(bi.qty) AS total_qty
                                FROM bill b
                                JOIN bill_item bi ON b.bill_no = bi.bill_id
                                WHERE b.`date` BETWEEN :start_date AND :end_date
                                GROUP BY b.bill_no, b.vehicle_no, b.customer_name, b.grand_total, b.`date`
                                ORDER BY b.vehicle_no
                            """)

                params = {
                    'start_date': start_date,
                    'end_date': end_date
                }

            vehicle_bills = db.session.execute(query, params).fetchall()

            for row in vehicle_bills:
                grouped_data[row.vehicle_no].append({
                    'bill_no':row.bill_no,
                    'customer_name': row.customer_name,
                    'grand_total': row.grand_total,
                    'date': row.bill_date,
                    'total_qty': row.total_qty
                })

        except ValueError as e:
            print(f"Date parsing error: {e}")

    return render_template('vehicle_cust_repo.html', today=today, grouped_data=grouped_data,username=session['username'])






@app.route('/Face_Reco')
def Face_Reco():
    return render_template('ResumeParse.html', username=session['username'])


@app.route('/claim_extract', methods=['GET', 'POST'])
def claim_extract():
    if request.method == 'POST':
        user_text = request.form.get('text')
    else:  
        user_text = request.args.get('text')

    if user_text:
        data = {'value': user_text}
        try:
            response = requests.post(
                "http://127.0.0.1:5000/claim_expenses",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(data)
            )
            response.raise_for_status()
            parsed_data = response.json()
            return render_template('ClaimDtl.html', data=parsed_data)

        except requests.exceptions.RequestException as e:
            return f"An error occurred: {e}"


    return render_template('Claim.html', username=session.get('username'))







@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #license_key=request.form.get('license_key')
        user_input = request.form.get('username')
        pwd = request.form.get('password')

        if not user_input or not pwd:
            flash('⚠️ Please fill in both fields.')
            return redirect(url_for('login'))

        user = User.query.filter_by(uname=user_input).first()
        if user and user.check_password(pwd):
            session['username'] = user.uname
            return redirect(url_for('home'))
        else:
            flash('❌ Invalid credentials.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        
        user_input = request.form.get('username')
        pwd = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if not user_input or not pwd or not confirm:
            flash('⚠️ Please fill in all fields.')
            return redirect(url_for('signup'))

        if User.query.filter_by(uname=user_input).first():
            flash('Username already exists.')
            return redirect(url_for('signup'))

        if pwd != confirm:
            flash('Passwords do not match.')
            return redirect(url_for('signup'))

        new_user = User(uname=user_input)
        new_user.set_password(pwd)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
        if not username:
            flash('Please enter your Username.')
            return redirect(url_for('forgot_password'))
        user = User.query.filter_by(uname=username).first()

        if not user:
            flash('Username not found.')
            return redirect(url_for('forgot_password'))
        elif not password:
            flash('Passwod not found.')
            return redirect(url_for('forgot_password'))
        elif password!=cpassword:
            flash('Confirm Passwod.')
            return redirect(url_for('forgot_password'))
        
        user._pass = generate_password_hash(password)
        db.session.commit()

        flash('Password updated successfully. Please log in.')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')



if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5002)
