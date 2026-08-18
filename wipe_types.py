import psycopg

conn = psycopg.connect("postgresql://pritesh:ysRDe3WNkWdFAoptajYf0Q@valid-shaman-32362.j77.aws-ap-south-1.cockroachlabs.cloud:26257/ghostops?sslmode=verify-full&sslrootcert=/Users/priteshhome/.postgresql/root.crt", autocommit=True)
cur = conn.cursor()

# Get all enum types in the public schema
cur.execute("""
    SELECT t.typname
    FROM pg_type t
    JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'public' AND t.typtype = 'e';
""")
types = cur.fetchall()

for typ in types:
    typ_name = typ[0]
    if typ_name.startswith('crdb_'):
        continue
    print(f"Dropping type {typ_name}...")
    try:
        cur.execute(f"DROP TYPE IF EXISTS {typ_name};")
    except Exception as e:
        print(f"Failed to drop {typ_name}: {e}")

print("All types dropped.")
