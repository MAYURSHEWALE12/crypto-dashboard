from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
from utils import get_current_prices
from bs4 import BeautifulSoup
from functools import wraps  # To create @admin_required decorator
from datetime import datetime
from flask_migrate import Migrate
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from werkzeug.utils import secure_filename
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/news_images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

# Etherscan API Key
ETHERSCAN_API_KEY = 'YNNXWK7EQQ4RKVQVB8DWKJ3837P7ZGUA58'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Add the is_admin field

    def __repr__(self):
        return f'<User {self.username}>'

#Define Models (if not imported from another file)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(120), nullable=True)  # Store image filename
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)



# Portfolio model
class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coin_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Home page
@app.route('/')
def index():
    try:
        response = requests.get('https://api.coingecko.com/api/v3/coins/markets', params={
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 10,#number of coins you want to
            'page': 1,
            'sparkline': False
        })

        if response.status_code == 200:
            coin_data = response.json()
            if not coin_data:
                error_message = "No data available at the moment. Please try again later."
                return render_template('index.html', coin_data=[], error_message=error_message)
        else:
            error_message = f"API Error: {response.status_code}. Please try again later."
            return render_template('index.html', coin_data=[], error_message=error_message)

    except Exception as e:
        print(f"Error: {e}")
        error_message = "An unexpected error occurred. Please try again later."
        return render_template('index.html', coin_data=[], error_message=error_message)

    return render_template('index.html', coin_data=coin_data)






#get available coins
def get_available_coins():
    try:
        response = requests.get('https://api.coingecko.com/api/v3/coins/list')
        response.raise_for_status()
        return response.json()  # Returns a list of coin dictionaries
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return []

# Function to get coin data from an API
def get_coin_data():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
    response = requests.get(url)
    data = response.json()
    print(data)  # Add this line to see the API response
    return data

#get current prices of coins 
def get_current_prices():
    # Example return value
    return {
        'bitcoin': 69000,
        'ethereum': 3000,
        'binancecoin' :200
        # Add other coins...
    }

#function to get current price 

def get_current_prices():
    # Example API call to get prices for multiple coins
    response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,litecoin&vs_currencies=usd')
    if response.status_code == 200:
        return response.json()  # Returns a dictionary with coin prices
    return {}




# login / logut and profile management
# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:  # You should hash passwords in production!
            login_user(user)
            return redirect(url_for('portfolio'))
        else:
            flash('Login failed. Check your email and password.')
    return render_template('login.html')

# Route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# forget password
@app.route('/change_password', methods=['POST'])
@login_required  # Ensure user is logged in
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_new_password = request.form['confirm_new_password']

    # Get the current user's ID (assuming you have session management)
    user_id = session.get('user_id')
    user = get_user_by_id(user_id)  # Fetch user from the database

    # Check if current password is correct
    if not check_password_hash(user.password, current_password):
        flash('Current password is incorrect!', 'danger')
        return redirect(url_for('profile'))  # Redirect to profile page

    # Check if new passwords match
    if new_password != confirm_new_password:
        flash('New passwords do not match!', 'danger')
        return redirect(url_for('profile'))

    # Update the password in the database
    user.password = generate_password_hash(new_password)
    update_user(user)  # Function to update user in the database

    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile'))

# Route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')  # Ensure this is being captured
        password = request.form.get('password')
        
        # Check if the email is valid and not already taken
        if User.query.filter_by(email=email).first():
            flash('Email is already in use. Please choose a different one.')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for portfolio
@app.route('/portfolio', methods=['GET'])
@login_required
def portfolio():
    coin_prices = get_current_prices()  # Fetch current prices

    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    total_profit_loss = 0
    total_balance = 0
    portfolio_data = []

    for portfolio in portfolios:
        current_price = coin_prices.get(portfolio.coin_name, {'usd': 0})['usd']
        profit_loss = (current_price - portfolio.purchase_price) * portfolio.amount
        total_profit_loss += profit_loss
        total_balance += current_price * portfolio.amount

        portfolio_data.append({
            'coin': portfolio.coin_name,
            'quantity': portfolio.amount,
            'current_price': current_price,
            'profit_loss': profit_loss,
        })

    # Calculate 24h change (you can adjust logic as needed)
    change_24h = 0.0  # Placeholder

    return render_template(
        'portfolio.html',
        portfolio_data=portfolio_data,
        total_profit_loss=total_profit_loss,
        total_balance=total_balance,
        change_24h=change_24h
    )

