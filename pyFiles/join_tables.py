import psycopg2
import traceback
from config import PG_CONFIG
from utils import busca_quantidades_colunas, busca_todas_tabelas_postgress, busca_qtde_campo_pk, busca_quantidades_referencias, busca_tabelas_pk_joins


def verify_join_tables():
    pg_connection = psycopg2.connect(**PG_CONFIG)

    try:
        # Buscar tabelas do PostgreSQL
        resultados = busca_todas_tabelas_postgress(pg_connection)

        table_info = [(table[0], table[1]) for table in resultados]
        join_tables = list()
        for table, num_foreign_keys in table_info:
            colunas_nao_pk = busca_quantidades_colunas(pg_connection, table) - busca_qtde_campo_pk(pg_connection, table)
            num_references_keys = busca_quantidades_referencias(pg_connection, table)

            if num_foreign_keys == 2 and num_references_keys == 0:
                colunas_nao_pk -= num_foreign_keys
                if colunas_nao_pk < 1:
                    referenciadas = busca_tabelas_pk_joins(pg_connection, table)
                    join_tables.append([table] + referenciadas)
        return join_tables
    except Exception as e:
        print("Erro:", e)
        traceback_str = traceback.format_exc()

        # Imprime o traceback
        print(traceback_str)
    finally:
        pg_connection.close()


print(verify_join_tables())