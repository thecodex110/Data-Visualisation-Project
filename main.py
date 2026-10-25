import os
import sys
import argparse
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

import db_setup
import preprocessing
import visualizations

DB_NAME = "library.db"

def check_db():
    if not os.path.exists(DB_NAME):
        print("\n [Setup] Initializing SQLite database 'library.db' with synthetic engineering library data...")
        db_setup.init_db()
        db_setup.seed_db()
        print(" [Setup] Database ready!\n")
    db_setup.ensure_shipments()

def get_conn():
    return sqlite3.connect(DB_NAME)

# ==============================================================================
# CORE LMS OPERATIONS (ADD, MINUS/REMOVE, SEARCH, ISSUE, RETURN, OVERDUE)
# ==============================================================================

def view_books():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.book_id, b.title, b.author, d.dept_name, b.total_copies, b.available_copies, b.publisher_state
        FROM books b
        JOIN departments d ON b.dept_id = d.dept_id
        ORDER BY d.dept_name, b.title;
    """)
    rows = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*88)
    print("                              LIBRARY BOOK CATALOG")
    print("="*88)
    print(f"{'ID':<4} | {'Title':<33} | {'Author':<20} | {'Dept':<12} | {'Avail/Total':<11} | {'Pub State'}")
    print("-"*88)
    for r in rows:
        avail_str = f"{r[5]}/{r[4]}"
        print(f"{r[0]:<4} | {r[1][:33]:<33} | {r[2][:20]:<20} | {r[3]:<12} | {avail_str:<11} | {r[6]}")
    print("="*88 + "\n")

def add_book():
    print("\n" + "-"*40)
    print("          ADD NEW BOOK (+)")
    print("-"*40)
    title = input("Enter Title: ").strip()
    author = input("Enter Author: ").strip()
    if not title or not author:
        print(" [!] Title and Author cannot be empty.")
        return
        
    conn = get_conn()
    depts = pd.read_sql_query("SELECT * FROM departments;", conn)
    print("\nSelect Academic Department:")
    for _, d in depts.iterrows():
        print(f"  {d['dept_id']}. {d['dept_name']}")
        
    try:
        dept_id = int(input("\nSelect Department ID: "))
        total_copies = int(input("Enter Total Copies: "))
        if total_copies <= 0:
            print(" [!] Copies must be at least 1.")
            conn.close()
            return
            
        pub_state = input("Enter Publisher State (e.g., Maharashtra, Delhi): ").strip()
        if not pub_state:
            pub_state = "Maharashtra"
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (title, author, dept_id, total_copies, available_copies, publisher_state)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (title, author, dept_id, total_copies, total_copies, pub_state))
        conn.commit()
        print(f"\n [✓] Success: Added '{title}' by {author} ({total_copies} copies).")
    except Exception as e:
        print(f" [!] Error adding book: {e}")
    finally:
        conn.close()

def remove_book():
    """Allows decreasing copies or completely removing a book from library inventory."""
    print("\n" + "-"*40)
    print("       REMOVE / MINUS BOOK (-)")
    print("-"*40)
    try:
        book_id = int(input("Enter Book ID to remove: "))
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, author, total_copies, available_copies 
            FROM books WHERE book_id = ?;
        """, (book_id,))
        row = cursor.fetchone()
        
        if not row:
            print(" [!] Error: Book ID not found in library.")
            conn.close()
            return
            
        title, author, total, avail = row
        active_loans = total - avail
        print(f"\nFound: '{title}' by {author}")
        print(f"Total Copies: {total} | Available on Shelf: {avail} | Currently Loaned: {active_loans}")
        
        print("\nChoose Action:")
        print(" 1. Decrease copy count by a specific quantity")
        print(" 2. Completely delete this book record from system")
        action = input("Select (1/2): ").strip()
        
        if action == '1':
            minus_count = int(input(f"Enter quantity to deduct (1 - {avail}): "))
            if minus_count <= 0 or minus_count > avail:
                print(f" [!] Invalid quantity. You can only reduce up to {avail} unloaned copies.")
            else:
                new_total = total - minus_count
                new_avail = avail - minus_count
                cursor.execute("""
                    UPDATE books SET total_copies = ?, available_copies = ? WHERE book_id = ?;
                """, (new_total, new_avail, book_id))
                conn.commit()
                print(f"\n [✓] Updated: '{title}' copies reduced by {minus_count}. New Total: {new_total}.")
        elif action == '2':
            if active_loans > 0:
                print(f" [!] Cannot delete completely: {active_loans} copies are currently on loan by students.")
                print("     Please return all active loans before deleting.")
            else:
                confirm = input(f"Are you sure you want to permanently delete '{title}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    cursor.execute("DELETE FROM transactions WHERE book_id = ?;", (book_id,))
                    cursor.execute("DELETE FROM books WHERE book_id = ?;", (book_id,))
                    conn.commit()
                    print(f"\n [✓] Successfully deleted '{title}' from catalog.")
                else:
                    print(" Operation cancelled.")
        conn.close()
    except Exception as e:
        print(f" [!] Error removing book: {e}")

def search_books():
    query_str = input("\nEnter search title / author / department keyword: ").strip()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.book_id, b.title, b.author, d.dept_name, b.available_copies, b.total_copies, b.publisher_state
        FROM books b
        JOIN departments d ON b.dept_id = d.dept_id
        WHERE b.title LIKE ? OR b.author LIKE ? OR d.dept_name LIKE ?;
    """, (f"%{query_str}%", f"%{query_str}%", f"%{query_str}%"))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print(" [!] No matching books found.")
        return
        
    print(f"\nFound {len(rows)} matching book(s):")
    print("-" * 80)
    for r in rows:
        print(f" [ID {r[0]}] '{r[1]}' by {r[2]} ({r[3]}) | Shelf: {r[4]}/{r[5]} | State: {r[6]}")
    print("-" * 80)

def view_students():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.student_id, s.name, d.dept_name, s.year, s.home_state
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        ORDER BY s.student_id;
    """)
    rows = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*75)
    print("                             STUDENT DIRECTORY")
    print("="*75)
    print(f"{'ID':<5} | {'Student Name':<25} | {'Department':<16} | {'Year':<7} | {'Home State'}")
    print("-"*75)
    for r in rows:
        print(f"{r[0]:<5} | {r[1]:<25} | {r[2]:<16} | Year {r[3]:<2} | {r[4]}")
    print("="*75 + "\n")

