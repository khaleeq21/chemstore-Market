# ============================================================================
# CHEMSTORE MARKET - FLASK APPLICATION
# E-commerce platform for chemicals and laboratory supplies
# Payment: Cash on Delivery (COD) only - no online payment methods
# ============================================================================

from flask import (
    Flask, render_template, request, redirect, url_for, session, abort,
    send_from_directory, flash, get_flashed_messages, jsonify,
)
from datetime import datetime, timedelta
import sqlite3
import os
import sys
import math
import secrets
import time
import smtplib
import socket
import threading
import webbrowser
import json
import urllib.error
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash


def _get_base_dir():
    # If running as a PyInstaller bundle, use the executable's folder path
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _get_base_dir()
RESOURCE_DIR = getattr(sys, '_MEIPASS', BASE_DIR)
def _asset_version():
    mtimes = []
    for name in ('style.css', 'app.js'):
        path = os.path.join(RESOURCE_DIR, 'static', name)
        if os.path.exists(path):
            mtimes.append(int(os.path.getmtime(path)))
    return str(max(mtimes) if mtimes else 1)


ASSET_VERSION = _asset_version()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
OTP_TTL_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
DEFAULT_UNIT = 'L'
CHEMICAL_UNITS = {
    'L': {'label': 'Liters (L)', 'low_stock': 50},
    'mL': {'label': 'Milliliters (mL)', 'low_stock': 5000},
    'kg': {'label': 'Kilograms (kg)', 'low_stock': 50},
    'g': {'label': 'Grams (g)', 'low_stock': 5000},
    'pcs': {'label': 'Pieces (pcs)', 'low_stock': 10},
    'pack': {'label': 'Packs (pack)', 'low_stock': 10},
    'set': {'label': 'Sets (set)', 'low_stock': 5},
    'unit': {'label': 'Units (unit)', 'low_stock': 10},
}
STORE_NAME = 'ChemStore Market'
STORE_TAGLINE = 'Everyday chemicals, lab apparatus, and surplus supplies'
STORE_SUPPORT_EMAIL = os.environ.get('CHEMSTORE_SUPPORT_EMAIL', 'support@chemstoremarket.com').strip()
SHIPPING_FLAT_CENTS = int(os.environ.get('CHEMSTORE_SHIPPING_CENTS', '0') or 0)
ORDER_STATUSES = ('pending', 'processing', 'shipped', 'completed', 'cancelled')
STORE_PAGE_SIZE = 12
REVIEW_RATINGS = (1, 2, 3, 4, 5)
APP_HOST = '127.0.0.1'
APP_BIND_HOST = os.environ.get('CHEMSTORE_HOST', '0.0.0.0').strip() or '0.0.0.0'
APP_PORT = int(os.environ.get('CHEMSTORE_PORT', '5000'))
DEV_EMAIL = os.environ.get('CHEMSTORE_DEV_EMAIL', '').strip()
DEV_USERNAME = os.environ.get('CHEMSTORE_DEV_USERNAME', 'developer').strip() or 'developer'
DEV_PASSWORD = os.environ.get('CHEMSTORE_DEV_PASSWORD', '')


def _load_secret_key():
    env_key = os.environ.get('CHEMSTORE_SECRET_KEY')
    if env_key:
        return env_key

    key_path = os.path.join(BASE_DIR, '.secret_key')
    try:
        if os.path.exists(key_path):
            with open(key_path, 'r', encoding='utf-8') as key_file:
                existing = key_file.read().strip()
            if existing:
                return existing
        key = secrets.token_hex(32)
        with open(key_path, 'w', encoding='utf-8') as key_file:
            key_file.write(key)
        return key
    except OSError:
        return secrets.token_hex(32)


app = Flask(
    __name__,
    template_folder=os.path.join(RESOURCE_DIR, 'templates'),
    static_folder=os.path.join(RESOURCE_DIR, 'static'),
)
app.secret_key = _load_secret_key()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _normalise_unit(unit):
    return unit if unit in CHEMICAL_UNITS else DEFAULT_UNIT


def _low_stock_limit(unit):
    return CHEMICAL_UNITS[_normalise_unit(unit)]['low_stock']


def _is_low_stock(quantity, unit=DEFAULT_UNIT):
    try:
        return float(quantity) <= _low_stock_limit(unit)
    except (TypeError, ValueError):
        return False


