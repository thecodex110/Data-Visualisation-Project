import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

DB_NAME = "library.db"

def get_connection(db_path=DB_NAME):
    return sqlite3.connect(db_path)

def load_raw_data(db_path=DB_NAME):
    """Loads raw dataframes from sqlite database."""
    conn = get_connection(db_path)
    
    depts_df = pd.read_sql_query("SELECT * FROM departments;", conn)
    students_df = pd.read_sql_query("SELECT * FROM students;", conn)
    books_df = pd.read_sql_query("SELECT * FROM books;", conn)
    txns_df = pd.read_sql_query("SELECT * FROM transactions;", conn)
    
    conn.close()
    return depts_df, students_df, books_df, txns_df

def get_cleaned_transactions(db_path=DB_NAME):
    """
    Cleans raw transaction data, calculates durations, handles missing return dates,
    and enriches with student and book details.
    """
    conn = get_connection(db_path)
    
    query = """
    SELECT 
        t.txn_id,
        t.book_id,
        b.title AS book_title,
        b.author AS book_author,
        b.total_copies,
        b.available_copies,
        b.publisher_state,
        t.student_id,
        s.name AS student_name,
        s.year AS student_year,
        s.home_state AS student_home_state,
        d.dept_id,
        d.dept_name,
        t.issue_date,
        t.due_date,
        t.return_date,
        t.fine_amount
    FROM transactions t
    JOIN books b ON t.book_id = b.book_id
    JOIN students s ON t.student_id = s.student_id
    JOIN departments d ON b.dept_id = d.dept_id;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    today = pd.Timestamp(datetime.now().date())
    
    # Convert dates
    df['issue_date_dt'] = pd.to_datetime(df['issue_date'])
    df['due_date_dt'] = pd.to_datetime(df['due_date'])
    df['return_date_dt'] = pd.to_datetime(df['return_date'])
    
    # Issue Month string (YYYY-MM)
    df['issue_month'] = df['issue_date_dt'].dt.to_period('M').astype(str)
    
    # Calculate days kept and overdue days
    is_returned = df['return_date_dt'].notnull()
    
    # Days kept
    df['days_kept'] = np.where(
        is_returned,
        (df['return_date_dt'] - df['issue_date_dt']).dt.days,
        (today - df['issue_date_dt']).dt.days
    )
    df['days_kept'] = df['days_kept'].clip(lower=1) # at least 1 day
    
    # Overdue days
    df['overdue_days'] = np.where(
        is_returned,
        (df['return_date_dt'] - df['due_date_dt']).dt.days,
        (today - df['due_date_dt']).dt.days
    )
    df['overdue_days'] = df['overdue_days'].clip(lower=0)
    
    # Recalculate fine amount accurately
    df['calculated_fine'] = df['overdue_days'] * 5.0
    # Use max of recorded fine or calculated fine
    df['effective_fine'] = np.maximum(df['fine_amount'], df['calculated_fine'])
    
    # Status categorisation
    conditions = [
        (~is_returned) & (df['overdue_days'] > 0),
        (~is_returned) & (df['overdue_days'] == 0),
        (is_returned) & (df['overdue_days'] > 0),
        (is_returned) & (df['overdue_days'] == 0)
    ]
    choices = ['Active Overdue', 'Active On-Time', 'Returned Overdue', 'Returned On-Time']
    df['status'] = np.select(conditions, choices, default='Unknown')
    
    # Simplified Status for high-level charts (Issued, Returned, Overdue)
    df['simple_status'] = np.where(
        df['status'].str.contains('Overdue'), 'Overdue',
        np.where(df['status'].str.contains('Returned'), 'Returned', 'Active Issued')
    )
    
    # Display friendly return date string
    df['return_date_display'] = df['return_date'].fillna('Active Issue')
    
    return df

def get_department_aggregates(db_path=DB_NAME):
    """Aggregates book count, total copies, active issues, and fines by Department."""
    txns = get_cleaned_transactions(db_path)
    depts, students, books, _ = load_raw_data(db_path)
    
    # Books per department
    books_per_dept = books.groupby('dept_id').agg(
        total_unique_titles=('book_id', 'count'),
        total_copies=('total_copies', 'sum'),
        available_copies=('available_copies', 'sum')
    ).reset_index()
    
    books_per_dept = pd.merge(depts, books_per_dept, on='dept_id', how='left').fillna(0)
    
    # Transaction counts per department
    txn_counts = txns.groupby(['dept_name', 'simple_status']).size().unstack(fill_value=0).reset_index()
    for col in ['Active Issued', 'Returned', 'Overdue']:
        if col not in txn_counts.columns:
            txn_counts[col] = 0
            
    txn_counts['total_transactions'] = txn_counts['Active Issued'] + txn_counts['Returned'] + txn_counts['Overdue']
    
    summary = pd.merge(books_per_dept, txn_counts, left_on='dept_name', right_on='dept_name', how='left').fillna(0)
    return summary

def get_author_aggregates(db_path=DB_NAME):
    """Aggregates book count, total copies, and borrow volume by Author."""
    _, _, books, _ = load_raw_data(db_path)
    txns = get_cleaned_transactions(db_path)
    
    author_books = books.groupby('author').agg(
        book_titles=('book_id', 'count'),
        total_copies=('total_copies', 'sum')
    ).reset_index()
    
    author_txns = txns.groupby('book_author').agg(
        total_borrowed=('txn_id', 'count')
    ).reset_index().rename(columns={'book_author': 'author'})
    
    author_summary = pd.merge(author_books, author_txns, on='author', how='left').fillna(0)
    author_summary['total_borrowed'] = author_summary['total_borrowed'].astype(int)
    return author_summary.sort_values('total_borrowed', ascending=False)

def get_monthly_matrix(db_path=DB_NAME):
    """Pivots transactions into Department x Month issue counts."""
    txns = get_cleaned_transactions(db_path)
    pivot = txns.pivot_table(
        index='dept_name',
        columns='issue_month',
        values='txn_id',
        aggfunc='count',
        fill_value=0
    )
    # Sort months chronologically
    sorted_cols = sorted(pivot.columns)
    return pivot[sorted_cols]

def get_monthly_timeseries(db_path=DB_NAME):
    """Aggregates monthly issue count, return count, and total fines for time series analysis."""
    txns = get_cleaned_transactions(db_path)
    
    monthly = txns.groupby('issue_month').agg(
        issued_count=('txn_id', 'count'),
        returned_count=('return_date_dt', lambda x: x.notnull().sum()),
        overdue_count=('overdue_days', lambda x: (x > 0).sum()),
        total_fines=('effective_fine', 'sum')
    ).reset_index()
    
    monthly['issue_month_dt'] = pd.to_datetime(monthly['issue_month'] + '-01')
    monthly = monthly.sort_values('issue_month_dt').reset_index(drop=True)
    
    # Rolling 3-month average
    monthly['rolling_3m_issues'] = monthly['issued_count'].rolling(window=3, min_periods=1).mean()
    
    return monthly

def get_student_feature_matrix(db_path=DB_NAME):
    """
    Creates a student-level feature matrix showing count of books borrowed per department,
    used for PCA dimension reduction clustering.
    """
    txns = get_cleaned_transactions(db_path)
    students_df = load_raw_data(db_path)[1]
    
    pivot = txns.pivot_table(
        index='student_id',
        columns='dept_name',
        values='txn_id',
        aggfunc='count',
        fill_value=0
    )
    
    # Merge back student metadata
    student_matrix = pd.merge(students_df[['student_id', 'name', 'dept_id', 'home_state']], pivot, on='student_id', how='left').fillna(0)
    depts_map = dict(load_raw_data(db_path)[0][['dept_id', 'dept_name']].values)
    student_matrix['primary_dept'] = student_matrix['dept_id'].map(depts_map)
    
    return student_matrix

def get_state_geospatial_summary(db_path=DB_NAME):
    """Aggregates student count and borrowing volume by Indian home state."""
    txns = get_cleaned_transactions(db_path)
    students_df = load_raw_data(db_path)[1]
    
    student_counts = students_df.groupby('home_state').agg(
        student_count=('student_id', 'count')
    ).reset_index()
    
    txn_counts = txns.groupby('student_home_state').agg(
        total_issues=('txn_id', 'count'),
        total_fines=('effective_fine', 'sum')
    ).reset_index().rename(columns={'student_home_state': 'home_state'})
    
    geo_summary = pd.merge(student_counts, txn_counts, on='home_state', how='left').fillna(0)
    return geo_summary

def get_student_summary(db_path=DB_NAME):
    """One row per student: loan count, average days kept, overdue loans and total fines."""
    txns = get_cleaned_transactions(db_path)
    depts, students, _, _ = load_raw_data(db_path)
    
    agg = txns.groupby('student_id').agg(
        total_loans=('txn_id', 'count'),
        avg_days_kept=('days_kept', 'mean'),
        overdue_loans=('overdue_days', lambda x: (x > 0).sum()),
        total_fines=('effective_fine', 'sum')
    ).reset_index()
    
    summary = pd.merge(students, agg, on='student_id', how='left').fillna(0)
    summary['primary_dept'] = summary['dept_id'].map(dict(depts[['dept_id', 'dept_name']].values))
    return summary

def print_cleaning_report(db_path=DB_NAME):
    """Terminal report of the cleaning + aggregation pipeline (raw -> clean -> aggregated)."""
    depts, students, books, txns = load_raw_data(db_path)
    print("\n" + "=" * 70)
    print("          DATA CLEANING & AGGREGATION REPORT")
    print("=" * 70)
    
    print("\n[1] RAW TABLES (rows x columns)")
    for name, t in [('departments', depts), ('students', students), ('books', books), ('transactions', txns)]:
        print(f"    {name:<13}: {t.shape[0]:>4} x {t.shape[1]}")
    
    print("\n[2] MISSING VALUES IN RAW transactions")
    for col, n in txns.isnull().sum().items():
        if n:
            print(f"    {col:<13}: {n} nulls  -> meaning: book not returned yet (active loan)")
    print(f"    duplicate rows: {txns.duplicated().sum()}")
    
    clean = get_cleaned_transactions(db_path)
    print("\n[3] CLEANING STEPS APPLIED")
    print("    - issue/due/return dates converted from text to datetime")
    print("    - null return_date kept as active loan (display: 'Active Issue')")
    print("    - days_kept    = return (or today) - issue, clipped at minimum 1")
    print("    - overdue_days = return (or today) - due,   clipped at minimum 0")
    print("    - effective_fine = max(recorded fine, overdue_days x Rs 5)")
    print("    - status / simple_status labels derived from the two rules above")
    print(f"    cleaned shape: {clean.shape[0]} x {clean.shape[1]} (joined with books, students, departments)")
    
    print("\n[4] AGGREGATION: loans by department x status")
    print(clean.pivot_table(index='dept_name', columns='simple_status', values='txn_id',
                            aggfunc='count', fill_value=0).to_string())
    
    print("\n[5] AGGREGATION: summary statistics of days_kept and fines")
    print(clean[['days_kept', 'overdue_days', 'effective_fine']].describe().round(2).to_string())
    print("=" * 70 + "\n")

def get_library_kpis(dept_name=None, year=None, db_path=DB_NAME):
    """Power BI style headline measures, optionally sliced by department and student year."""
    txns = get_cleaned_transactions(db_path)
    depts, _, books, _ = load_raw_data(db_path)
    books = pd.merge(books, depts, on='dept_id')
    if dept_name:
        txns = txns[txns['dept_name'] == dept_name]
        books = books[books['dept_name'] == dept_name]
    if year:
        txns = txns[txns['student_year'] == year]
    
    this_month = pd.Timestamp(datetime.now().date()).to_period('M')
    month_counts = txns['issue_date_dt'].dt.to_period('M').value_counts()
    total_copies = int(books['total_copies'].sum())
    on_loan = total_copies - int(books['available_copies'].sum())
    active = txns[txns['return_date_dt'].isnull()]
    
    return {
        'titles': int(len(books)),
        'total_copies': total_copies,
        'on_loan': on_loan,
        'utilization_pct': (on_loan / total_copies * 100) if total_copies else 0.0,
        'total_loans': int(len(txns)),
        'active_loans': int(len(active)),
        'active_overdue': int((active['overdue_days'] > 0).sum()),
        'overdue_rate_pct': float((txns['overdue_days'] > 0).mean() * 100) if len(txns) else 0.0,
        'total_fines': float(txns['effective_fine'].sum()),
        'issues_this_month': int(month_counts.get(this_month, 0)),
        'issues_last_month': int(month_counts.get(this_month - 1, 0)),
    }

def get_cleaned_shipments(region=None, db_path=DB_NAME):
    """Cleans shipment logs: transit time, delay and delivery status (Supply Chain case study)."""
    conn = get_connection(db_path)
    df = pd.read_sql_query("""
        SELECT sh.*, b.title AS book_title, d.dept_name
        FROM shipments sh
        JOIN books b ON sh.book_id = b.book_id
        JOIN departments d ON b.dept_id = d.dept_id;
    """, conn)
    conn.close()
    
    today = pd.Timestamp(datetime.now().date())
    df['dispatch_dt'] = pd.to_datetime(df['dispatch_date'])
    df['expected_dt'] = pd.to_datetime(df['expected_date'])
    df['delivery_dt'] = pd.to_datetime(df['delivery_date'])
    delivered = df['delivery_dt'].notnull()
    end = df['delivery_dt'].fillna(today)
    
    df['transit_days'] = (end - df['dispatch_dt']).dt.days
    df['delay_days'] = (end - df['expected_dt']).dt.days.clip(lower=0)
    df['status'] = np.select(
        [delivered & (df['delay_days'] == 0), delivered, ~delivered & (df['delay_days'] > 0)],
        ['Delivered On-Time', 'Delivered Late', 'Delayed In Transit'],
        default='In Transit'
    )
    df['dispatch_month'] = df['dispatch_dt'].dt.to_period('M').astype(str)
    if region:
        df = df[df['region'] == region]
    return df

if __name__ == "__main__":
    print("Testing Preprocessing Module...")
    df = get_cleaned_transactions()
    print(f"Cleaned Transactions shape: {df.shape}")
    print(df[['txn_id', 'student_name', 'book_title', 'days_kept', 'overdue_days', 'effective_fine', 'status']].head())
    print("\nDepartment Aggregate:")
    print(get_department_aggregates())
