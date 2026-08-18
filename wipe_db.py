import psycopg

conn = psycopg.connect("postgresql://pritesh:ysRDe3WNkWdFAoptajYf0Q@valid-shaman-32362.j77.aws-ap-south-1.cockroachlabs.cloud:26257/ghostops?sslmode=verify-full&sslrootcert=/Users/priteshhome/.postgresql/root.crt", autocommit=True)
cur = conn.cursor()

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE';
""")
tables = cur.fetchall()

for table in tables:
    table_name = table[0]
    print(f"Dropping table {table_name}...")
    cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

print("All tables dropped.")