def add_student():
    print("\n" + "-"*40)
    print("          ADD NEW STUDENT")
    print("-"*40)
    name = input("Enter Student Full Name: ").strip()
    if not name:
        print(" [!] Name cannot be empty.")
        return
        
    conn = get_conn()
    depts = pd.read_sql_query("SELECT * FROM departments;", conn)
    print("\nSelect Academic Department:")
    for _, d in depts.iterrows():
        print(f"  {d['dept_id']}. {d['dept_name']}")
        
    try:
        dept_id = int(input("\nSelect Department ID: "))
        year = int(input("Enter Academic Year (1-4): "))
        home_state = input("Enter Home State (e.g. Maharashtra, Karnataka): ").strip()
        if not home_state:
            home_state = "Maharashtra"
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (name, dept_id, year, home_state)
            VALUES (?, ?, ?, ?);
        """, (name, dept_id, year, home_state))
        conn.commit()
        print(f"\n [✓] Successfully registered student '{name}'.")
    except Exception as e:
        print(f" [!] Error adding student: {e}")
    finally:
        conn.close()

def issue_book():
    print("\n" + "-"*40)
    print("          ISSUE A BOOK")
    print("-"*40)
    try:
        student_id = int(input("Enter Student ID: "))
        book_id = int(input("Enter Book ID to issue: "))
        
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM students WHERE student_id = ?;", (student_id,))
        s_row = cursor.fetchone()
        if not s_row:
            print(" [!] Error: Student ID not found.")
            conn.close()
            return
            
        cursor.execute("SELECT title, available_copies FROM books WHERE book_id = ?;", (book_id,))
        b_row = cursor.fetchone()
        if not b_row:
            print(" [!] Error: Book ID not found.")
            conn.close()
            return
            
        if b_row[1] <= 0:
            print(f" [!] Unavailable: '{b_row[0]}' currently has 0 available copies on the shelf.")
            conn.close()
            return
            
        issue_dt = datetime.now()
        due_dt = issue_dt + timedelta(days=14)
        
        issue_str = issue_dt.strftime("%Y-%m-%d")
        due_str = due_dt.strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO transactions (book_id, student_id, issue_date, due_date, return_date, fine_amount)
            VALUES (?, ?, ?, ?, NULL, 0.0);
        """, (book_id, student_id, issue_str, due_str))
        
        cursor.execute("UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?;", (book_id,))
        conn.commit()
        conn.close()
        
        print(f"\n [✓] Issued '{b_row[0]}' to {s_row[0]}.")
        print(f"     Loan Period: 14 Days | Due Date: {due_str}")
    except Exception as e:
        print(f" [!] Error issuing book: {e}")

