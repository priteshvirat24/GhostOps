import psycopg

try:
    conn = psycopg.connect("postgresql://pritesh:ysRDe3WNkWdFAoptajYf0Q@valid-shaman-32362.j77.aws-ap-south-1.cockroachlabs.cloud:26257/ghostops?sslmode=verify-full&sslrootcert=/Users/priteshhome/.postgresql/root.crt", autocommit=True, connect_timeout=5)
    cur = conn.cursor()
    cur.execute("SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid();")
    print("Cancelled other backends.")
except Exception as e:
    print(f"Error: {e}")
