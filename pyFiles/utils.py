import psycopg2
from decimal import Decimal
from datetime import date


def convert_value(value):
    if isinstance(value, Decimal) and value > 0.00:
        return float(value)
    elif isinstance(value, date):
        return value.isoformat()
    elif isinstance(value, memoryview):
        return bytes(value)


def busca_todas_tabelas_postgress(pg_connection):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(
        "SELECT t.table_name, COUNT(constraint_name) AS num_foreign_keys FROM information_schema.tables t LEFT JOIN information_schema.table_constraints tc ON t.table_name = tc.table_name AND constraint_type = 'FOREIGN KEY' WHERE t.table_schema = 'public' and t.table_type = 'BASE TABLE'  GROUP BY t.table_name ORDER BY num_foreign_keys DESC;")
    return pg_cursor.fetchall()

def busca_estrutura_tabela(pg_connection, table):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';")
    return {row[0]: row[1] for row in pg_cursor.fetchall()}

def busca_quantidades_referencias(pg_connection, table):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(
        f"SELECT count(tc.table_name) FROM information_schema.constraint_column_usage cu JOIN information_schema.table_constraints tc ON cu.constraint_name = tc.constraint_name WHERE tc.constraint_type = 'FOREIGN KEY' AND cu.table_name = '{table}'")
    return pg_cursor.fetchone()[0]

def verifica_campo_pk(pg_connection, table, collumn):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(
        f"SELECT ccu.table_name AS referenced_table, ccu.column_name AS referenced_column FROM information_schema.key_column_usage kcu JOIN information_schema.constraint_column_usage ccu ON kcu.constraint_name = ccu.constraint_name WHERE kcu.table_name = '{table}' AND kcu.column_name = '{collumn}' AND ccu.table_name !='{table}'")
    return pg_cursor.fetchone()

def busca_campo_pk(pg_connection, table):
    try:
        pg_cursor = pg_connection.cursor()
        pg_cursor.execute(
            f"SELECT cu.column_name FROM information_schema.tables t LEFT JOIN information_schema.table_constraints tc ON t.table_name = tc.table_name JOIN information_schema.constraint_column_usage cu ON cu.constraint_name = tc.constraint_name WHERE tc.constraint_type = 'PRIMARY KEY' AND t.table_name = '{table}';")
        return pg_cursor.fetchone()
    except psycopg2.Error as e:
        return False

def busca_quantidades_colunas(pg_connection, table):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(
        f"SELECT count(*) AS quantidade_colunas FROM pg_attribute WHERE attrelid = '{table}'::regclass AND attnum > 0 AND NOT attisdropped;")
    return pg_cursor.fetchone()[0]


def busca_qtde_campo_pk(pg_connection, table):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(
        f"SELECT count(tc.table_name) FROM information_schema.constraint_column_usage cu JOIN information_schema.table_constraints tc ON cu.constraint_name = tc.constraint_name WHERE tc.constraint_type = 'PRIMARY KEY' AND cu.table_name = '{table}'")
    return pg_cursor.fetchone()[0]

def busca_tabelas_pk_joins(pg_connection, table):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(f"""SELECT cu.table_name FROM information_schema.constraint_column_usage cu JOIN information_schema.table_constraints tc ON cu.constraint_name = tc.constraint_name WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = '{table}' ORDER BY ( SELECT count(*) FROM information_schema.table_constraints tc2 JOIN information_schema.constraint_column_usage cu2 ON tc2.constraint_name = cu2.constraint_name
    WHERE tc2.constraint_type = 'FOREIGN KEY' AND tc2.table_name = cu.table_name ) DESC;""")
    return [row[0] for row in pg_cursor.fetchall()]


def busca_conteudo_join_table_field(pg_connection, table, field, value_search):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name <> '{field}';")
    fields = pg_cursor.fetchall()
    column_names = ', '.join([col[0] for col in fields])

    return column_names

def busca_campos_relacao_join_table(pg_connection, table, table_join):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(f"""SELECT
    	                    kcu.table_name,
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM
                            information_schema.table_constraints AS tc
                        JOIN
                            information_schema.key_column_usage AS kcu
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                        JOIN
                            information_schema.constraint_column_usage AS ccu
                            ON ccu.constraint_name = tc.constraint_name
                            AND ccu.table_schema = tc.table_schema
                        WHERE
                            tc.constraint_type = 'FOREIGN KEY'
                            AND tc.table_name='{table_join}'
                            AND ccu.table_name='{table}';""")
    results = pg_cursor.fetchall()
    return [field for row in results for field in row]


def busca_campo_tabela_fk(pg_connection, table, field):
    pg_cursor = pg_connection.cursor()
    pg_cursor.execute(f"""SELECT
                            tc.constraint_name, 
                            tc.table_name AS local_table,
                            kcu.column_name AS local_column,
                            ccu.table_name AS foreign_table,
                            ccu.column_name AS foreign_column
                        FROM 
                            information_schema.table_constraints AS tc 
                        JOIN 
                            information_schema.key_column_usage AS kcu 
                        ON 
                            tc.constraint_catalog = kcu.constraint_catalog
                            AND tc.constraint_schema = kcu.constraint_schema
                            AND tc.constraint_name = kcu.constraint_name
                        JOIN 
                            information_schema.constraint_column_usage AS ccu 
                        ON 
                            tc.constraint_name = ccu.constraint_name
                            AND tc.constraint_schema = ccu.constraint_schema
                        WHERE 
                            tc.constraint_type = 'FOREIGN KEY'
                            AND tc.table_name = '{table}'
                            AND kcu.column_name = '{field}';""")
    results = pg_cursor.fetchall()
    return [field for row in results for field in row]