import json
import os, csv
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from db import query

app = Flask(__name__)
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- Helpers ----------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required():
    if not session.get("user"):
        flash("Please login first", "warning")
        return False
    return True

def admin_required():
    u = session.get("user")
    return u and u.get("role") == "admin"

# ---------- UI Tasks Support (Navbar scroll, alerts, validation JS) ----------
@app.route("/")
def home():
    return redirect(url_for("dashboard")) if session.get("user") else redirect(url_for("login"))

# ---------- Auth ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        role = request.form.get("role","user")

        if not name or not email or len(password) < 6:
            flash("Invalid data (password min 6).", "danger")
            return redirect(url_for("register"))

        existing = query("SELECT id FROM users WHERE email=%s", (email,), one=True)
        if existing:
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        pwd_hash = generate_password_hash(password)
        query("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,%s)",
              (name, email, pwd_hash, role), commit=True)
        flash("Registered successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("auth/register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user = query("SELECT id,name,email,password_hash,role FROM users WHERE email=%s", (email,), one=True)

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email/password.", "danger")
            return redirect(url_for("login"))

        session["user"] = {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
        session.setdefault("cart", {})
        flash("Login success!", "success")
        return redirect(url_for("dashboard"))

    return render_template("auth/login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

# ---------- Dashboard (counts + highest salary style query analog using price/stock) ----------
@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    total_users = query("SELECT COUNT(*) AS c FROM users", one=True)["c"]
    total_students = query("SELECT COUNT(*) AS c FROM students", one=True)["c"]
    total_products = query("SELECT COUNT(*) AS c FROM products", one=True)["c"]
    total_orders = query("SELECT COUNT(*) AS c FROM orders", one=True)["c"]

    highest_price = query("SELECT * FROM products ORDER BY price DESC LIMIT 1", one=True)

    # monthly registrations (students)
    monthly = query("""
        SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS ym, COUNT(*) AS c
        FROM students
        GROUP BY ym
        ORDER BY ym DESC
        LIMIT 12
    """)

    return render_template("dashboard.html",
                           total_users=total_users,
                           total_students=total_students,
                           total_products=total_products,
                           total_orders=total_orders,
                           highest_price=highest_price,
                           monthly=monthly)

# ---------- Students CRUD + Search + Pagination + Sorting ----------
@app.route("/students")
def students_list():
    if not login_required():
        return redirect(url_for("login"))

    q = request.args.get("q","").strip()
    dept = request.args.get("dept","").strip()
    sort = request.args.get("sort","created_at_desc")
    page = int(request.args.get("page", 1))
    per_page = 5
    offset = (page - 1) * per_page

    where = "WHERE 1=1"
    params = []

    if q:
        where += " AND (name LIKE %s OR email LIKE %s)"
        like = f"%{q}%"
        params += [like, like]

    if dept:
        where += " AND dept=%s"
        params.append(dept)

    order_by = "ORDER BY created_at DESC"
    if sort == "name_asc":
        order_by = "ORDER BY name ASC"
    elif sort == "name_desc":
        order_by = "ORDER BY name DESC"
    elif sort == "created_at_asc":
        order_by = "ORDER BY created_at ASC"

    total = query(f"SELECT COUNT(*) AS c FROM students {where}", tuple(params), one=True)["c"]
    rows = query(f"SELECT * FROM students {where} {order_by} LIMIT %s OFFSET %s", tuple(params + [per_page, offset]))

    total_pages = max(1, (total + per_page - 1) // per_page)

    depts = query("SELECT DISTINCT dept FROM students WHERE dept IS NOT NULL AND dept<>'' ORDER BY dept")

    return render_template("students/list.html",
                           rows=rows, q=q, dept=dept, sort=sort,
                           page=page, total_pages=total_pages, total=total, depts=depts)

@app.route("/students/new", methods=["GET","POST"])
def students_new():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip()
        phone = request.form.get("phone","").strip()
        dept = request.form.get("dept","").strip()

        if not name or not email:
            flash("Name & Email required.", "danger")
            return redirect(url_for("students_new"))

        query("INSERT INTO students(name,email,phone,dept) VALUES(%s,%s,%s,%s)",
              (name, email, phone, dept), commit=True)
        flash("Student added.", "success")
        return redirect(url_for("students_list"))

    return render_template("students/form.html", mode="create", item=None)

@app.route("/students/<int:sid>/edit", methods=["GET","POST"])
def students_edit(sid):
    if not login_required():
        return redirect(url_for("login"))

    item = query("SELECT * FROM students WHERE id=%s", (sid,), one=True)
    if not item:
        flash("Student not found.", "warning")
        return redirect(url_for("students_list"))

    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip()
        phone = request.form.get("phone","").strip()
        dept = request.form.get("dept","").strip()

        if not name or not email:
            flash("Name & Email required.", "danger")
            return redirect(url_for("students_edit", sid=sid))

        query("UPDATE students SET name=%s,email=%s,phone=%s,dept=%s WHERE id=%s",
              (name, email, phone, dept, sid), commit=True)
        flash("Student updated.", "success")
        return redirect(url_for("students_list"))

    return render_template("students/form.html", mode="edit", item=item)

@app.route("/students/<int:sid>/delete", methods=["POST"])
def students_delete(sid):
    if not login_required():
        return redirect(url_for("login"))

    query("DELETE FROM students WHERE id=%s", (sid,), commit=True)
    flash("Student deleted.", "info")
    return redirect(url_for("students_list"))

@app.route("/students/bulk-delete", methods=["POST"])
def students_bulk_delete():
    if not login_required():
        return redirect(url_for("login"))

    ids = request.form.getlist("ids")
    if not ids:
        flash("Select at least one.", "warning")
        return redirect(url_for("students_list"))

    placeholders = ",".join(["%s"] * len(ids))
    query(f"DELETE FROM students WHERE id IN ({placeholders})", tuple(ids), commit=True)
    flash(f"Deleted {len(ids)} students.", "info")
    return redirect(url_for("students_list"))

@app.route("/students/export.csv")
def students_export_csv():
    if not login_required():
        return redirect(url_for("login"))

    rows = query("SELECT id,name,email,phone,dept,created_at FROM students ORDER BY created_at DESC")
    path = os.path.join("static", "students_export.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","name","email","phone","dept","created_at"])
        for r in rows:
            w.writerow([r["id"], r["name"], r["email"], r["phone"], r["dept"], r["created_at"]])
    return send_file(path, as_attachment=True)

# ---------- Feedback + Contact (store in DB) ----------
@app.route("/feedback", methods=["POST"])
def feedback():
    if not login_required():
        return redirect(url_for("login"))

    msg = request.form.get("message","").strip()
    if not msg:
        flash("Feedback empty.", "warning")
        return redirect(url_for("dashboard"))
    uid = session["user"]["id"]
    query("INSERT INTO feedback(user_id,message) VALUES(%s,%s)", (uid, msg), commit=True)
    flash("Thanks for feedback!", "success")
    return redirect(url_for("dashboard"))

@app.route("/contact", methods=["POST"])
def contact():
    # Contact form store as feedback for simplicity (can create separate table too)
    name = request.form.get("name","").strip()
    email = request.form.get("email","").strip()
    msg = request.form.get("message","").strip()
    if not name or not email or not msg:
        flash("Fill all contact fields.", "danger")
        return redirect(url_for("dashboard"))
    query("INSERT INTO feedback(user_id,message) VALUES(%s,%s)", (None, f"CONTACT: {name} ({email}) -> {msg}"), commit=True)
    flash("Contact saved!", "success")
    return redirect(url_for("dashboard"))

# ---------- Products CRUD + Search Filter + Image Upload ----------
@app.route("/products")
def products_list():
    if not login_required():
        return redirect(url_for("login"))

    q = request.args.get("q","").strip()
    cat = request.args.get("cat","").strip()

    where = "WHERE 1=1"
    params = []
    if q:
        where += " AND title LIKE %s"
        params.append(f"%{q}%")
    if cat:
        where += " AND category=%s"
        params.append(cat)

    rows = query(f"SELECT * FROM products {where} ORDER BY created_at DESC", tuple(params))
    cats = query("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category<>'' ORDER BY category")
    return render_template("products/list.html", rows=rows, q=q, cat=cat, cats=cats)

@app.route("/products/new", methods=["GET","POST"])
def products_new():
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        flash("Admin only.", "danger")
        return redirect(url_for("products_list"))

    if request.method == "POST":
        title = request.form.get("title","").strip()
        category = request.form.get("category","").strip()
        price = request.form.get("price","0").strip()
        stock = request.form.get("stock","0").strip()

        image = request.files.get("image")
        image_path = None
        if image and image.filename:
            if not allowed_file(image.filename):
                flash("Invalid image type.", "danger")
                return redirect(url_for("products_new"))
            fn = secure_filename(image.filename)
            save_path = os.path.join(UPLOAD_FOLDER, fn)
            image.save(save_path)
            image_path = f"uploads/{fn}"

        query("INSERT INTO products(title,category,price,stock,image_path) VALUES(%s,%s,%s,%s,%s)",
              (title, category, price, stock, image_path), commit=True)
        flash("Product added.", "success")
        return redirect(url_for("products_list"))

    return render_template("products/form.html", mode="create", item=None)

@app.route("/products/<int:pid>/edit", methods=["GET","POST"])
def products_edit(pid):
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        flash("Admin only.", "danger")
        return redirect(url_for("products_list"))

    item = query("SELECT * FROM products WHERE id=%s", (pid,), one=True)
    if not item:
        flash("Product not found.", "warning")
        return redirect(url_for("products_list"))

    if request.method == "POST":
        title = request.form.get("title","").strip()
        category = request.form.get("category","").strip()
        price = request.form.get("price","0").strip()
        stock = request.form.get("stock","0").strip()

        image = request.files.get("image")
        image_path = item["image_path"]
        if image and image.filename:
            if not allowed_file(image.filename):
                flash("Invalid image type.", "danger")
                return redirect(url_for("products_edit", pid=pid))
            fn = secure_filename(image.filename)
            save_path = os.path.join(UPLOAD_FOLDER, fn)
            image.save(save_path)
            image_path = f"uploads/{fn}"

        query("UPDATE products SET title=%s,category=%s,price=%s,stock=%s,image_path=%s WHERE id=%s",
              (title, category, price, stock, image_path, pid), commit=True)
        flash("Product updated.", "success")
        return redirect(url_for("products_list"))

    return render_template("products/form.html", mode="edit", item=item)

@app.route("/products/<int:pid>/delete", methods=["POST"])
def products_delete(pid):
    if not login_required():
        return redirect(url_for("login"))
    if not admin_required():
        flash("Admin only.", "danger")
        return redirect(url_for("products_list"))

    query("DELETE FROM products WHERE id=%s", (pid,), commit=True)
    flash("Product deleted.", "info")
    return redirect(url_for("products_list"))

# ---------- Mini e-commerce: Cart (session) + Orders ----------
@app.route("/cart/add/<int:pid>", methods=["POST"])
def cart_add(pid):
    if not login_required():
        return redirect(url_for("login"))

    p = query("SELECT id,title,price,stock FROM products WHERE id=%s", (pid,), one=True)
    if not p:
        flash("Product not found.", "warning")
        return redirect(url_for("products_list"))

    cart = session.get("cart", {})
    cart[str(pid)] = cart.get(str(pid), 0) + 1
    session["cart"] = cart
    flash("Added to cart.", "success")
    return redirect(url_for("products_list"))

@app.route("/cart")
def cart_view():
    if not login_required():
        return redirect(url_for("login"))

    cart = session.get("cart", {})
    items = []
    total = 0.0
    for pid, qty in cart.items():
        p = query("SELECT * FROM products WHERE id=%s", (pid,), one=True)
        if not p:
            continue
        line = float(p["price"]) * int(qty)
        total += line
        items.append({"p": p, "qty": int(qty), "line": line})

    return render_template("products/list.html", rows=query("SELECT * FROM products ORDER BY created_at DESC"),
                           q="", cat="", cats=query("SELECT DISTINCT category FROM products ORDER BY category"),
                           cart_items=items, cart_total=total)

@app.route("/order/checkout", methods=["POST"])
def checkout():
    if not login_required():
        return redirect(url_for("login"))

    cart = session.get("cart", {})
    if not cart:
        flash("Cart empty.", "warning")
        return redirect(url_for("products_list"))

    items = []
    total = 0.0
    for pid, qty in cart.items():
        p = query("SELECT id,price,stock FROM products WHERE id=%s", (pid,), one=True)
        if not p:
            continue
        qty = int(qty)
        total += float(p["price"]) * qty
        items.append((int(pid), qty, float(p["price"])))

    order_id = query("INSERT INTO orders(user_id,total) VALUES(%s,%s)",
                     (session["user"]["id"], total), commit=True)

    for pid, qty, price in items:
        query("INSERT INTO order_items(order_id,product_id,qty,price) VALUES(%s,%s,%s,%s)",
              (order_id, pid, qty, price), commit=True)

    session["cart"] = {}
    flash("Order placed!", "success")
    return redirect(url_for("orders"))

@app.route("/orders")
def orders():
    if not login_required():
        return redirect(url_for("login"))

    uid = session["user"]["id"]
    rows = query("SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC", (uid,))
    return render_template("dashboard.html",
                           total_users=query("SELECT COUNT(*) AS c FROM users", one=True)["c"],
                           total_students=query("SELECT COUNT(*) AS c FROM students", one=True)["c"],
                           total_products=query("SELECT COUNT(*) AS c FROM products", one=True)["c"],
                           total_orders=query("SELECT COUNT(*) AS c FROM orders", one=True)["c"],
                           highest_price=query("SELECT * FROM products ORDER BY price DESC LIMIT 1", one=True),
                           monthly=query("""
                               SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS ym, COUNT(*) AS c
                               FROM students GROUP BY ym ORDER BY ym DESC LIMIT 12
                           """),
                           orders=rows)

if __name__ == "__main__":
    app.run(debug=True)

    