def return_book():
    print("\n" + "-"*40)
    print("      RETURN BOOK & CALCULATE FINE")
    print("-"*40)
    try:
        txn_id = int(input("Enter Transaction ID to return: "))
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.book_id, b.title, t.due_date, t.return_date, s.name
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN students s ON t.student_id = s.student_id
            WHERE t.txn_id = ?;
        """, (txn_id,))
        row = cursor.fetchone()
        
        if not row:
            print(" [!] Error: Transaction ID not found.")
            conn.close()
            return
            
        if row[3] is not None:
            print(f" [i] Notice: Book was already returned previously on {row[3]}.")
            conn.close()
            return
            
        book_id, title, due_str, _, student_name = row
        return_dt = datetime.now()
        due_dt = datetime.strptime(due_str, "%Y-%m-%d")
        return_str = return_dt.strftime("%Y-%m-%d")
        
        overdue_days = max(0, (return_dt.date() - due_dt.date()).days)
        fine_amount = float(overdue_days * 5.0)  # ₹5 / day overdue fine
        
        cursor.execute("""
            UPDATE transactions
            SET return_date = ?, fine_amount = ?
            WHERE txn_id = ?;
        """, (return_str, fine_amount, txn_id))
        
        cursor.execute("UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?;", (book_id,))
        conn.commit()
        conn.close()
        
        print(f"\n [✓] Successfully processed return for '{title}' (Borrower: {student_name}).")
        if fine_amount > 0:
            print(f" [!] OVERDUE NOTICE: {overdue_days} days late. Fine Due: ₹{fine_amount:.2f} (@ ₹5/day).")
        else:
            print(" [✓] Returned on-time. Fine Due: ₹0.00.")
    except Exception as e:
        print(f" [!] Error returning book: {e}")

def view_overdue_books():
    print("\n" + "="*88)
    print("                           CURRENTLY OVERDUE LOANS")
    print("="*88)
    df = preprocessing.get_cleaned_transactions()
    overdue_df = df[df['status'].str.contains('Overdue')]
    
    if overdue_df.empty:
        print(" No overdue books at present.")
        return
        
    print(f"{'Txn ID':<7} | {'Student Name':<20} | {'Book Title':<28} | {'Due Date':<10} | {'Days Late':<9} | {'Fine (₹)'}")
    print("-"*88)
    for _, r in overdue_df.iterrows():
        print(f"{r['txn_id']:<7} | {r['student_name'][:20]:<20} | {r['book_title'][:28]:<28} | {r['due_date']:<10} | {r['overdue_days']:<9} | ₹{r['effective_fine']:.2f}")
    print("="*88 + "\n")

def student_history():
    try:
        s_id = int(input("\nEnter Student ID: "))
        df = preprocessing.get_cleaned_transactions()
        s_txns = df[df['student_id'] == s_id]
        
        if s_txns.empty:
            print(" [!] No transaction history found for this student.")
            return
            
        print(f"\nBorrowing History: Student {s_id} - {s_txns['student_name'].iloc[0]} ({s_txns['dept_name'].iloc[0]}):")
        print("="*85)
        print(f"{'Txn ID':<7} | {'Book Title':<30} | {'Issue Date':<10} | {'Due Date':<10} | {'Return Date':<12} | {'Fine (₹)'}")
        print("-"*85)
        for _, r in s_txns.iterrows():
            print(f"{r['txn_id']:<7} | {r['book_title'][:30]:<30} | {r['issue_date']:<10} | {r['due_date']:<10} | {r['return_date_display']:<12} | ₹{r['effective_fine']:.2f}")
        print("="*85 + "\n")
    except Exception as e:
        print(f" [!] Error fetching history: {e}")

def export_for_power_bi():
    """Exports database tables into library_export.xlsx for Power BI modeling."""
    print("\n" + "-"*40)
    print("      EXPORTING DATA FOR POWER BI")
    print("-"*40)
    try:
        conn = get_conn()
        excel_path = "library_export.xlsx"
        
        depts = pd.read_sql_query("SELECT * FROM departments;", conn)
        students = pd.read_sql_query("SELECT * FROM students;", conn)
        books = pd.read_sql_query("SELECT * FROM books;", conn)
        transactions = pd.read_sql_query("SELECT * FROM transactions;", conn)
        shipments = pd.read_sql_query("SELECT * FROM shipments;", conn)
        conn.close()
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            depts.to_excel(writer, sheet_name='departments', index=False)
            students.to_excel(writer, sheet_name='students', index=False)
            books.to_excel(writer, sheet_name='books', index=False)
            transactions.to_excel(writer, sheet_name='transactions', index=False)
            shipments.to_excel(writer, sheet_name='shipments', index=False)
            
        print(f" [✓] SUCCESS: Dataset exported to '{excel_path}' with 5 tables:")
        print("     - departments, students, books, transactions, shipments")
        print(" [i] Open POWERBI_GUIDE.md for step-by-step instructions on building the Power BI dashboard.")
    except Exception as e:
        print(f" [!] Error exporting to Excel: {e}")

# ==============================================================================
# POWER BI STYLE KPI CARDS (Cards, KPI vs target, Gauge, Slicers, Drill-down) IN THE TERMINAL
# ==============================================================================

def _text_gauge(pct, width=30):
    filled = int(round(pct / 100 * width))
    return "[" + "#" * filled + "-" * (width - filled) + f"] {pct:.1f}%"

def kpi_dashboard():
    conn = get_conn()
    depts = pd.read_sql_query("SELECT dept_name FROM departments ORDER BY dept_id;", conn)['dept_name'].tolist()
    conn.close()
    
    # Slicers
    print("\nSlicer 1 - Department:  0. All")
    for i, d in enumerate(depts, 1):
        print(f"                        {i}. {d}")
    d_choice = input("Select department (0 = All): ").strip()
    dept = depts[int(d_choice) - 1] if d_choice.isdigit() and 1 <= int(d_choice) <= len(depts) else None
    y_choice = input("Slicer 2 - Student Year (1-4, 0 = All): ").strip()
    year = int(y_choice) if y_choice in ('1', '2', '3', '4') else None
    
    k = preprocessing.get_library_kpis(dept, year)
    change = k['issues_this_month'] - k['issues_last_month']
    arrow = "▲" if change > 0 else ("▼" if change < 0 else "■")
    
    print("\n" + "=" * 70)
    print(f"  LIBRARY KPI DASHBOARD | Dept: {dept or 'All'} | Year: {year or 'All'}")
    print("=" * 70)
    print("  CARDS")
    print(f"    Titles: {k['titles']:<6} Copies: {k['total_copies']:<6} On Loan: {k['on_loan']:<6} Total Loans: {k['total_loans']}")
    print(f"    Active Loans: {k['active_loans']:<6} Active Overdue: {k['active_overdue']:<6} Total Fines: Rs {k['total_fines']:,.2f}")
    print("  KPI (this month vs last month target)")
    print(f"    Issues this month: {k['issues_this_month']}  vs last month: {k['issues_last_month']}  {arrow} {change:+d}")
    print(f"    Overdue rate: {k['overdue_rate_pct']:.1f}%  (target <= 20%: {'OK' if k['overdue_rate_pct'] <= 20 else 'ABOVE TARGET'})")
    print("  GAUGE - Library utilisation (copies on loan / total copies)")
    print(f"    {_text_gauge(k['utilization_pct'])}")
    print("=" * 70)
    
    # Drill-down: department -> books
    df = preprocessing.get_cleaned_transactions()
    if year:
        df = df[df['student_year'] == year]
    if dept is None:
        print("\n  DRILL-DOWN LEVEL 1: Loans by Department")
        for name, n in df.groupby('dept_name').size().sort_values(ascending=False).items():
            print(f"    {name:<18} {n:>4}  {'█' * (n // 3)}")
        pick = input("\n  Type a department name to drill down (Enter to skip): ").strip()
        dept = next((d for d in depts if d.lower() == pick.lower()), None)
    if dept:
        print(f"\n  DRILL-DOWN LEVEL 2: Top Books in {dept}")
        top = df[df['dept_name'] == dept].groupby('book_title').size().sort_values(ascending=False).head(8)
        for title, n in top.items():
            print(f"    {title[:45]:<45} {n:>3}  {'█' * n}")
    print()

# ==============================================================================
# SELF-STUDY CASE STUDY: SUPPLY CHAIN & LOGISTICS (Route mapping, delivery KPIs, region filter)
# ==============================================================================

def supply_chain_case_study():
    regions = ['North', 'West', 'South', 'East']
    print("\nFilter by Region:  0. All Regions")
    for i, r in enumerate(regions, 1):
        print(f"                   {i}. {r}")
    choice = input("Select region (0-4): ").strip()
    region = regions[int(choice) - 1] if choice in ('1', '2', '3', '4') else None
    
    ship = preprocessing.get_cleaned_shipments(region)
    if ship.empty:
        print(" [!] No shipments found for this region.")
        return
    delivered = ship[ship['status'].str.startswith('Delivered')]
    on_time = (delivered['status'] == 'Delivered On-Time').mean() * 100 if len(delivered) else 0.0
    
    print("\n" + "=" * 78)
    print(f"  SUPPLY CHAIN & LOGISTICS - BOOK PROCUREMENT | Region: {region or 'All'}")
    print("=" * 78)
    print(f"  Shipments: {len(ship)} | Units: {ship['quantity'].sum()} | Freight: Rs {ship['freight_cost'].sum():,.0f}")
    print(f"  On-time delivery: {_text_gauge(on_time)} (target 90%)")
    print(f"  Avg transit days (delivered): {delivered['transit_days'].mean():.1f}")
    
    print("\n  DELIVERY STATUS KPIs")
    for status, n in ship['status'].value_counts().items():
        print(f"    {status:<20} {n:>4}  ({n / len(ship) * 100:.1f}%)")
    
    print("\n  ROUTES (publisher hub -> Pune campus)")
    print(f"    {'Origin':<12} {'Region':<7} {'Km':>6} {'Shipments':>10} {'Avg Days':>9} {'Late/Delayed':>13}")
    routes = ship.groupby(['origin_city', 'region']).agg(
        km=('distance_km', 'first'), n=('shipment_id', 'count'), days=('transit_days', 'mean'),
        late=('status', lambda s: s.isin(['Delivered Late', 'Delayed In Transit']).sum())
    ).reset_index().sort_values('n', ascending=False)
    for _, r in routes.iterrows():
        print(f"    {r['origin_city']:<12} {r['region']:<7} {r['km']:>6.0f} {r['n']:>10} {r['days']:>9.1f} {r['late']:>13}")
    print("=" * 78)
    
    visualizations.plot_supply_chain_dashboard(region)

# ==============================================================================
# DATA VISUALIZATION MENU (SYLLABUS UNIT-WISE)
# ==============================================================================

def print_chart_list():
    current_unit = None
    for i, (unit, title, _) in enumerate(visualizations.CHART_MENU, 1):
        if unit != current_unit:
            print(f"  --- {unit} ---")
            current_unit = unit
        print(f"  {i:>2}. {title}")

def run_chart(number):
    if 1 <= number <= len(visualizations.CHART_MENU):
        visualizations.CHART_MENU[number - 1][2]()
        return True
    print(f" [!] Invalid chart number. Use 1 to {len(visualizations.CHART_MENU)}.")
    return False

def visualization_menu():
    while True:
        print("\n" + "=" * 72)
        print("        DATA VISUALIZATION MENU (arranged by syllabus unit)")
        print("=" * 72)
        print_chart_list()
        print("   A. Generate ALL charts (saved to charts/, no windows)")
        print("   0. Back to Main Menu")
        print("=" * 72)
        
        choice = input(f"Select chart (1-{len(visualizations.CHART_MENU)}, A, 0): ").strip()
        if choice == '0':
            break
        elif choice.lower() == 'a':
            visualizations.generate_all_visualizations()
        elif choice.isdigit():
            run_chart(int(choice))
        else:
            print(" [!] Invalid option.")

# ==============================================================================
# MAIN APPLICATION MENU
# ==============================================================================

def main_menu():
    check_db()
    
    while True:
        print("\n" + "="*66)
        print("   ENGINEERING COLLEGE LIBRARY MANAGEMENT SYSTEM (LMS)")
        print("           DATA VISUALIZATION & ANALYTICS PLATFORM")
        print("="*66)
        print("  1. View Library Catalog")
        print("  2. Add New Book")
        print("  3. Remove / Minus Book (Reduce copies or delete)")
        print("  4. Search Books by Title / Author / Department")
        print("  5. View Student Directory")
        print("  6. Add New Student")
        print("  7. Issue a Book (Auto 14-day due date)")
        print("  8. Return a Book (Auto Rs 5/day fine calculation)")
        print("  9. View Overdue Loans")
        print(" 10. Student Borrowing History")
        print(" 11. Data Cleaning & Aggregation Report")
        print(" 12. Data Visualization Menu (Unit 1 - Unit 5)")
        print(" 13. Generate All Charts (One-Click)")
        print(" 14. KPI Dashboard (Cards, KPI, Gauge, Slicers, Drill-down)")
        print(" 15. Supply Chain & Logistics Case Study (Region filter)")
        print(" 16. Export Dataset for Power BI (library_export.xlsx)")
        print("  0. Exit")
        print("="*66)
        
        choice = input("Enter choice (0-16): ").strip()
        
        actions = {
            '1': view_books, '2': add_book, '3': remove_book, '4': search_books,
            '5': view_students, '6': add_student, '7': issue_book, '8': return_book,
            '9': view_overdue_books, '10': student_history,
            '11': preprocessing.print_cleaning_report, '12': visualization_menu,
            '13': visualizations.generate_all_visualizations, '14': kpi_dashboard,
            '15': supply_chain_case_study, '16': export_for_power_bi,
        }
        if choice == '0':
            print("\n [✓] Thank you for using Engineering College Library Management System. Goodbye!\n")
            sys.exit(0)
        elif choice in actions:
            actions[choice]()
        else:
            print(" [!] Invalid selection. Please enter a valid menu number (0-16).")

def parse_args():
    parser = argparse.ArgumentParser(description="Engineering College Library LMS - Data Visualization project (terminal).")
    parser.add_argument('--all', action='store_true', help="generate every chart into charts/ and exit")
    parser.add_argument('--list', action='store_true', help="list all chart numbers and exit")
    parser.add_argument('--chart', type=int, metavar='N', help="open/save chart number N and exit")
    parser.add_argument('--report', action='store_true', help="print the data cleaning & aggregation report and exit")
    parser.add_argument('--export', action='store_true', help="export library_export.xlsx for Power BI and exit")
    parser.add_argument('--reset-db', action='store_true', help="delete and re-create library.db with fresh sample data")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.reset_db and os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    check_db()
    if args.list:
        print_chart_list()
    elif args.chart:
        run_chart(args.chart)
    elif args.all:
        visualizations.generate_all_visualizations()
    elif args.report:
        preprocessing.print_cleaning_report()
    elif args.export:
        export_for_power_bi()
    elif not args.reset_db:
        main_menu()