def _format_quantity(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    if not math.isfinite(number):
        return value
    text = f'{number:.6f}'.rstrip('0').rstrip('.')
    return text or '0'


def _format_price(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f'Rs. {number:,.2f}'


def _format_money(cents):
    try:
        number = int(cents)
    except (TypeError, ValueError):
        number = 0
    return f'Rs. {number / 100:,.2f}'


def _money_to_cents(value):
    try:
        return int(round(float(value) * 100))
    except (TypeError, ValueError):
        return 0


def _get_setting(key, default=''):
    try:
        conn = get_db_connection()
        row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
        conn.close()
    except sqlite3.Error:
        return default
    if row and row['value'] is not None:
        return row['value']
    return default


def _set_setting(key, value):
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO settings (key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value = excluded.value''',
        (key, value),
    )
    conn.commit()
    conn.close()


def _get_smtp_config():
    def pick(env_key, setting_key, default=''):
        return (os.environ.get(env_key) or _get_setting(setting_key, '') or default).strip()

    port_raw = pick('SMTP_PORT', 'smtp_port', '587')
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 587
    return {
        'host': pick('SMTP_HOST', 'smtp_host'),
        'port': port,
        'user': pick('SMTP_USER', 'smtp_user'),
        'password': pick('SMTP_PASSWORD', 'smtp_password'),
        'from': pick('SMTP_FROM', 'smtp_from', 'no-reply@chemstore.local'),
        'security': pick('SMTP_SECURITY', 'smtp_security', 'starttls').lower(),
    }


def _smtp_configured():
    return bool(_get_smtp_config()['host'])


def _send_email(to_email, subject, text_body, html_body=None):
    config = _get_smtp_config()
    if not config['host']:
        return False, 'Email delivery is not configured. An administrator can add SMTP details in Store settings.'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = config['from']
    msg['To'] = to_email
    msg.attach(MIMEText(text_body, 'plain'))
    if html_body:
        msg.attach(MIMEText(html_body, 'html'))

    try:
        if config['security'] == 'ssl' or config['port'] == 465:
            with smtplib.SMTP_SSL(config['host'], config['port'], timeout=15) as server:
                if config['user'] and config['password']:
                    server.login(config['user'], config['password'])
                server.send_message(msg)
        else:
            with smtplib.SMTP(config['host'], config['port'], timeout=15) as server:
                if config['security'] == 'starttls':
                    server.starttls()
                if config['user'] and config['password']:
                    server.login(config['user'], config['password'])
                server.send_message(msg)
        return True, ''
    except Exception as exc:
        print(f'Email delivery failed: {exc}')
        return False, str(exc)


def _get_wishlist_ids():
    user_id = session.get('user_id')
    if not user_id:
        return set()
    try:
        conn = get_db_connection()
        rows = conn.execute('SELECT item_id FROM wishlist WHERE user_id = ?', (user_id,)).fetchall()
        conn.close()
    except sqlite3.Error:
        return set()
    return {row['item_id'] for row in rows}


def _get_coupon_by_code(code):
    normalized = (code or '').strip().upper()
    if not normalized:
        return None
    conn = get_db_connection()
    coupon = conn.execute(
        'SELECT * FROM coupons WHERE UPPER(code) = ?',
        (normalized,),
    ).fetchone()
    conn.close()
    return coupon


def _coupon_is_valid(coupon, subtotal_cents):
    if not coupon or not coupon['active']:
        return False, 'This coupon is not active.'
    if coupon['expires_at']:
        try:
            expires = datetime.fromisoformat(str(coupon['expires_at']).replace('Z', ''))
        except ValueError:
            expires = None
        if expires and datetime.now() > expires:
            return False, 'This coupon has expired.'
    if coupon['max_uses'] and coupon['used_count'] >= coupon['max_uses']:
        return False, 'This coupon has reached its usage limit.'
    if subtotal_cents < (coupon['min_subtotal_cents'] or 0):
        return False, f'This coupon requires a subtotal of {_format_money(coupon["min_subtotal_cents"])}.'
    return True, ''


def _coupon_discount_cents(coupon, subtotal_cents):
    if not coupon:
        return 0
    if coupon['discount_type'] == 'percent':
        discount = int(round(subtotal_cents * float(coupon['value']) / 100.0))
    else:
        discount = int(round(float(coupon['value']) * 100))
    return max(0, min(discount, subtotal_cents))


def _cart_totals():
    lines, subtotal_cents = _cart_lines()
    shipping_cents = SHIPPING_FLAT_CENTS if lines else 0
    discount_cents = 0
    coupon = None
    coupon_code = session.get('coupon_code')
    if lines and coupon_code:
        coupon = _get_coupon_by_code(coupon_code)
        valid, _ = _coupon_is_valid(coupon, subtotal_cents)
        if not valid:
            session.pop('coupon_code', None)
            coupon = None
        else:
            discount_cents = _coupon_discount_cents(coupon, subtotal_cents)
    total_cents = max(0, subtotal_cents + shipping_cents - discount_cents)
    return {
        'lines': lines,
        'subtotal_cents': subtotal_cents,
        'shipping_cents': shipping_cents,
        'discount_cents': discount_cents,
        'total_cents': total_cents,
        'coupon': coupon,
        'coupon_code': coupon['code'] if coupon else '',
    }


def _get_review_summary(item_id):
    conn = get_db_connection()
    row = conn.execute(
        '''SELECT COUNT(*) AS total, AVG(rating) AS average
           FROM reviews WHERE item_id = ? AND approved = 1''',
        (item_id,),
    ).fetchone()
    conn.close()
    total = row['total'] if row else 0
    average = float(row['average']) if row and row['average'] is not None else 0.0
    return {'count': total, 'average': round(average, 1)}


def _has_purchased(user_id, item_id):
    if not user_id:
        return False
    conn = get_db_connection()
    row = conn.execute(
        '''SELECT 1 FROM orders o
           JOIN order_items oi ON oi.order_id = o.id
           WHERE o.user_id = ? AND o.payment_status = 'paid' AND oi.item_id = ?
           LIMIT 1''',
        (user_id, item_id),
    ).fetchone()
    conn.close()
    return bool(row)


def _get_cart():
    raw_cart = session.get('cart')
    if not isinstance(raw_cart, dict):
        return {}
    cart = {}
    for item_id, quantity in raw_cart.items():
        try:
            amount = float(quantity)
        except (TypeError, ValueError):
            continue
        if amount > 0:
            cart[int(item_id)] = amount
    return cart


def _save_cart(cart):
    session['cart'] = {
        str(item_id): amount
        for item_id, amount in cart.items()
        if amount > 0
    }
    session.modified = True


def _cart_lines():
    cart = _get_cart()
    if not cart:
        return [], 0

    conn = get_db_connection()
    placeholders = ','.join('?' for _ in cart)
    rows = conn.execute(
        f'SELECT * FROM items WHERE id IN ({placeholders})', tuple(cart)
    ).fetchall()
    conn.close()

    lines = []
    subtotal_cents = 0
    valid_ids = set()
    for item in rows:
        quantity = cart[item['id']]
        unit_price_cents = _money_to_cents(item['price'])
        line_total_cents = int(round(unit_price_cents * quantity))
        subtotal_cents += line_total_cents
        valid_ids.add(item['id'])
        lines.append({
            'item': item,
            'quantity': quantity,
            'unit_price_cents': unit_price_cents,
            'line_total_cents': line_total_cents,
        })

    if valid_ids != set(cart):
        _save_cart({key: value for key, value in cart.items() if key in valid_ids})

    return lines, subtotal_cents


def _login_next_url(default_endpoint):
    next_url = request.values.get('next', '').strip()
    if next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return url_for(default_endpoint)


def _role_home():
    if session.get('role') in ('Developer', 'Admin'):
        return url_for('index')
    return url_for('store')


def _fulfill_order(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order or order['payment_status'] == 'paid':
        conn.close()
        return False

    order_lines = conn.execute(
        'SELECT * FROM order_items WHERE order_id = ?', (order_id,)
    ).fetchall()
    for line in order_lines:
        if line['item_id'] is None:
            continue
        conn.execute(
            '''UPDATE items
               SET quantity = CASE WHEN quantity - ? < 0 THEN 0 ELSE quantity - ? END
               WHERE id = ?''',
            (line['quantity'], line['quantity'], line['item_id']),
        )
    conn.execute(
        '''UPDATE orders
           SET payment_status = 'paid', status = 'processing', updated_at = CURRENT_TIMESTAMP
           WHERE id = ?''',
        (order_id,),
    )
    if order['coupon_code']:
        try:
            conn.execute(
                'UPDATE coupons SET used_count = used_count + 1 WHERE UPPER(code) = ?',
                (order['coupon_code'].upper(),),
            )
        except sqlite3.Error:
            pass
    conn.commit()
    conn.close()
    send_order_confirmation(order)
    return True


app.jinja_env.filters['fmt_qty'] = _format_quantity
app.jinja_env.filters['is_low_stock'] = _is_low_stock
app.jinja_env.filters['price'] = _format_price
app.jinja_env.filters['money'] = _format_money


def csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_hex(16)
        session['_csrf_token'] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {'csrf_token': csrf_token()}


@app.context_processor
def inject_store_context():
    wishlist_ids = _get_wishlist_ids()
    return {
        'cart_count': len(_get_cart()),
        'store_name': STORE_NAME,
        'store_tagline': STORE_TAGLINE,
        'support_email': _get_setting('support_email', STORE_SUPPORT_EMAIL),
        'is_staff': session.get('role') in ('Developer', 'Admin'),
        'is_signed_in': 'user_id' in session,
        'wishlist_ids': wishlist_ids,
        'wishlist_count': len(wishlist_ids),
        'review_ratings': REVIEW_RATINGS,
        'asset_version': ASSET_VERSION,
    }


def _is_ajax():
    requested_with = request.headers.get('X-Requested-With', '')
    return (
        requested_with in ('XMLHttpRequest', 'fetch')
        or request.accept_mimetypes.best == 'application/json'
    )


def _json_response(ok, message='', status=200, **extra):
    payload = {'ok': ok, 'message': message}
    payload.update(extra)
    return jsonify(payload), status


@app.after_request
def add_app_header(response):
    response.headers['X-ChemStore'] = '1'
    return response


@app.before_request
def protect_from_csrf():
    if request.method == 'POST' and not app.config.get('TESTING'):
        expected = session.get('_csrf_token')
        provided = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
        if not expected or not provided or not secrets.compare_digest(expected, provided):
            abort(400, description='Invalid or missing CSRF token.')


@app.before_request
def refresh_session_from_db():
    if request.endpoint in ('static', 'uploaded_file'):
        return
    user_id = session.get('user_id')
    if user_id is None:
        return

    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, role, approved FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    conn.close()

    if not user or user['approved'] == 0:
        session.clear()
        if _is_ajax():
            return _json_response(False, 'Your session has expired. Please sign in again.', 401)
        return redirect(url_for('login'))

    session['username'] = user['username']
    session['role'] = user['role']


def _allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


LOGIN_FAILURES = {}
LOGIN_WINDOW_SECONDS = 300
LOGIN_MAX_FAILURES = 8


def _is_login_blocked(key):
    count, first_attempt = LOGIN_FAILURES.get(key, (0, 0.0))
    if time.time() - first_attempt > LOGIN_WINDOW_SECONDS:
        LOGIN_FAILURES.pop(key, None)
        return False
    return count >= LOGIN_MAX_FAILURES


def _record_login_failure(key):
    count, first_attempt = LOGIN_FAILURES.get(key, (0, 0.0))
    if time.time() - first_attempt > LOGIN_WINDOW_SECONDS:
        count, first_attempt = 0, time.time()
    LOGIN_FAILURES[key] = (count + 1, first_attempt)


def _save_image_upload(file, prefix):
    if not file or not file.filename:
        return None
    if not _allowed_image(file.filename):
        return None
    extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f'{prefix}_{secrets.token_hex(6)}.{extension}'
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return url_for('uploaded_file', filename=filename)


def _remove_upload(filename):
    if not filename or filename == 'default.png':
        return
    path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(filename))
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def get_db_connection():
    db_path = os.path.join(BASE_DIR, 'warehouse.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            name TEXT NOT NULL,
            category TEXT,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL DEFAULT 'L',
            price REAL
        )
    ''')
    try:
        conn.execute("ALTER TABLE items ADD COLUMN unit TEXT NOT NULL DEFAULT 'L'")
    except sqlite3.OperationalError:
        pass
    for column_sql in (
        "ALTER TABLE items ADD COLUMN description TEXT DEFAULT ''",
        "ALTER TABLE items ADD COLUMN image_url TEXT DEFAULT ''",
        "ALTER TABLE items ADD COLUMN active INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE items ADD COLUMN featured INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE items ADD COLUMN seller_id INTEGER DEFAULT 1",
        "ALTER TABLE items ADD COLUMN seller_name TEXT DEFAULT 'ChemStore Official'",
        "ALTER TABLE items ADD COLUMN condition TEXT DEFAULT 'Brand New'",
        "ALTER TABLE items ADD COLUMN listing_type TEXT DEFAULT 'fixed'",
        "ALTER TABLE items ADD COLUMN starting_bid REAL DEFAULT 0.0",
        "ALTER TABLE items ADD COLUMN current_bid REAL DEFAULT 0.0",
        "ALTER TABLE items ADD COLUMN bid_count INTEGER DEFAULT 0",
        "ALTER TABLE items ADD COLUMN auction_end TEXT DEFAULT ''",
        "ALTER TABLE items ADD COLUMN brand TEXT DEFAULT ''",
        "ALTER TABLE items ADD COLUMN badge TEXT DEFAULT ''",
    ):
        try:
            conn.execute(column_sql)
        except sqlite3.OperationalError:
            pass

    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            address_line1 TEXT NOT NULL,
            address_line2 TEXT,
            city TEXT NOT NULL,
            state TEXT,
            postal_code TEXT,
            country TEXT NOT NULL,
            subtotal_cents INTEGER NOT NULL DEFAULT 0,
            shipping_cents INTEGER NOT NULL DEFAULT 0,
            discount_cents INTEGER NOT NULL DEFAULT 0,
            coupon_code TEXT,
            total_cents INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            payment_status TEXT NOT NULL DEFAULT 'unpaid',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER,
            name TEXT NOT NULL,
            unit TEXT,
            quantity REAL NOT NULL,
            unit_price_cents INTEGER NOT NULL,
            line_total_cents INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    ''')
    for column_sql in (
        "ALTER TABLE orders ADD COLUMN discount_cents INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN coupon_code TEXT",
        "ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'cod'",
        "ALTER TABLE orders ADD COLUMN carrier TEXT DEFAULT 'Pakistan Post'",
        "ALTER TABLE orders ADD COLUMN tracking_number TEXT DEFAULT ''",
        "ALTER TABLE orders ADD COLUMN estimated_delivery TEXT DEFAULT ''",
    ):
        try:
            conn.execute(column_sql)
        except sqlite3.OperationalError:
            pass

    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            title TEXT,
            body TEXT,
            verified INTEGER NOT NULL DEFAULT 0,
            approved INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, item_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            bidder_name TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS product_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS product_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            is_seller INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES product_questions (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_type TEXT NOT NULL DEFAULT 'percent',
            value REAL NOT NULL DEFAULT 0,
            min_subtotal_cents INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1,
            expires_at TEXT,
            max_uses INTEGER NOT NULL DEFAULT 0,
            used_count INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            profile_pic TEXT DEFAULT 'default.png',
            approved INTEGER DEFAULT 1
        )
    ''')
    
    for column_sql in (
        'ALTER TABLE users ADD COLUMN profile_pic TEXT DEFAULT "default.png"',
        'ALTER TABLE users ADD COLUMN approved INTEGER DEFAULT 1',
        'ALTER TABLE users ADD COLUMN is_seller INTEGER DEFAULT 0',
        'ALTER TABLE users ADD COLUMN seller_name TEXT DEFAULT ""',
        'ALTER TABLE users ADD COLUMN seller_rating REAL DEFAULT 5.0',
        'ALTER TABLE users ADD COLUMN seller_sales_count INTEGER DEFAULT 0',
    ):
        try:
            conn.execute(column_sql)
        except sqlite3.OperationalError:
            pass
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chemical_name TEXT,
            amount_used REAL,
            unit TEXT NOT NULL DEFAULT 'L',
            purpose TEXT,
            username TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        conn.execute("ALTER TABLE usage_logs ADD COLUMN unit TEXT NOT NULL DEFAULT 'L'")
    except sqlite3.OperationalError:
        pass
    
    dev_check = conn.execute('SELECT * FROM users WHERE role = ?', ('Developer',)).fetchone()
    if not dev_check:
        if DEV_EMAIL and DEV_PASSWORD:
            hashed_pw = generate_password_hash(DEV_PASSWORD)
            conn.execute('INSERT INTO users (email, username, password, role, profile_pic, approved) VALUES (?, ?, ?, ?, ?, ?)', 
                         (DEV_EMAIL, DEV_USERNAME, hashed_pw, 'Developer', 'default.png', 1))
            conn.commit()
        else:
            print('No Developer account exists. Set CHEMSTORE_DEV_EMAIL and CHEMSTORE_DEV_PASSWORD, then restart to create one.')

    count = conn.execute('SELECT COUNT(*) FROM items').fetchone()[0]
    conn.close()
    if count <= 1:
        try:
            import seed_database
            seed_database.migrate_and_seed()
        except Exception as seed_err:
            print(f'Seed catalog notice: {seed_err}')

def send_otp_email(to_email, otp_code):
    text_body = (
        f'Your ChemStore Market password reset code is: {otp_code}\n\n'
        f'It expires in {OTP_TTL_SECONDS // 60} minutes. '
        'If you did not request a reset, you can safely ignore this email.'
    )
    html_body = (
        f'<div style="font-family:Arial,sans-serif;padding:24px">'
        f'<h2 style="margin:0 0 12px">Reset your ChemStore Market password</h2>'
        f'<p>Use this one-time code to continue:</p>'
        f'<p style="font-size:30px;letter-spacing:6px;font-weight:700;margin:18px 0">{otp_code}</p>'
        f'<p style="color:#64748b">This code expires in {OTP_TTL_SECONDS // 60} minutes. '
        'If you did not request a reset, you can ignore this email.</p></div>'
    )
    sent, error = _send_email(to_email, 'ChemStore Market - Password reset code', text_body, html_body)
    if not sent:
        print(f"\n[OTP CODE FOR {to_email}]: {otp_code} ({error})\n")
    return sent


def send_order_confirmation(order):
    if not order:
        return False
    item_rows = []
    conn = get_db_connection()
    lines = conn.execute(
        'SELECT * FROM order_items WHERE order_id = ? ORDER BY id', (order['id'],)
    ).fetchall()
    conn.close()
    for line in lines:
        item_rows.append(
            f'<tr><td style="padding:6px 0">{line["name"]} ({_format_quantity(line["quantity"])} {line["unit"]})</td>'
            f'<td style="text-align:right">{_format_money(line["line_total_cents"])}</td></tr>'
        )
    text_body = (
        f'Thank you for your order #{order["id"]}.\n'
        f'Total: {_format_money(order["total_cents"])}\n'
        'We will email you again when your order ships.'
    )
    html_body = (
        f'<div style="font-family:Arial,sans-serif;padding:24px">'
        f'<h2>Order #{order["id"]} confirmed</h2>'
        f'<p>Thank you, {order["full_name"]}. We are preparing your order.</p>'
        f'<table style="width:100%;border-collapse:collapse">{"".join(item_rows)}</table>'
        f'<p style="font-size:18px;margin-top:18px"><strong>Total: {_format_money(order["total_cents"])}</strong></p>'
        '</div>'
    )
    sent, _ = _send_email(
        order['email'],
        f'ChemStore Market order #{order["id"]} confirmed',
        text_body,
        html_body,
    )
    return sent

def _build_activity(logs):
    today = datetime.now().date()
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    counts = {day: 0 for day in days}
    for log in logs:
        raw_timestamp = log['timestamp']
        if not raw_timestamp:
            continue
        try:
            log_day = datetime.fromisoformat(str(raw_timestamp).replace('Z', '')).date()
        except ValueError:
            continue
        if log_day in counts:
            counts[log_day] += 1
    return [
        {'label': day.strftime('%a'), 'date': day.isoformat(), 'count': counts[day]}
        for day in days
    ]


def _dashboard_context(search_query=''):
    conn = get_db_connection()
    if search_query:
        items = conn.execute(
            'SELECT * FROM items WHERE name LIKE ? OR code LIKE ? OR category LIKE ?',
            (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'),
        ).fetchall()
    else:
        items = conn.execute('SELECT * FROM items').fetchall()

    logs = conn.execute('SELECT * FROM usage_logs ORDER BY id DESC').fetchall()

    role = session.get('role')
    if role in ['Developer', 'Admin']:
        users = conn.execute(
            'SELECT id, email, username, role, profile_pic, approved FROM users ORDER BY id'
        ).fetchall()
    else:
        users = conn.execute(
            "SELECT id, email, username, role, profile_pic, approved FROM users WHERE role = 'Admin' AND approved = 1 ORDER BY id"
        ).fetchall()

    pending_admins = []
    pending_users = []
    if role == 'Developer':
        pending_admins = conn.execute(
            "SELECT * FROM users WHERE role = 'Admin' AND approved = 0 ORDER BY id"
        ).fetchall()
    if role in ['Developer', 'Admin']:
        pending_users = conn.execute(
            "SELECT * FROM users WHERE role = 'User' AND approved = 0 ORDER BY id"
        ).fetchall()

    current_user = conn.execute(
        'SELECT * FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()

    total_chemicals = conn.execute('SELECT COUNT(*) FROM items').fetchone()[0]
    total_logs = conn.execute('SELECT COUNT(*) FROM usage_logs').fetchone()[0]
    stock_rows = conn.execute('SELECT quantity, unit FROM items').fetchall()
    low_stock = sum(
        1 for row in stock_rows if _is_low_stock(row['quantity'], row['unit'])
    )
    conn.close()

    stats = {
        'chemicals': total_chemicals,
        'low_stock': low_stock,
        'logs': total_logs,
        'members': len(users),
    }

    return {
        'items': items,
        'logs': logs,
        'users': users,
        'search_query': search_query,
        'current_user': current_user,
        'pending_admins': pending_admins,
        'pending_users': pending_users,
        'stats': stats,
        'activity': _build_activity(logs),
        'units': CHEMICAL_UNITS,
    }


@app.route('/')
def store():
    search_query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    sort = request.args.get('sort', 'featured').strip()
    in_stock = request.args.get('in_stock', '').strip()
    listing_format = request.args.get('format', 'all').strip()
    condition = request.args.get('condition', 'all').strip()
    min_rating_raw = request.args.get('rating', '').strip()
    min_price_raw = request.args.get('min_price', '').strip()
    max_price_raw = request.args.get('max_price', '').strip()

    try:
        min_price = float(min_price_raw) if min_price_raw else None
    except ValueError:
        min_price = None
    try:
        max_price = float(max_price_raw) if max_price_raw else None
    except ValueError:
        max_price = None
    try:
        min_rating = float(min_rating_raw) if min_rating_raw else None
    except ValueError:
        min_rating = None

    clauses = ['COALESCE(i.active, 1) = 1']
    params = []
    if search_query:
        clauses.append('(i.name LIKE ? OR i.category LIKE ? OR i.code LIKE ? OR i.brand LIKE ? OR COALESCE(i.description, \'\') LIKE ?)')
        like = f'%{search_query}%'
        params.extend([like, like, like, like, like])
    if category:
        clauses.append('i.category = ?')
        params.append(category)
    if in_stock == '1':
        clauses.append('i.quantity > 0 AND (i.price > 0 OR i.starting_bid > 0)')
    if listing_format == 'fixed':
        clauses.append("i.listing_type IN ('fixed', 'both')")
    elif listing_format == 'auction':
        clauses.append("i.listing_type IN ('auction', 'both')")
    if condition and condition != 'all':
        clauses.append('i.condition LIKE ?')
        params.append(f'%{condition}%')
    if min_price is not None:
        clauses.append('(CASE WHEN i.price > 0 THEN i.price ELSE i.current_bid END) >= ?')
        params.append(min_price)
    if max_price is not None:
        clauses.append('(CASE WHEN i.price > 0 THEN i.price ELSE i.current_bid END) <= ?')
        params.append(max_price)
    if min_rating is not None:
        clauses.append('(SELECT AVG(r.rating) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) >= ?')
        params.append(min_rating)

    order_by = {
        'price_asc': '(CASE WHEN i.price > 0 THEN i.price ELSE i.current_bid END) ASC, i.name',
        'price_desc': '(CASE WHEN i.price > 0 THEN i.price ELSE i.current_bid END) DESC, i.name',
        'name': 'i.name ASC',
        'newest': 'i.id DESC',
        'ending_soon': "CASE WHEN i.auction_end != '' THEN i.auction_end ELSE '9999-12-31' END ASC, i.id DESC",
        'bids': 'COALESCE(i.bid_count, 0) DESC, i.id DESC',
        'rating': 'avg_rating DESC, review_count DESC, i.name',
        'featured': 'COALESCE(i.featured, 0) DESC, COALESCE(i.image_url, \'\') != \'\' DESC, i.name',
    }.get(sort, 'COALESCE(i.featured, 0) DESC, COALESCE(i.image_url, \'\') != \'\' DESC, i.name')

    try:
        page = max(1, int(request.args.get('page', '1')))
    except ValueError:
        page = 1

    where_sql = ' AND '.join(clauses)
    conn = get_db_connection()
    total = conn.execute(
        f'SELECT COUNT(*) FROM items i WHERE {where_sql}', tuple(params)
    ).fetchone()[0]
    pages = max(1, math.ceil(total / STORE_PAGE_SIZE))
    page = min(page, pages)
    offset = (page - 1) * STORE_PAGE_SIZE
    items = conn.execute(
        f'''SELECT i.*,
                   (SELECT AVG(r.rating) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS avg_rating,
                   (SELECT COUNT(*) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS review_count
            FROM items i
            WHERE {where_sql}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?''',
        tuple(params) + (STORE_PAGE_SIZE, offset),
    ).fetchall()
    categories = conn.execute(
        '''SELECT category, COUNT(*) AS total
           FROM items
           WHERE COALESCE(active, 1) = 1 AND category IS NOT NULL AND category != ''
           GROUP BY category ORDER BY category'''
    ).fetchall()
    featured = conn.execute(
        '''SELECT i.*,
                  (SELECT AVG(r.rating) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS avg_rating,
                  (SELECT COUNT(*) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS review_count
           FROM items i
           WHERE COALESCE(i.active, 1) = 1 AND (i.price > 0 OR i.starting_bid > 0)
           ORDER BY COALESCE(i.featured, 0) DESC, i.id DESC LIMIT 4'''
    ).fetchall()
    auctions_ending_soon = conn.execute(
        '''SELECT i.*,
                  (SELECT AVG(r.rating) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS avg_rating,
                  (SELECT COUNT(*) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS review_count
           FROM items i
           WHERE COALESCE(i.active, 1) = 1 AND i.listing_type IN ('auction', 'both') AND i.auction_end != ''
           ORDER BY i.auction_end ASC LIMIT 6'''
    ).fetchall()
    deals_of_the_day = conn.execute(
        '''SELECT i.*,
                  (SELECT AVG(r.rating) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS avg_rating,
                  (SELECT COUNT(*) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS review_count
           FROM items i
           WHERE COALESCE(i.active, 1) = 1 AND (i.badge != '' OR i.featured = 1)
           ORDER BY i.featured DESC, i.id DESC LIMIT 6'''
    ).fetchall()
    conn.close()

    return render_template(
        'store.html',
        items=items,
        featured=featured,
        auctions_ending_soon=auctions_ending_soon,
        deals_of_the_day=deals_of_the_day,
        categories=categories,
        search_query=search_query,
        selected_category=category,
        sort=sort,
        in_stock=in_stock,
        listing_format=listing_format,
        condition=condition,
        rating=min_rating_raw,
        min_price=min_price_raw,
        max_price=max_price_raw,
        pagination={
            'page': page,
            'pages': pages,
            'total': total,
            'has_prev': page > 1,
            'has_next': page < pages,
            'start': offset + 1 if total else 0,
            'end': min(offset + STORE_PAGE_SIZE, total),
        },
    )


@app.route('/product/<int:id>')
def product_detail(id):
    conn = get_db_connection()
    item = conn.execute(
        '''SELECT i.*,
                  (SELECT AVG(r.rating) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS avg_rating,
                  (SELECT COUNT(*) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS review_count
           FROM items i WHERE i.id = ? AND COALESCE(i.active, 1) = 1''',
        (id,),
    ).fetchone()
    if not item:
        conn.close()
        abort(404)

    reviews = conn.execute(
        '''SELECT r.*, u.username FROM reviews r
           JOIN users u ON u.id = r.user_id
           WHERE r.item_id = ? AND r.approved = 1
           ORDER BY r.id DESC''',
        (id,),
    ).fetchall()

    bids = conn.execute(
        '''SELECT * FROM bids WHERE item_id = ? ORDER BY amount DESC, id DESC LIMIT 20''',
        (id,)
    ).fetchall()

    questions_raw = conn.execute(
        '''SELECT q.*, u.username FROM product_questions q
           JOIN users u ON u.id = q.user_id
           WHERE q.item_id = ? ORDER BY q.id DESC''',
        (id,)
    ).fetchall()
    questions = []
    for q in questions_raw:
        answers = conn.execute(
            '''SELECT a.*, u.username FROM product_answers a
               JOIN users u ON u.id = a.user_id
               WHERE a.question_id = ? ORDER BY a.id ASC''',
            (q['id'],)
        ).fetchall()
        questions.append({'question': q, 'answers': answers})

    total_revs = len(reviews)
    star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        if r['rating'] in star_counts:
            star_counts[r['rating']] += 1
    rating_breakdown = {
        star: {
            'count': count,
            'percent': int(round((count / total_revs) * 100)) if total_revs else 0
        }
        for star, count in star_counts.items()
    }

    cur_bid = float(item['current_bid'] or item['starting_bid'] or 0.0)
    inc = 1.0 if cur_bid < 25 else (2.5 if cur_bid < 100 else 5.0)
    min_next_bid = round(cur_bid + inc if item['bid_count'] > 0 else cur_bid, 2)

    is_ended = False
    time_left_str = ''
    if item['auction_end']:
        try:
            end_dt = datetime.fromisoformat(item['auction_end'].replace('Z', ''))
            delta = end_dt - datetime.now()
            if delta.total_seconds() <= 0:
                is_ended = True
                time_left_str = 'Ended'
            else:
                days = delta.days
                hours = delta.seconds // 3600
                mins = (delta.seconds % 3600) // 60
                if days > 0:
                    time_left_str = f'{days}d {hours}h left'
                elif hours > 0:
                    time_left_str = f'{hours}h {mins}m left'
                else:
                    time_left_str = f'{mins}m left'
        except ValueError:
            pass

    my_review = None
    if session.get('user_id'):
        my_review = conn.execute(
            'SELECT * FROM reviews WHERE item_id = ? AND user_id = ?',
            (id, session['user_id']),
        ).fetchone()

    related = conn.execute(
        '''SELECT i.*,
                  (SELECT AVG(r.rating) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS avg_rating,
                  (SELECT COUNT(*) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS review_count
           FROM items i
           WHERE COALESCE(i.active, 1) = 1 AND i.id != ? AND i.category = ?
           ORDER BY COALESCE(i.featured, 0) DESC, i.name LIMIT 4''',
        (id, item['category']),
    ).fetchall()

    seller_info = None
    if item['seller_id']:
        seller_info = conn.execute(
            'SELECT id, username, email, seller_name, seller_rating, seller_sales_count FROM users WHERE id = ?',
            (item['seller_id'],)
        ).fetchone()

    conn.close()
    return render_template(
        'product.html',
        item=item,
        reviews=reviews,
        bids=bids,
        questions=questions,
        rating_breakdown=rating_breakdown,
        min_next_bid=min_next_bid,
        is_ended=is_ended,
        time_left_str=time_left_str,
        seller_info=seller_info,
        related=related,
        review_summary={'count': len(reviews), 'average': round(float(item['avg_rating'] or 0), 1)},
        my_review=my_review,
        purchased=_has_purchased(session.get('user_id'), id),
    )


@app.route('/product/<int:id>/bid', methods=('POST',))
def place_bid(id):
    if 'user_id' not in session:
        if _is_ajax():
            return _json_response(False, 'Please sign in to place a bid.', 401)
        return redirect(url_for('login', next=url_for('product_detail', id=id)))

    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ? AND COALESCE(active, 1) = 1', (id,)).fetchone()
    if not item or item['listing_type'] not in ('auction', 'both'):
        conn.close()
        flash('This item is not open for bidding.', 'error')
        return redirect(url_for('product_detail', id=id))

    if item['auction_end']:
        try:
            end_time = datetime.fromisoformat(item['auction_end'].replace('Z', ''))
            if datetime.now() > end_time:
                conn.close()
                flash('This auction has already ended.', 'error')
                return redirect(url_for('product_detail', id=id))
        except ValueError:
            pass

    try:
        bid_amount = round(float(request.form.get('amount', '0')), 2)
    except ValueError:
        bid_amount = 0.0

    cur_bid = float(item['current_bid'] or item['starting_bid'] or 0.0)
    inc = 1.0 if cur_bid < 25 else (2.5 if cur_bid < 100 else 5.0)
    min_allowed = round(cur_bid + inc if item['bid_count'] > 0 else cur_bid, 2)

    if bid_amount < min_allowed:
        conn.close()
        msg = f'Your bid must be at least ${_format_price(min_allowed)}.'
        if _is_ajax():
            return _json_response(False, msg, 400)
        flash(msg, 'error')
        return redirect(url_for('product_detail', id=id))

    uname = session.get('username', 'bidder')
    masked = (uname[0] + '***' + uname[-1]) if len(uname) > 2 else (uname + '***')

    conn.execute(
        'INSERT INTO bids (item_id, user_id, bidder_name, amount) VALUES (?, ?, ?, ?)',
        (id, session['user_id'], masked, bid_amount)
    )
    conn.execute(
        'UPDATE items SET current_bid = ?, bid_count = bid_count + 1 WHERE id = ?',
        (bid_amount, id)
    )
    conn.commit()
    conn.close()

    msg = f'Congratulations! You are now the highest bidder at ${_format_price(bid_amount)}.'
    if _is_ajax():
        return _json_response(True, msg, new_bid=bid_amount, new_count=item['bid_count'] + 1)
    flash(msg, 'success')
    return redirect(url_for('product_detail', id=id))


@app.route('/product/<int:id>/question', methods=('POST',))
def ask_product_question(id):
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('product_detail', id=id)))
    question_text = request.form.get('question', '').strip()[:1000]
    if not question_text:
        flash('Please enter a question.', 'error')
        return redirect(url_for('product_detail', id=id) + '#qa')
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO product_questions (item_id, user_id, question) VALUES (?, ?, ?)',
        (id, session['user_id'], question_text)
    )
    conn.commit()
    conn.close()
    flash('Your question has been posted to the seller and community.', 'success')
    return redirect(url_for('product_detail', id=id) + '#qa')


