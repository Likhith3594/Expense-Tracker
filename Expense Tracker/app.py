from flask import Flask, render_template, request, redirect, flash
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "secret123"

# ------------------ DB INIT ------------------
def init_db():
    conn = sqlite3.connect('expenses.db')
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        amount REAL,
        category TEXT,
        expense_date TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ------------------ HOME ------------------
@app.route('/')
def index():
    conn = sqlite3.connect('expenses.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM expenses ORDER BY expense_date DESC")
    data = cur.fetchall()

    # Total & Avg
    cur.execute("SELECT SUM(amount) FROM expenses")
    total = cur.fetchone()[0] or 0

    cur.execute("SELECT AVG(amount) FROM expenses")
    avg = cur.fetchone()[0] or 0

    # Highest & Lowest
    cur.execute("SELECT * FROM expenses ORDER BY amount DESC LIMIT 1")
    highest = cur.fetchone()

    cur.execute("SELECT * FROM expenses ORDER BY amount ASC LIMIT 1")
    lowest = cur.fetchone()

    # Monthly Summary
    cur.execute("""
    SELECT SUBSTR(expense_date,1,7), SUM(amount)
    FROM expenses
    GROUP BY SUBSTR(expense_date,1,7)
    """)
    monthly = cur.fetchall()

    # Running Total
    cur.execute("""
    SELECT expense_date, amount,
    SUM(amount) OVER (ORDER BY expense_date)
    FROM expenses
    """)
    running = cur.fetchall()

    # Budget Alert
    if total > 5000:
        flash("⚠️ Budget exceeded!", "error")

    # Daily Reminder
    today = date.today().isoformat()
    cur.execute("SELECT * FROM expenses WHERE expense_date=?", (today,))
    if len(cur.fetchall()) == 0:
        flash("📌 No expense added today!", "error")

    conn.close()

    return render_template("index.html", data=data, total=total, avg=avg,
                           highest=highest, lowest=lowest,
                           monthly=monthly, running=running)

# ------------------ ADD ------------------
@app.route('/add', methods=['POST'])
def add():
    try:
        title = request.form['title']
        amount = float(request.form['amount'])
        category = request.form['category']
        date_val = request.form['date']

        conn = sqlite3.connect('expenses.db')
        cur = conn.cursor()

        cur.execute("INSERT INTO expenses(title, amount, category, expense_date) VALUES (?, ?, ?, ?)",
                    (title, amount, category, date_val))
        conn.commit()
        conn.close()

        # High expense alert
        if amount > 2000:
            flash("🚨 High expense detected!", "error")

        flash("✅ Expense added successfully!", "success")

    except:
        flash("❌ Error adding expense!", "error")

    return redirect('/')

# ------------------ DELETE ------------------
@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('expenses.db')
    cur = conn.cursor()

    cur.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("🗑️ Expense deleted!", "success")
    return redirect('/')

# ------------------ EDIT ------------------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = sqlite3.connect('expenses.db')
    cur = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']
        date_val = request.form['date']

        cur.execute("""
        UPDATE expenses
        SET title=?, amount=?, category=?, expense_date=?
        WHERE id=?
        """, (title, amount, category, date_val, id))

        conn.commit()
        conn.close()

        flash("✏️ Expense updated!", "success")
        return redirect('/')

    cur.execute("SELECT * FROM expenses WHERE id=?", (id,))
    data = cur.fetchone()
    conn.close()

    return render_template("edit.html", data=data)

# ------------------ SEARCH ------------------
@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']

    conn = sqlite3.connect('expenses.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM expenses WHERE title LIKE ?", ('%' + keyword + '%',))
    data = cur.fetchall()

    conn.close()
    return render_template("index.html", data=data, total=0, avg=0,
                           highest=None, lowest=None,
                           monthly=[], running=[])

# ------------------ FILTER ------------------
@app.route('/filter', methods=['POST'])
def filter():
    category = request.form['category']

    conn = sqlite3.connect('expenses.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM expenses WHERE category=?", (category,))
    data = cur.fetchall()

    conn.close()
    return render_template("index.html", data=data, total=0, avg=0,
                           highest=None, lowest=None,
                           monthly=[], running=[])
@app.route('/test')
def test():
    flash("🔥 Flash is working!", "success")
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)