# Function to get current price of a coin
def get_current_price(coin_name):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_name}&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    return data.get(coin_name, {}).get('usd', 0)

# Add to portfolio
@app.route('/add_portfolio', methods=['GET', 'POST'])
@login_required
def add_portfolio():
    if request.method == 'POST':
        # Handle form submission
        coin_name = request.form.get('coin_name')
        amount = request.form.get('amount')
        purchase_price = request.form.get('purchase_price')

        # Insert logic to add the coin to the database
        new_portfolio_entry = Portfolio(
            user_id=current_user.id,
            coin_name=coin_name,
            amount=amount,
            purchase_price=purchase_price
        )
        db.session.add(new_portfolio_entry)
        db.session.commit()
        
        flash('Portfolio entry added successfully!', 'success')  # Optional flash message
        return redirect(url_for('portfolio'))  # Redirect after successful addition

    # For GET request, fetch the available coins and render the form template
    coins = get_available_coins()  # Fetch the available coins
    return render_template('add_portfolio.html', coins=coins)  # Pass coins to the template

@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    transaction = Portfolio.query.get_or_404(transaction_id)
    
    if request.method == 'POST':
        transaction.coin = request.form['coin']
        transaction.quantity = float(request.form['quantity'])
        transaction.purchase_price = float(request.form['purchase_price'])
        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('portfolio'))

    return render_template('edit_transaction.html', transaction=transaction)

# Route to delete a transaction
@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    transaction = Portfolio.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('portfolio'))

# for redirect to the coin page 
@app.route('/coin/<coin_id>', methods=['GET'])
def coin_details(coin_id):
    # Fetch data for the selected coin
    coin_response = requests.get(f'https://api.coingecko.com/api/v3/coins/{coin_id}')
    coin_data = coin_response.json()

    # Fetch current price data
    price_response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd')
    price_data = price_response.json()

    # Print price_data to check available keys
    print(price_data)

    return render_template('coin.html', coin_data=coin_data, price_data=price_data)

#etherium balance 
def get_eth_balance(address):
    url = f'https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        balance_in_wei = int(data['result'])
        balance_in_eth = balance_in_wei / (10**18)
        return balance_in_eth
    else:
        return None

@app.route('/eth_balance', methods=['GET', 'POST'])
def eth_balance():
    balance = None
    address = None
    if request.method == 'POST':
        address = request.form.get('address')
        balance = get_eth_balance(address)
    return render_template('eth_balance.html', address=address, balance=balance)

# Profile page
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

#admin

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Hardcoded check for admin credentials
        if username == 'admin' and password == 'admin':
            # You can create a dummy admin user object
            user = User.query.filter_by(username='admin').first()  # assuming 'admin' exists in the database
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login failed. Check your username and/or password.', 'danger')
    
    return render_template('admin/admin_login.html')


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))  # Redirect non-admin users to the homepage
    users = User.query.all()  # Get all users
    return render_template('admin/admin_dashboard.html', users=users)
@app.route('/admin/manage_users')



#________________________________


@app.route('/news', methods=['GET'])
def news():
    # Fetch news data from the database
    all_news = News.query.all()
    return render_template('news.html', news=all_news)

# Set up the image upload folder

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/admin/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files['image']
        
        # Handle the image upload
        image_filename = None
        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # Create a new news entry in the database
        news_item = News(title=title, content=content, image_filename=image_filename)
        db.session.add(news_item)
        db.session.commit()

        flash('News added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/add_news.html')


@app.route('/admin/edit_news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))

    news_item = News.query.get_or_404(id)

    if request.method == 'POST':
        news_item.title = request.form['title']
        news_item.content = request.form['content']

        # Handle the image upload
        image = request.files['image']
        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            news_item.image_filename = image_filename

        db.session.commit()
        flash('News updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/edit_news.html', news_item=news_item)


@app.route('/admin/delete_news/<int:id>', methods=['GET'])
@login_required
def delete_news(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))

    news_item = News.query.get_or_404(id)
    db.session.delete(news_item)
    db.session.commit()

    flash('News deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

#____________________________

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