@app.route('/question/<int:question_id>/answer', methods=('POST',))
def answer_product_question(question_id):
    if 'user_id' not in session:
        flash('Please sign in to answer.', 'error')
        return redirect(url_for('login'))
    answer_text = request.form.get('answer', '').strip()[:2000]
    if not answer_text:
        flash('Please enter an answer.', 'error')
        return redirect(request.referrer or url_for('store'))
    conn = get_db_connection()
    q = conn.execute('SELECT * FROM product_questions WHERE id = ?', (question_id,)).fetchone()
    if not q:
        conn.close()
        abort(404)
    item = conn.execute('SELECT seller_id FROM items WHERE id = ?', (q['item_id'],)).fetchone()
    is_seller = 1 if (item and item['seller_id'] == session['user_id']) or session.get('role') in ('Developer', 'Admin') else 0
    conn.execute(
        'INSERT INTO product_answers (question_id, user_id, answer, is_seller) VALUES (?, ?, ?, ?)',
        (question_id, session['user_id'], answer_text, is_seller)
    )
    conn.commit()
    conn.close()
    flash('Thank you! Your answer has been posted.', 'success')
    return redirect(url_for('product_detail', id=q['item_id']) + '#qa')


@app.route('/sell', methods=('GET', 'POST'))
def sell_item():
    if 'user_id' not in session:
        flash('Please sign in or create an account to start selling on ChemStore.', 'info')
        return redirect(url_for('login', next=url_for('sell_item')))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        brand = request.form.get('brand', '').strip()
        condition = request.form.get('condition', 'Brand New').strip()
        listing_type = request.form.get('listing_type', 'fixed').strip()
        price_raw = request.form.get('price', '').strip() or '0'
        starting_bid_raw = request.form.get('starting_bid', '').strip() or '0'
        quantity_raw = request.form.get('quantity', '1').strip() or '1'
        try:
            duration_days = int(request.form.get('duration_days', '7'))
        except ValueError:
            duration_days = 7
        unit = request.form.get('unit', 'pcs').strip() or 'pcs'
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        image_file = request.files.get('image_file')

        if not name or not category:
            flash('Item title and category are required.', 'error')
            return redirect(url_for('sell_item'))

        try:
            price = float(price_raw)
            starting_bid = float(starting_bid_raw)
            quantity = float(quantity_raw)
            if price < 0 or starting_bid < 0 or quantity <= 0:
                raise ValueError
        except ValueError:
            flash('Please enter valid, non-negative numbers for pricing and quantity.', 'error')
            return redirect(url_for('sell_item'))

        if listing_type == 'auction' and starting_bid <= 0:
            flash('Auction items require a starting bid greater than Rs. 0.', 'error')
            return redirect(url_for('sell_item'))
        if listing_type == 'fixed' and price <= 0:
            flash('Buy It Now items require a price greater than Rs. 0.', 'error')
            return redirect(url_for('sell_item'))

        auction_end = ''
        if listing_type in ('auction', 'both'):
            auction_end = (datetime.now() + timedelta(days=duration_days)).isoformat()

        saved_image_url = None
        if image_file and image_file.filename:
            if not _allowed_image(image_file.filename):
                flash('Image must be a PNG, JPG, JPEG, GIF, or WEBP file.', 'error')
                return redirect(url_for('sell_item'))
            saved_image_url = _save_image_upload(image_file, 'product')
            if saved_image_url:
                image_url = saved_image_url
        if not image_url:
            image_url = '/static/images/beakers.svg'

        code = 'MKT-' + secrets.token_hex(3).upper()

        conn = get_db_connection()
        cursor = conn.execute('''
            INSERT INTO items (
                code, name, category, quantity, unit, price, description, image_url,
                active, featured, seller_id, seller_name, condition, listing_type,
                starting_bid, current_bid, bid_count, auction_end, brand, badge
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        ''', (
            code, name, category, quantity, unit, price, description, image_url,
            session['user_id'], session.get('username', 'Seller'), condition,
            listing_type, starting_bid, starting_bid if listing_type in ('auction', 'both') else 0.0,
            auction_end, brand, 'New Listing'
        ))
        item_id = cursor.lastrowid
        conn.execute('UPDATE users SET is_seller = 1 WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()

        flash(f'Success! Your listing "{name}" is now live on ChemStore Marketplace.', 'success')
        return redirect(url_for('product_detail', id=item_id))

    conn = get_db_connection()
    categories = conn.execute(
        "SELECT DISTINCT category FROM items WHERE category IS NOT NULL AND category != '' ORDER BY category"
    ).fetchall()
    conn.close()
    return render_template('sell.html', categories=categories, units=CHEMICAL_UNITS)


@app.route('/seller/listings')
def seller_listings():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('seller_listings')))
    conn = get_db_connection()
    items = conn.execute(
        '''SELECT i.*,
                  (SELECT COUNT(*) FROM bids b WHERE b.item_id = i.id) AS total_bids
           FROM items i
           WHERE i.seller_id = ?
           ORDER BY i.id DESC''',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return render_template('seller_listings.html', items=items)


@app.route('/orders/<int:order_id>/invoice')
def order_invoice(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('orders')))
    conn = get_db_connection()
    if session.get('role') in ('Developer', 'Admin'):
        order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    else:
        order = conn.execute(
            'SELECT * FROM orders WHERE id = ? AND user_id = ?',
            (order_id, session['user_id']),
        ).fetchone()
    if not order:
        conn.close()
        abort(404)
    items = conn.execute(
        'SELECT * FROM order_items WHERE order_id = ? ORDER BY id', (order_id,)
    ).fetchall()
    conn.close()
    return render_template(
        'invoice.html',
        order=order,
        items=items,
        store_name=STORE_NAME,
        support_email=_get_setting('support_email', STORE_SUPPORT_EMAIL),
    )


@app.route('/product/<int:id>/review', methods=('POST',))
def submit_review(id):
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('product_detail', id=id)))
    try:
        rating = int(request.form.get('rating', '0'))
    except ValueError:
        rating = 0
    title = request.form.get('title', '').strip()[:120]
    body = request.form.get('body', '').strip()[:2000]
    if rating not in REVIEW_RATINGS:
        flash('Choose a star rating from 1 to 5.', 'error')
        return redirect(url_for('product_detail', id=id) + '#reviews')

    conn = get_db_connection()
    item = conn.execute('SELECT id FROM items WHERE id = ?', (id,)).fetchone()
    if not item:
        conn.close()
        abort(404)
    existing = conn.execute(
        'SELECT id FROM reviews WHERE item_id = ? AND user_id = ?',
        (id, session['user_id']),
    ).fetchone()
    verified = 1 if _has_purchased(session['user_id'], id) else 0
    if existing:
        conn.execute(
            '''UPDATE reviews SET rating = ?, title = ?, body = ?, verified = ?,
               created_at = CURRENT_TIMESTAMP WHERE id = ?''',
            (rating, title, body, verified, existing['id']),
        )
    else:
        conn.execute(
            '''INSERT INTO reviews (item_id, user_id, rating, title, body, verified)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (id, session['user_id'], rating, title, body, verified),
        )
    conn.commit()
    conn.close()
    flash('Thanks! Your review has been published.', 'success')
    return redirect(url_for('product_detail', id=id) + '#reviews')


@app.route('/wishlist')
def wishlist():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('wishlist')))
    conn = get_db_connection()
    rows = conn.execute(
        '''SELECT i.*,
                  (SELECT AVG(r.rating) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS avg_rating,
                  (SELECT COUNT(*) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS review_count
           FROM wishlist w JOIN items i ON i.id = w.item_id
           WHERE w.user_id = ? AND COALESCE(i.active, 1) = 1
           ORDER BY w.id DESC''',
        (session['user_id'],),
    ).fetchall()
    conn.close()
    return render_template('wishlist.html', items=rows)


@app.route('/wishlist/toggle/<int:id>', methods=('POST',))
def toggle_wishlist(id):
    if 'user_id' not in session:
        if _is_ajax():
            return _json_response(False, 'Please sign in to save products.', 401)
        return redirect(url_for('login', next=url_for('product_detail', id=id)))
    conn = get_db_connection()
    item = conn.execute('SELECT id, name FROM items WHERE id = ?', (id,)).fetchone()
    if not item:
        conn.close()
        abort(404)
    existing = conn.execute(
        'SELECT id FROM wishlist WHERE user_id = ? AND item_id = ?',
        (session['user_id'], id),
    ).fetchone()
    if existing:
        conn.execute('DELETE FROM wishlist WHERE id = ?', (existing['id'],))
        saved = False
        message = f'{item["name"]} removed from your saved items.'
    else:
        conn.execute(
            'INSERT INTO wishlist (user_id, item_id) VALUES (?, ?)',
            (session['user_id'], id),
        )
        saved = True
        message = f'{item["name"]} saved to your list.'
    conn.commit()
    conn.close()
    if _is_ajax():
        return _json_response(True, message, saved=saved)
    flash(message, 'success')
    return redirect(request.referrer or url_for('product_detail', id=id))


@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('cart')))
    totals = _cart_totals()
    return render_template('cart.html', **totals)


@app.route('/cart/coupon', methods=('POST',))
def apply_coupon():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('cart')))
    code = request.form.get('coupon_code', '').strip()
    if request.form.get('action') == 'remove':
        session.pop('coupon_code', None)
        flash('Coupon removed.', 'success')
        return redirect(url_for('cart'))
    coupon = _get_coupon_by_code(code)
    lines, subtotal_cents = _cart_lines()
    valid, message = _coupon_is_valid(coupon, subtotal_cents)
    if not lines:
        flash('Add products to your cart before applying a coupon.', 'error')
    elif not coupon:
        flash('That coupon code was not found.', 'error')
    elif not valid:
        flash(message, 'error')
    else:
        session['coupon_code'] = coupon['code']
        flash(f'Coupon {coupon["code"]} applied.', 'success')
    return redirect(url_for('cart'))


@app.route('/buy-now/<int:id>', methods=('POST',))
def buy_now(id):
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('product_detail', id=id)))
    try:
        amount = float(request.form.get('quantity', '1'))
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError
    except ValueError:
        flash('Enter a valid quantity.', 'error')
        return redirect(url_for('product_detail', id=id))
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ? AND COALESCE(active, 1) = 1', (id,)).fetchone()
    conn.close()
    if not item:
        abort(404)
    if item['listing_type'] == 'auction':
        flash('This item is up for auction. Place a bid instead.', 'error')
        return redirect(url_for('product_detail', id=id) + '#bid-box')
    if float(item['price'] or 0) <= 0 or float(item['quantity']) <= 0:
        flash('This product is not available for sale yet.', 'error')
        return redirect(url_for('product_detail', id=id))
    if amount > float(item['quantity']):
        flash('That quantity is not available. Please choose a smaller amount.', 'error')
        return redirect(url_for('product_detail', id=id))
    cart_items = _get_cart()
    cart_items[id] = round(amount, 6)
    _save_cart(cart_items)
    return redirect(url_for('checkout'))


@app.route('/cart/add/<int:id>', methods=('POST',))
def add_to_cart(id):
    if 'user_id' not in session:
        flash('Please sign in to start shopping.', 'error')
        return redirect(url_for('login', next=url_for('product_detail', id=id)))

    try:
        amount = float(request.form.get('quantity', '1'))
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError
    except ValueError:
        flash('Enter a valid quantity.', 'error')
        return redirect(url_for('product_detail', id=id))

    conn = get_db_connection()
    item = conn.execute(
        'SELECT * FROM items WHERE id = ? AND COALESCE(active, 1) = 1', (id,)
    ).fetchone()
    conn.close()
    if not item:
        abort(404)

    if item['listing_type'] == 'auction':
        flash('This item is up for auction. Place a bid instead.', 'error')
        return redirect(url_for('product_detail', id=id) + '#bid-box')

    unit = _normalise_unit(item['unit'])
    available = float(item['quantity'])
    if float(item['price'] or 0) <= 0:
        flash('This product is not available for sale yet.', 'error')
        return redirect(url_for('product_detail', id=id))
    if available <= 0:
        flash(f'{item["name"]} is out of stock.', 'error')
        return redirect(url_for('product_detail', id=id))

    cart_items = _get_cart()
    new_quantity = cart_items.get(id, 0) + amount
    if new_quantity > available:
        flash(
            f'Not enough stock for {item["name"]}. Please reduce the quantity.',
            'error',
        )
        return redirect(url_for('product_detail', id=id))

    cart_items[id] = round(new_quantity, 6)
    _save_cart(cart_items)
    flash(f'Added {_format_quantity(amount)} {unit} of {item["name"]} to your cart.', 'success')
    return redirect(url_for('cart'))


@app.route('/cart/update/<int:id>', methods=('POST',))
def update_cart(id):
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('cart')))

    cart_items = _get_cart()
    if id not in cart_items:
        return redirect(url_for('cart'))

    try:
        amount = float(request.form.get('quantity', ''))
        if not math.isfinite(amount):
            raise ValueError
    except ValueError:
        flash('Enter a valid quantity.', 'error')
        return redirect(url_for('cart'))

    if amount <= 0:
        cart_items.pop(id, None)
        _save_cart(cart_items)
        flash('Item removed from your cart.', 'success')
        return redirect(url_for('cart'))

    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()
    conn.close()
    if not item:
        cart_items.pop(id, None)
        _save_cart(cart_items)
        flash('That product is no longer available.', 'error')
        return redirect(url_for('cart'))

    available = float(item['quantity'])
    if amount > available:
        flash(
            f'Not enough stock for {item["name"]}. Please reduce the quantity.',
            'error',
        )
        return redirect(url_for('cart'))

    cart_items[id] = round(amount, 6)
    _save_cart(cart_items)
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:id>', methods=('POST',))
def remove_from_cart(id):
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('cart')))
    cart_items = _get_cart()
    cart_items.pop(id, None)
    _save_cart(cart_items)
    flash('Item removed from your cart.', 'success')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=('GET', 'POST'))
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('checkout')))

    totals = _cart_totals()
    lines = totals['lines']
    if not lines:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    subtotal_cents = totals['subtotal_cents']
    shipping_cents = totals['shipping_cents']
    discount_cents = totals['discount_cents']
    total_cents = totals['total_cents']
    coupon = totals['coupon']
    coupon_code = totals['coupon_code']
    values = {
        'full_name': session.get('username', ''),
        'email': user['email'] if user else '',
        'phone': '',
        'address_line1': '',
        'address_line2': '',
        'city': '',
        'state': '',
        'postal_code': '',
        'country': 'United States',
        'payment_method': 'cod',
    }
    error = None

    if request.method == 'POST':
        for field in values:
            values[field] = request.form.get(field, '').strip()
        payment_method = request.form.get('payment_method', 'cod').strip()

        if not values['full_name'] or not values['email'] or not values['address_line1'] or not values['city'] or not values['country']:
            error = 'Name, email, address, city, and country are required.'
        elif '@' not in values['email']:
            error = 'Enter a valid email address.'
        else:
            for line in lines:
                if line['quantity'] > float(line['item']['quantity']):
                    error = f'Not enough stock for {line["item"]["name"]}. Please update your cart.'
                    break

        if not error:
            tracking_num = 'CHEM-FDX-' + secrets.token_hex(4).upper()
            est_delivery = (datetime.now() + timedelta(days=3)).strftime('%A, %b %d')
            initial_status = 'pending'
            initial_payment = 'unpaid'

            conn = get_db_connection()
            cursor = conn.execute(
                '''INSERT INTO orders (
                       user_id, email, full_name, phone, address_line1, address_line2,
                       city, state, postal_code, country, subtotal_cents,
                       shipping_cents, discount_cents, coupon_code, total_cents,
                       status, payment_status, payment_method, carrier, tracking_number,
                       estimated_delivery
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    session['user_id'], values['email'], values['full_name'],
                    values['phone'], values['address_line1'], values['address_line2'],
                    values['city'], values['state'], values['postal_code'],
                    values['country'], subtotal_cents, shipping_cents,
                    discount_cents, coupon_code or None, total_cents,
                    initial_status, initial_payment, payment_method,
                    'Pakistan Post', tracking_num, est_delivery
                ),
            )
            order_id = cursor.lastrowid
            for line in lines:
                item = line['item']
                conn.execute(
                    '''INSERT INTO order_items (
                           order_id, item_id, name, unit, quantity,
                           unit_price_cents, line_total_cents
                       ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        order_id, item['id'], item['name'], _normalise_unit(item['unit']),
                        line['quantity'], line['unit_price_cents'], line['line_total_cents'],
                    ),
                )
            conn.commit()

            # Deduct stock for Cash on Delivery order
            for line in lines:
                if line['item']['id'] is not None:
                    conn.execute(
                        '''UPDATE items
                           SET quantity = CASE WHEN quantity - ? < 0 THEN 0 ELSE quantity - ? END
                           WHERE id = ?''',
                        (line['quantity'], line['quantity'], line['item']['id'])
                    )
            conn.commit()
            conn.close()
            session.pop('coupon_code', None)
            _save_cart({})
            flash('Your order has been placed successfully!', 'success')
            return redirect(url_for('checkout_success') + f'?order_id={order_id}')

    return render_template(
        'checkout.html',
        **totals,
        values=values,
        error=error,
    )


@app.route('/checkout/success')
def checkout_success():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('orders')))

    order_id_param = request.args.get('order_id', '').strip()
    conn = get_db_connection()
    order = None

    if order_id_param and order_id_param.isdigit():
        order = conn.execute(
            'SELECT * FROM orders WHERE id = ? AND user_id = ?',
            (int(order_id_param), session['user_id']),
        ).fetchone()

    if not order:
        pending_id = session.get('pending_order_id')
        if pending_id:
            order = conn.execute(
                'SELECT * FROM orders WHERE id = ? AND user_id = ?',
                (pending_id, session['user_id']),
            ).fetchone()
    conn.close()

    if not order:
        flash('We could not find that order.', 'error')
        return redirect(url_for('orders'))

    conn = get_db_connection()
    items = conn.execute(
        'SELECT * FROM order_items WHERE order_id = ? ORDER BY id', (order['id'],)
    ).fetchall()
    conn.close()
    return render_template(
        'checkout_success.html',
        order=order,
        items=items,
        paid=order['payment_status'] == 'paid',
    )


@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('orders')))
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC',
        (session['user_id'],),
    ).fetchall()
    conn.close()
    return render_template('orders.html', orders=rows, admin_view=False)


@app.route('/orders/<int:order_id>')
def order_detail(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('orders')))
    conn = get_db_connection()
    if session.get('role') in ('Developer', 'Admin'):
        order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    else:
        order = conn.execute(
            'SELECT * FROM orders WHERE id = ? AND user_id = ?',
            (order_id, session['user_id']),
        ).fetchone()
    if not order:
        conn.close()
        abort(404)
    items = conn.execute(
        'SELECT * FROM order_items WHERE order_id = ? ORDER BY id', (order_id,)
    ).fetchall()
    conn.close()
    return render_template(
        'order_detail.html',
        order=order,
        items=items,
        admin_view=session.get('role') in ('Developer', 'Admin'),
        order_statuses=ORDER_STATUSES,
    )


@app.route('/account')
def account():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('account')))
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    recent_orders = conn.execute(
        'SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 4',
        (session['user_id'],),
    ).fetchall()
    order_count = conn.execute(
        'SELECT COUNT(*) FROM orders WHERE user_id = ?', (session['user_id'],)
    ).fetchone()[0]
    wishlist_items = conn.execute(
        '''SELECT i.*,
                  (SELECT AVG(r.rating) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS avg_rating,
                  (SELECT COUNT(*) FROM reviews r WHERE r.item_id = i.id AND r.approved = 1) AS review_count
           FROM wishlist w JOIN items i ON i.id = w.item_id
           WHERE w.user_id = ? AND COALESCE(i.active, 1) = 1
           ORDER BY w.id DESC LIMIT 4''',
        (session['user_id'],),
    ).fetchall()
    wishlist_total = conn.execute(
        'SELECT COUNT(*) FROM wishlist w JOIN items i ON i.id = w.item_id WHERE w.user_id = ? AND COALESCE(i.active, 1) = 1',
        (session['user_id'],),
    ).fetchone()[0]
    review_count = conn.execute(
        'SELECT COUNT(*) FROM reviews WHERE user_id = ?', (session['user_id'],)
    ).fetchone()[0]
    conn.close()
    return render_template(
        'account.html',
        account_user=user,
        recent_orders=recent_orders,
        order_count=order_count,
        wishlist_items=wishlist_items,
        wishlist_count=wishlist_total,
        review_count=review_count,
    )


INFO_PAGES = {
    'about': {
        'eyebrow': 'About us',
        'title': 'Chemicals without the runaround',
        'intro': 'ChemStore Market brings everyday chemicals, clear pricing, and dependable delivery together in one straightforward online store.',
        'sections': [
            ('What we do', [
                'We stock a focused catalog of commonly used chemicals for workshops, facilities, cleaning teams, and production environments.',
                'Every listing shows the exact selling unit, current availability, and a transparent price so you know what you are ordering before checkout.',
            ]),
            ('How we work', [
                'Orders are checked against live stock, packed by our team, and tracked from payment through delivery.',
                'Our support team is available for product questions, bulk requirements, and order help.',
            ]),
        ],
    },
    'help': {
        'eyebrow': 'Customer service',
        'title': 'How can we help?',
        'intro': 'Find quick answers about ordering, payment, delivery, and account access.',
        'sections': [
            ('Ordering', [
                'Create a customer account, browse the catalog, choose your quantity, and add products to your cart.',
                'You can review and update quantities in the cart before continuing to secure payment.',
            ]),
            ('Payments', [
                'Orders are placed with Cash on Delivery. Pay by invoice, bank transfer, or on delivery.',
                'You will receive an order confirmation after payment is confirmed.',
            ]),
            ('Account access', [
                'Use the Forgot password link on the sign-in page to reset your password by email.',
                'If you still cannot access your account, contact support with your registered email address.',
            ]),
        ],
    },
    'shipping': {
        'eyebrow': 'Shipping information',
        'title': 'Delivery you can plan around',
        'intro': 'We prepare paid orders promptly and keep you updated as your parcel moves.',
        'sections': [
            ('Processing', [
                'Orders are usually processed within one business day after payment is confirmed.',
                'You will receive an email when your order status changes to shipped.',
            ]),
            ('Delivery', [
                'Delivery times depend on your location and the carrier. Tracking information is added to your order when available.',
                'Shipping charges, if any, are shown in the cart and at checkout before you pay.',
            ]),
        ],
    },
    'returns': {
        'eyebrow': 'Returns and refunds',
        'title': 'Clear, fair returns',
        'intro': 'If something is wrong with your order, contact us quickly so we can make it right.',
        'sections': [
            ('Damaged or incorrect items', [
                'Report damaged, leaking, or incorrect items within 48 hours of delivery and include photos where possible.',
                'We will arrange a replacement or refund after reviewing the issue.',
            ]),
            ('Unopened products', [
                'Unopened products in their original packaging may be eligible for return within 14 days of delivery.',
                'For safety and regulatory reasons, opened chemicals cannot normally be returned.',
            ]),
        ],
    },
    'privacy': {
        'eyebrow': 'Privacy',
        'title': 'Your data, handled carefully',
        'intro': 'We collect only the information needed to run your account, process orders, and provide support.',
        'sections': [
            ('What we collect', [
                'Account details such as your name, email address, and username; order and delivery details; and messages you send to support.',
                'Payment is by Cash on Delivery. No card details are stored by ChemStore Market.',
            ]),
            ('How we use it', [
                'We use your information to fulfil orders, provide customer service, prevent fraud, and meet legal obligations.',
                'We do not sell your personal information.',
            ]),
        ],
    },
    'terms': {
        'eyebrow': 'Terms of service',
        'title': 'Shopping terms',
        'intro': 'By using ChemStore Market you agree to the terms below.',
        'sections': [
            ('Orders and pricing', [
                'Product availability and pricing are shown on the storefront and may change without notice.',
                'We may cancel an order if stock is unavailable, payment cannot be verified, or an error is identified; any captured payment will be refunded.',
            ]),
            ('Safe handling', [
                'You are responsible for storing, handling, using, and disposing of purchased chemicals in accordance with applicable laws, safety guidance, and product instructions.',
                'Only purchase products you are qualified and authorised to handle.',
            ]),
        ],
    },
}


@app.route('/info/<page>')
def info_page(page):
    content = INFO_PAGES.get(page)
    if not content:
        abort(404)
    return render_template('info.html', page_key=page, content=content)


@app.route('/contact', methods=('GET', 'POST'))
def contact():
    error = None
    success = None
    values = {
        'name': session.get('username', ''),
        'email': '',
        'subject': request.args.get('subject', '').strip()[:200],
        'message': '',
    }
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        if user:
            values['email'] = user['email']
    if request.method == 'POST':
        for field in values:
            values[field] = request.form.get(field, '').strip()
        if not values['name'] or not values['email'] or not values['message']:
            error = 'Name, email, and message are required.'
        elif '@' not in values['email']:
            error = 'Enter a valid email address.'
        else:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO contact_messages (name, email, subject, message) VALUES (?, ?, ?, ?)',
                (values['name'], values['email'], values['subject'], values['message']),
            )
            conn.commit()
            conn.close()
            success = 'Thanks for reaching out. Our team will reply by email.'
            values = {'name': '', 'email': '', 'subject': '', 'message': ''}
    return render_template('contact.html', values=values, error=error, success=success)


@app.route('/admin/orders')
def admin_orders():
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('orders.html', orders=rows, admin_view=True)


@app.route('/admin/orders/<int:order_id>/status', methods=('POST',))
def admin_order_status(order_id):
    if session.get('role') not in ('Developer', 'Admin'):
        if _is_ajax():
            return _json_response(False, 'You do not have permission to update orders.', 403)
        return redirect(url_for('store'))
    status = request.form.get('status', '').strip()
    if status not in ORDER_STATUSES:
        flash('Choose a valid order status.', 'error')
        return redirect(url_for('order_detail', order_id=order_id))
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.execute(
        'UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (status, order_id),
    )
    conn.commit()
    conn.close()
    if order and status in ('shipped', 'completed') and order['payment_status'] == 'paid':
        _send_email(
            order['email'],
            f'ChemStore Market order #{order_id} is {status}',
            f'Your order #{order_id} is now marked as {status}.\n\n'
            'You can view your order details by signing in to your ChemStore Market account.',
        )
    flash('Order status updated.', 'success')
    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/admin/customers')
def admin_customers():
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    conn = get_db_connection()
    rows = conn.execute(
        '''SELECT u.*,
                  (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count,
                  (SELECT COALESCE(SUM(o.total_cents), 0) FROM orders o
                   WHERE o.user_id = u.id AND o.payment_status = 'paid') AS spend_cents
           FROM users u ORDER BY u.id'''
    ).fetchall()
    conn.close()
    return render_template('admin_customers.html', users=rows)


@app.route('/admin/reviews')
def admin_reviews():
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    conn = get_db_connection()
    rows = conn.execute(
        '''SELECT r.*, u.username, i.name AS item_name
           FROM reviews r JOIN users u ON u.id = r.user_id
           JOIN items i ON i.id = r.item_id
           ORDER BY r.id DESC'''
    ).fetchall()
    conn.close()
    return render_template('admin_reviews.html', reviews=rows)


@app.route('/admin/reviews/<int:review_id>/toggle', methods=('POST',))
def admin_review_toggle(review_id):
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    conn = get_db_connection()
    review = conn.execute('SELECT * FROM reviews WHERE id = ?', (review_id,)).fetchone()
    if review:
        conn.execute('UPDATE reviews SET approved = ? WHERE id = ?', (0 if review['approved'] else 1, review_id))
        conn.commit()
    conn.close()
    flash('Review visibility updated.', 'success')
    return redirect(url_for('admin_reviews'))


@app.route('/admin/reviews/<int:review_id>/delete', methods=('POST',))
def admin_review_delete(review_id):
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    conn = get_db_connection()
    conn.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
    conn.commit()
    conn.close()
    flash('Review deleted.', 'success')
    return redirect(url_for('admin_reviews'))


@app.route('/admin/coupons', methods=('GET', 'POST'))
def admin_coupons():
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    error = None
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        discount_type = request.form.get('discount_type', 'percent')
        value_raw = request.form.get('value', '').strip()
        min_raw = request.form.get('min_subtotal', '').strip() or '0'
        max_uses_raw = request.form.get('max_uses', '').strip() or '0'
        expires_raw = request.form.get('expires_at', '').strip()
        try:
            value = float(value_raw)
            min_subtotal = max(0, _money_to_cents(min_raw))
            max_uses = max(0, int(max_uses_raw))
        except ValueError:
            value = -1
            min_subtotal = 0
            max_uses = 0
        if not code or len(code) < 3:
            error = 'Enter a coupon code with at least 3 characters.'
        elif discount_type not in ('percent', 'fixed'):
            error = 'Choose percent or fixed discount.'
        elif value <= 0 or (discount_type == 'percent' and value > 100):
            error = 'Enter a valid discount value.'
        else:
            expires_at = f'{expires_raw} 23:59:59' if expires_raw else None
            conn = get_db_connection()
            try:
                conn.execute(
                    '''INSERT INTO coupons (code, discount_type, value, min_subtotal_cents,
                       active, expires_at, max_uses) VALUES (?, ?, ?, ?, 1, ?, ?)''',
                    (code, discount_type, value, min_subtotal, expires_at, max_uses),
                )
                conn.commit()
                flash(f'Coupon {code} created.', 'success')
            except sqlite3.IntegrityError:
                error = 'That coupon code already exists.'
            conn.close()
            if not error:
                return redirect(url_for('admin_coupons'))
    conn = get_db_connection()
    coupons = conn.execute('SELECT * FROM coupons ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin_coupons.html', coupons=coupons, error=error)


@app.route('/admin/coupons/<int:coupon_id>/toggle', methods=('POST',))
def admin_coupon_toggle(coupon_id):
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    conn = get_db_connection()
    coupon = conn.execute('SELECT * FROM coupons WHERE id = ?', (coupon_id,)).fetchone()
    if coupon:
        conn.execute('UPDATE coupons SET active = ? WHERE id = ?', (0 if coupon['active'] else 1, coupon_id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_coupons'))


@app.route('/admin/coupons/<int:coupon_id>/delete', methods=('POST',))
def admin_coupon_delete(coupon_id):
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    conn = get_db_connection()
    conn.execute('DELETE FROM coupons WHERE id = ?', (coupon_id,))
    conn.commit()
    conn.close()
    flash('Coupon deleted.', 'success')
    return redirect(url_for('admin_coupons'))


@app.route('/admin/messages')
def admin_messages():
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM contact_messages ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin_messages.html', messages=rows)


@app.route('/admin/messages/<int:message_id>/status', methods=('POST',))
def admin_message_status(message_id):
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    status = request.form.get('status', 'read')
    if status not in ('new', 'read', 'archived'):
        status = 'read'
    conn = get_db_connection()
    conn.execute('UPDATE contact_messages SET status = ? WHERE id = ?', (status, message_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_messages'))


@app.route('/admin/messages/<int:message_id>/delete', methods=('POST',))
def admin_message_delete(message_id):
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    conn = get_db_connection()
    conn.execute('DELETE FROM contact_messages WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin_messages'))


@app.route('/admin/settings', methods=('GET', 'POST'))
def admin_settings():
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    message = None
    error = None
    if request.method == 'POST':
        if request.form.get('action') == 'test_email':
            target = request.form.get('test_email', '').strip()
            if not target:
                error = 'Enter an email address for the test message.'
            else:
                sent, detail = _send_email(
                    target,
                    'ChemStore Market test email',
                    'This is a test message from your ChemStore Market store settings.',
                )
                if sent:
                    message = f'Test email sent to {target}.'
                else:
                    error = f'Could not send the test email: {detail}'
        else:
            for key in ('smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'smtp_from', 'smtp_security', 'support_email'):
                if key in request.form:
                    _set_setting(key, request.form.get(key, '').strip())
            message = 'Store settings saved.'
    smtp = _get_smtp_config()
    settings = {
        'smtp_host': smtp['host'],
        'smtp_port': smtp['port'],
        'smtp_user': smtp['user'],
        'smtp_password': smtp['password'],
        'smtp_from': smtp['from'],
        'smtp_security': smtp['security'],
        'support_email': _get_setting('support_email', STORE_SUPPORT_EMAIL),
    }
    return render_template('admin_settings.html', settings=settings, message=message, error=error)


@app.route('/admin')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('index')))
    if session.get('role') not in ('Developer', 'Admin'):
        return redirect(url_for('store'))
    return render_template('index.html', **_dashboard_context(request.args.get('q', '')))


@app.route('/api/dashboard')
def dashboard_data():
    if 'user_id' not in session:
        return _json_response(False, 'Your session has expired. Please sign in again.', 401)

    context = _dashboard_context()
    return _json_response(
        True,
        'Dashboard updated.',
        stats=context['stats'],
        activity=context['activity'],
        counts={
            'pending_admins': len(context['pending_admins']),
            'pending_users': len(context['pending_users']),
        },
        updated_at=datetime.now().strftime('%H:%M:%S'),
        inventory_html=render_template('partials/inventory_rows.html', **context),
        logs_html=render_template('partials/logs_rows.html', **context),
        users_html=render_template('partials/users_rows.html', **context),
        pending_admins_html=render_template('partials/pending_admins_rows.html', **context),
        pending_users_html=render_template('partials/pending_users_rows.html', **context),
    )

@app.route('/profile', methods=('GET', 'POST'))
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    error = None
    success = None
    
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        old_profile_pic = user['profile_pic']
        profile_pic_filename = old_profile_pic
        saved_pic = None

        if not new_username or not new_email:
            error = "Username and email are required."
        elif new_password:
            if not current_password or not check_password_hash(user['password'], current_password):
                error = "Incorrect current password provided."
            elif len(new_password) < 6:
                error = "New password must be at least 6 characters long."

        file = request.files.get('profile_pic')
        if error is None and file and file.filename:
            if not _allowed_image(file.filename):
                error = "Profile picture must be a PNG, JPG, JPEG, GIF, or WEBP image."
            else:
                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"user_{session['user_id']}_{secrets.token_hex(4)}.{extension}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_pic_filename = filename
                saved_pic = filename

        if error is None:
            try:
                if new_password:
                    hashed_pw = generate_password_hash(new_password)
                    conn.execute('''
                        UPDATE users SET username = ?, email = ?, password = ?, profile_pic = ? WHERE id = ?
                    ''', (new_username, new_email, hashed_pw, profile_pic_filename, session['user_id']))
                    success = "Profile and password updated successfully!"
                else:
                    conn.execute('''
                        UPDATE users SET username = ?, email = ?, profile_pic = ? WHERE id = ?
                    ''', (new_username, new_email, profile_pic_filename, session['user_id']))
                    success = "Profile updated successfully!"

                conn.commit()
                session['username'] = new_username
                user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
                if saved_pic:
                    _remove_upload(old_profile_pic)
            except sqlite3.IntegrityError:
                conn.rollback()
                _remove_upload(saved_pic)
                error = "Username or Email is already taken by another account."

    conn.close()

    if _is_ajax() and request.method == 'POST':
        if error:
            return _json_response(False, error, 400)
        profile_pic_url = None
        if user['profile_pic'] and user['profile_pic'] != 'default.png':
            profile_pic_url = url_for('uploaded_file', filename=user['profile_pic'])
        return _json_response(
            True,
            success,
            username=user['username'],
            email=user['email'],
            profile_pic_url=profile_pic_url,
        )

    return render_template('profile.html', user=user, error=error, success=success)

@app.route('/approve/<int:user_id>', methods=('POST',))
def approve_user(user_id):
    if 'user_id' not in session:
        if _is_ajax():
            return _json_response(False, 'Please sign in again.', 401)
        return redirect(url_for('login'))

    conn = get_db_connection()
    target_user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    role = session.get('role')

    if not target_user:
        conn.close()
        if _is_ajax():
            return _json_response(False, 'That account no longer exists.', 404)
        return redirect(url_for('index'))

    allowed = (
        (target_user['role'] == 'Admin' and role == 'Developer')
        or (target_user['role'] == 'User' and role in ['Developer', 'Admin'])
    )
    if not allowed:
        conn.close()
        if _is_ajax():
            return _json_response(False, 'You do not have permission to approve that account.', 403)
        return redirect(url_for('index'))

    conn.execute('UPDATE users SET approved = 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    if _is_ajax():
        return _json_response(True, f'{target_user["username"]} approved successfully.')
    return redirect(url_for('index'))


@app.route('/reject/<int:user_id>', methods=('POST',))
def reject_user(user_id):
    if 'user_id' not in session:
        if _is_ajax():
            return _json_response(False, 'Please sign in again.', 401)
        return redirect(url_for('login'))

    conn = get_db_connection()
    target_user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    role = session.get('role')

    if not target_user:
        conn.close()
        if _is_ajax():
            return _json_response(False, 'That account no longer exists.', 404)
        return redirect(url_for('index'))

    allowed = (
        (target_user['role'] == 'Admin' and role == 'Developer')
        or (target_user['role'] == 'User' and role in ['Developer', 'Admin'])
    )
    if not allowed:
        conn.close()
        if _is_ajax():
            return _json_response(False, 'You do not have permission to reject that account.', 403)
        return redirect(url_for('index'))

    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    if _is_ajax():
        return _json_response(True, f'{target_user["username"]} rejected and removed.')
    return redirect(url_for('index'))

def _clear_reset_session():
    for key in ('reset_email', 'reset_otp', 'reset_otp_expires', 'reset_otp_attempts'):
        session.pop(key, None)


@app.route('/forgot-password', methods=('GET', 'POST'))
def forgot_password():
    error = None
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE (email = ? OR username = ?) AND approved = 1',
            (identifier, identifier),
        ).fetchone()
        conn.close()

        if user:
            otp = str(secrets.randbelow(900000) + 100000)
            session['reset_email'] = user['email']
            session['reset_otp'] = otp
            session['reset_otp_expires'] = time.time() + OTP_TTL_SECONDS
            session['reset_otp_attempts'] = 0
            if send_otp_email(user['email'], otp):
                return redirect(url_for('verify_otp'))
            _clear_reset_session()
            error = (
                'We could not send the reset email. Please ask an administrator to '
                'configure email delivery in Store settings, then try again.'
            )
        else:
            error = "No approved account found with that email or username."
            
    return render_template('forgot_password.html', error=error)


@app.route('/verify-otp', methods=('GET', 'POST'))
def verify_otp():
    if 'reset_email' not in session:
        return redirect(url_for('forgot_password'))
        
    error = None
    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '')
        expected_otp = session.get('reset_otp')
        expires = session.get('reset_otp_expires', 0)
        attempts = session.get('reset_otp_attempts', 0)

        if time.time() > expires:
            _clear_reset_session()
            error = "OTP has expired. Please request a new one."
        elif attempts >= OTP_MAX_ATTEMPTS:
            _clear_reset_session()
            error = "Too many invalid OTP attempts. Please request a new one."
        elif len(new_password) < 6:
            error = "New password must be at least 6 characters long."
        elif expected_otp and secrets.compare_digest(entered_otp, expected_otp):
            hashed_pw = generate_password_hash(new_password)
            conn = get_db_connection()
            conn.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_pw, session['reset_email']))
            conn.commit()
            conn.close()
            _clear_reset_session()
            flash('Password reset successful. Please sign in.', 'success')
            return redirect(url_for('login'))
        else:
            session['reset_otp_attempts'] = attempts + 1
            error = "Invalid OTP code. Please try again."
            
    return render_template('verify_otp.html', error=error)

@app.route('/login', methods=('GET', 'POST'))
def login():
    error = None
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        failure_key = f"{request.remote_addr}:{identifier.lower()}"
        if _is_login_blocked(failure_key):
            error = 'Too many failed login attempts. Please wait a few minutes and try again.'
            if _is_ajax():
                return _json_response(False, error, 429)
            return render_template('login.html', error=error)

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? OR username = ?', (identifier, identifier)).fetchone()
        conn.close()
        
        if user:
            if check_password_hash(user['password'], password):
                if user['approved'] == 0:
                    error = 'Your account is pending approval by an administrator.'
                else:
                    db_role = user['role']
                    LOGIN_FAILURES.pop(failure_key, None)
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = db_role
                    destination = _login_next_url(
                        'index' if db_role in ('Developer', 'Admin') else 'store'
                    )
                    if _is_ajax():
                        return _json_response(
                            True,
                            f'Welcome back, {user["username"]}!',
                            redirect=destination,
                        )
                    return redirect(destination)
            else:
                _record_login_failure(failure_key)
                error = 'Incorrect password.'
        else:
            _record_login_failure(failure_key)
            register_url = url_for('register', email=identifier)
            if _is_ajax():
                return _json_response(
                    True,
                    'No account found with those details. Opening registration...',
                    redirect=register_url,
                )
            return redirect(register_url)

    if _is_ajax() and error:
        return _json_response(False, error, 400)
    return render_template('login.html', error=error)

@app.route('/register', methods=('GET', 'POST'))
def register():
    prefill_email = request.args.get('email', '').strip()
    prefill_role = request.args.get('role', 'User').strip()
    if prefill_role not in ('User', 'Admin'):
        prefill_role = 'User'
    error = None
    success = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        username = request.form.get('username', '').strip()
        role = request.form.get('role', 'User').strip()
        if role not in ('User', 'Admin'):
            role = 'User'

        if len(password) < 8:
            error = 'Password must be at least 8 characters long.'
        elif not email or not username:
            error = 'Email and username are required.'
        else:
            approved = 1 if role == 'User' else 0
            conn = get_db_connection()
            try:
                conn.execute(
                    'INSERT INTO users (email, username, password, role, profile_pic, approved) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (email, username, generate_password_hash(password), role, 'default.png', approved),
                )
                conn.commit()
                if role == 'Admin':
                    success = 'Admin request submitted. A Developer must approve the account before sign-in.'
                else:
                    success = 'Your customer account has been registered. Sign in to start shopping.'
            except sqlite3.IntegrityError:
                error = 'Email or Username is already taken.'
            finally:
                conn.close()

    if _is_ajax() and request.method == 'POST':
        if error:
            return _json_response(False, error, 400)
        flash(success, 'success')
        return _json_response(True, success, redirect=url_for('login'))

    return render_template(
        'register.html',
        prefill_email=email if request.method == 'POST' else prefill_email,
        prefill_role=role if request.method == 'POST' else prefill_role,
        error=error,
        success=success,
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add', methods=('POST',))
def add_chemical():
    if session.get('role') not in ['Developer', 'Admin']:
        if _is_ajax():
            return _json_response(False, 'You do not have permission to add products.', 403)
        return redirect(url_for('index'))

    code = request.form.get('code', '').strip()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    quantity_raw = request.form.get('quantity', '').strip()
    unit = request.form.get('unit', DEFAULT_UNIT).strip() or DEFAULT_UNIT
    price_raw = request.form.get('price', '').strip() or '0'
    description = request.form.get('description', '').strip()
    image_url = request.form.get('image_url', '').strip()
    featured = 1 if request.form.get('featured') in ('1', 'on', 'true') else 0
    image_file = request.files.get('image_file')

    if unit not in CHEMICAL_UNITS:
        message = 'Choose a valid unit (L, mL, kg, or g).'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    try:
        quantity = float(quantity_raw)
        price = float(price_raw)
        if not math.isfinite(quantity) or quantity < 0:
            raise ValueError
        if not math.isfinite(price) or price < 0:
            raise ValueError
    except ValueError:
        message = 'Quantity and price must be non-negative numbers.'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    if not code or not name or not category:
        message = 'Code, name, and category are required.'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    existing = conn.execute(
        'SELECT id FROM items WHERE UPPER(TRIM(code)) = ?', (code.upper(),)
    ).fetchone()
    conn.close()
    if existing:
        message = 'A product with that code already exists.'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    saved_image_url = None
    if image_file and image_file.filename:
        if not _allowed_image(image_file.filename):
            message = 'Product image must be a PNG, JPG, JPEG, GIF, or WEBP file.'
            if _is_ajax():
                return _json_response(False, message, 400)
            flash(message, 'error')
            return redirect(url_for('index'))
        saved_image_url = _save_image_upload(image_file, 'product')
        if saved_image_url:
            image_url = saved_image_url

    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO items (code, name, category, quantity, unit, price, description, image_url, featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, name, category, quantity, unit, price, description, image_url, featured))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        _remove_upload(saved_image_url)
        message = 'A product with that code already exists.'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))
    finally:
        conn.close()

    message = f'Product "{name}" added successfully.'
    if _is_ajax():
        return _json_response(True, message)
    flash(message, 'success')
    return redirect(url_for('index'))


@app.route('/product/<int:id>/edit', methods=('POST',))
def edit_product(id):
    if session.get('role') not in ['Developer', 'Admin']:
        if _is_ajax():
            return _json_response(False, 'You do not have permission to edit products.', 403)
        return redirect(url_for('store'))

    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    price_raw = request.form.get('price', '').strip() or '0'
    description = request.form.get('description', '').strip()
    image_url = request.form.get('image_url', '').strip()
    active = 1 if request.form.get('active', '1') in ('1', 'on', 'true') else 0
    featured = 1 if request.form.get('featured') in ('1', 'on', 'true') else 0
    image_file = request.files.get('image_file')

    if not name or not category:
        message = 'Name and category are required.'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    try:
        price = float(price_raw)
        if not math.isfinite(price) or price < 0:
            raise ValueError
    except ValueError:
        message = 'Price must be a non-negative number.'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    saved_image_url = None
    if image_file and image_file.filename:
        if not _allowed_image(image_file.filename):
            message = 'Product image must be a PNG, JPG, JPEG, GIF, or WEBP file.'
            if _is_ajax():
                return _json_response(False, message, 400)
            flash(message, 'error')
            return redirect(url_for('index'))
        saved_image_url = _save_image_upload(image_file, 'product')
        if saved_image_url:
            image_url = saved_image_url

    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()
    if not item:
        conn.close()
        _remove_upload(saved_image_url)
        message = 'Product not found.'
        if _is_ajax():
            return _json_response(False, message, 404)
        flash(message, 'error')
        return redirect(url_for('index'))

    conn.execute(
        '''UPDATE items
           SET name = ?, category = ?, price = ?, description = ?, image_url = ?,
               active = ?, featured = ?
           WHERE id = ?''',
        (name, category, price, description, image_url, active, featured, id),
    )
    conn.commit()
    conn.close()
    if saved_image_url:
        _remove_upload(item['image_url'])

    message = f'Product "{name}" updated.'
    if _is_ajax():
        return _json_response(True, message)
    flash(message, 'success')
    return redirect(url_for('index'))


@app.route('/restock/<int:id>', methods=('POST',))
def restock_chemical(id):
    if session.get('role') not in ['Developer', 'Admin']:
        if _is_ajax():
            return _json_response(False, 'You do not have permission to add stock.', 403)
        return redirect(url_for('index'))

    try:
        amount_added = float(request.form.get('amount_added', ''))
        if not math.isfinite(amount_added) or amount_added <= 0:
            raise ValueError
    except ValueError:
        message = 'Amount to add must be a positive number.'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()
    if not item:
        conn.close()
        message = 'Product not found.'
        if _is_ajax():
            return _json_response(False, message, 404)
        flash(message, 'error')
        return redirect(url_for('index'))

    unit = _normalise_unit(item['unit'])
    new_qty = round(float(item['quantity']) + amount_added, 6)
    conn.execute('UPDATE items SET quantity = ? WHERE id = ?', (new_qty, id))
    conn.commit()
    conn.close()

    message = (
        f'Added {_format_quantity(amount_added)} {unit} to "{item["name"]}". '
        f'New stock: {_format_quantity(new_qty)} {unit}.'
    )
    if _is_ajax():
        return _json_response(
            True, message, quantity=new_qty, unit=unit, item_name=item['name']
        )
    flash(message, 'success')
    return redirect(url_for('index'))


@app.route('/delete/<int:id>', methods=('POST',))
def delete_chemical(id):
    if session.get('role') not in ['Developer', 'Admin']:
        if _is_ajax():
            return _json_response(False, 'You do not have permission to delete products.', 403)
        return redirect(url_for('index'))

    conn = get_db_connection()
    item = conn.execute('SELECT name, image_url FROM items WHERE id = ?', (id,)).fetchone()
    if not item:
        conn.close()
        if _is_ajax():
            return _json_response(False, 'That product no longer exists.', 404)
        return redirect(url_for('index'))

    conn.execute('DELETE FROM items WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    _remove_upload(item['image_url'])

    message = f'Product "{item["name"]}" deleted.'
    if _is_ajax():
        return _json_response(True, message)
    return redirect(url_for('index'))

@app.route('/remove-user/<int:user_id>', methods=('POST',))
def remove_user(user_id):
    role = session.get('role')
    if role not in ['Developer', 'Admin']:
        if _is_ajax():
            return _json_response(False, 'You do not have permission to remove members.', 403)
        return redirect(url_for('index'))

    conn = get_db_connection()
    target_user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if not target_user:
        conn.close()
        if _is_ajax():
            return _json_response(False, 'That member no longer exists.', 404)
        return redirect(url_for('index'))

    # Developers cannot be removed; only a Developer may remove an Admin.
    if target_user['role'] == 'Developer' or (
        target_user['role'] == 'Admin' and role != 'Developer'
    ):
        conn.close()
        if _is_ajax():
            return _json_response(False, 'You do not have permission to remove that member.', 403)
        return redirect(url_for('index'))

    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    message = f'{target_user["username"]} removed.'
    if _is_ajax():
        return _json_response(True, message)
    return redirect(url_for('index'))


@app.route('/use/<int:id>', methods=('POST',))
def use_stock(id):
    if 'user_id' not in session:
        if _is_ajax():
            return _json_response(False, 'Please sign in again.', 401)
        return redirect(url_for('login'))

    try:
        amount_used = float(request.form.get('amount_used', ''))
    except ValueError:
        message = 'Amount used must be a valid number.'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    purpose = request.form.get('purpose', '').strip()

    if not math.isfinite(amount_used) or amount_used <= 0 or not purpose:
        message = 'Enter a positive amount and a purpose.'
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()

    if not item:
        conn.close()
        message = 'Product not found.'
        if _is_ajax():
            return _json_response(False, message, 404)
        flash(message, 'error')
        return redirect(url_for('index'))

    unit = _normalise_unit(item['unit'])
    available = float(item['quantity'])
    if amount_used > available:
        conn.close()
        message = (
            f'Cannot use {_format_quantity(amount_used)} {unit}; '
            f'only {_format_quantity(available)} {unit} in stock.'
        )
        if _is_ajax():
            return _json_response(False, message, 400)
        flash(message, 'error')
        return redirect(url_for('index'))

    new_qty = round(available - amount_used, 6)
    conn.execute('UPDATE items SET quantity = ? WHERE id = ?', (new_qty, id))
    conn.execute('''
        INSERT INTO usage_logs (chemical_name, amount_used, unit, purpose, username)
        VALUES (?, ?, ?, ?, ?)
    ''', (item['name'], amount_used, unit, purpose, session['username']))
    conn.commit()
    conn.close()

    message = f'Logged {_format_quantity(amount_used)} {unit} of {item["name"]}.'
    if _is_ajax():
        return _json_response(
            True, message, quantity=new_qty, unit=unit, item_name=item['name']
        )
    flash(message, 'success')
    return redirect(url_for('index'))


init_db()


def _find_available_port(host, preferred, attempts=20):
    for offset in range(attempts):
        port = preferred + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    return preferred


def _find_running_instance(host, preferred, attempts=20):
    for offset in range(attempts):
        port = preferred + offset
        try:
            with socket.create_connection((host, port), timeout=0.4) as sock:
                request = (
                    f'GET /login HTTP/1.0\r\nHost: {host}:{port}\r\n'
                    'Connection: close\r\n\r\n'
                )
                sock.sendall(request.encode('ascii'))
                chunks = []
                received = 0
                while received < 65536:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    received += len(chunk)
            response = b''.join(chunks).decode('latin-1', 'ignore')
            if 'x-chemstore: 1' in response.lower():
                return port
        except OSError:
            continue
    return None


def _get_lan_addresses():
    addresses = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_STREAM):
            ip = info[4][0]
            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                addresses.add(ip)
    except OSError:
        pass

    if not addresses:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(('8.8.8.8', 80))
                addresses.add(sock.getsockname()[0])
        except OSError:
            pass

    return sorted(addresses)


def _print_access_urls(port):
    local_url = f'http://{APP_HOST}:{port}'
    print(f'\nLocal access:  {local_url}')

    if APP_BIND_HOST in ('0.0.0.0', '::'):
        lan_addresses = _get_lan_addresses()
        if lan_addresses:
            print('Mobile access (same Wi-Fi network):')
            for ip in lan_addresses:
                print(f'  http://{ip}:{port}')
        else:
            print('Mobile access: connect this computer to Wi-Fi/Ethernet to get a network address.')
        print('If your phone cannot connect, allow this app through Windows Firewall for private networks.')
    else:
        print(f'LAN/mobile access is disabled (CHEMSTORE_HOST={APP_BIND_HOST}).')
    print()


def _open_browser_when_ready(url, host, port, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.2)
    print(f"Opening {url} in your browser...")
    if not webbrowser.open(url):
        print(f"Could not open a browser automatically. Please open {url} manually.")


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    open_browser = os.environ.get('CHEMSTORE_NO_BROWSER', '0') != '1'

    if open_browser:
        running_port = _find_running_instance(APP_HOST, APP_PORT)
        if running_port is not None:
            webbrowser.open(f'http://{APP_HOST}:{running_port}')
            sys.exit(0)

    port = _find_available_port(APP_BIND_HOST, APP_PORT)
    url = f'http://{APP_HOST}:{port}'
    if open_browser:
        threading.Thread(
            target=_open_browser_when_ready,
            args=(url, APP_HOST, port),
            daemon=True,
        ).start()
    _print_access_urls(port)
    app.run(host=APP_BIND_HOST, port=port, debug=debug)
