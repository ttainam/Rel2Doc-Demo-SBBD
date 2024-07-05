import psycopg2
from bson.objectid import ObjectId
from pymongo import MongoClient
import pymongo
import traceback
import copy
from config import PG_CONFIG, MONGO_CONFIG, INSERT_OBJECT_ID_REFERENCES, INSERT_NULL_FIELDS
from utils import (convert_value, busca_todas_tabelas_postgress, busca_estrutura_tabela,
                   busca_quantidades_referencias, verifica_campo_pk, busca_campo_pk,
                   busca_conteudo_join_table_field, busca_campos_relacao_join_table, busca_campo_tabela_fk)
from join_tables import verify_join_tables
# Conexão com o banco de dados MongoDB
mongo_client = MongoClient(MONGO_CONFIG['host'], MONGO_CONFIG['port'])
mongo_db = mongo_client[MONGO_CONFIG['dbname']]

# Conexão com o banco de dados PostgreSQL
pg_connection = psycopg2.connect(**PG_CONFIG)

try:
    tabelas_verificadas = list()
    tabelas_join_verificadas = list()
    join_tables = verify_join_tables()
    # Buscar tabelas do PostgreSQL
    resultados = busca_todas_tabelas_postgress(pg_connection)

    table_info = [(table[0], table[1]) for table in resultados]

    for table, num_foreign_keys in table_info:
        if table in tabelas_verificadas or table in tabelas_join_verificadas:
            continue

        table_join = False
        table_to_add_collumn = False
        for sublist in join_tables:
            if sublist[0] == table:
                table_join = True
            if sublist[1] == table:
                table_to_add_collumn = True

        if table_join:
            continue

        # Quantidade de tabelas que referenciam a tabela atual (Tabela A)
        num_references_keys = busca_quantidades_referencias(pg_connection, table)

        new_column_names = []
        join_table_names = []
        campo_pk_joins = []
        join_table_2 = []
        if table_to_add_collumn:
            for sublist in join_tables:
                if sublist[1] == table:
                    new_column_names.append(f"_{sublist[2]}")
                    join_table_2.append(sublist[2])
                    join_table_names.append(sublist[0])
                    campo_pk_joins.append(busca_campo_pk(pg_connection, sublist[1])[0])

        if num_foreign_keys == 0 and num_references_keys == 1 and table not in join_table_2:
            continue
        
        # Buscar estrutura da tabela
        columns = busca_estrutura_tabela(pg_connection, table)

        # Buscar dados da tabela
        pg_cursor = pg_connection.cursor()
        pg_cursor.execute(f"SELECT * FROM {table};")
        data = pg_cursor.fetchall()

        # Inserir dados no MongoDB
        mongo_collection = mongo_db[table]
        for row in data:
            document = {}
            for i, value in enumerate(row):
                column_name = pg_cursor.description[i].name
                data_type = columns.get(column_name)

                if len(new_column_names) > 0 and column_name in campo_pk_joins:
                    for join_table_name, new_column_name in zip(join_table_names, new_column_names):
                        results = ''
                        result_dict = ''
                        infos_join = busca_campos_relacao_join_table(pg_connection, table, join_table_name)
                        if len(infos_join) >= 2:
                            column_names_search = busca_conteudo_join_table_field(pg_connection, infos_join[0], infos_join[1], value)
                            pg_cursor2 = pg_connection.cursor()
                            pg_cursor2.execute(f"SELECT {column_names_search} FROM {infos_join[0]} WHERE {infos_join[1]} = {value};")
                            results = pg_cursor2.fetchall()
                            column_names = [desc[0] for desc in pg_cursor2.description]
                            if results:
                                result_dict = [{col_name: col_value for col_name, col_value in zip(column_names, row)} for row in results]
                                new_result_dict = copy.deepcopy(result_dict)

                                if result_dict:
                                    for r in result_dict:
                                        for col_name, col_value in r.items():
                                            existe_fk_col = busca_campo_tabela_fk(pg_connection, infos_join[0], col_name)

                                            if len(existe_fk_col) > 0:
                                                #r.pop(col_name)
                                                num_references_keys_referenced_table = busca_quantidades_referencias(pg_connection, existe_fk_col[3])
                                                if num_references_keys_referenced_table == 1:
                                                    pg_cursor11 = pg_connection.cursor()
                                                    pg_cursor11.execute(
                                                        f"SELECT * FROM {existe_fk_col[3]} WHERE {existe_fk_col[4]} = {col_value};")
                                                    values = pg_cursor11.fetchone()
                                                    column_names_referenced = [desc[0] for desc in
                                                                               pg_cursor11.description]
                                                    col_value_subtable = {col_name: col_value for col_name, col_value in
                                                                          zip(column_names_referenced, values)}

                                                    col_value_name = existe_fk_col[3]
                                                    for name, valor in enumerate(column_names_referenced):
                                                        if name > 0:
                                                            is_pk = verifica_campo_pk(pg_connection,
                                                                                      existe_fk_col[3], valor)
                                                            if is_pk:
                                                                col_value_subtable[is_pk[0]] = col_value_subtable.pop(
                                                                    valor)

                                                    if existe_fk_col[3] not in tabelas_join_verificadas:
                                                        tabelas_join_verificadas.append(existe_fk_col[3])

                                                    new_result_dict = [
                                                        {**{key: val for key, val in obj.items() if key != existe_fk_col[4]},
                                                         existe_fk_col[3]: col_value_subtable} if obj.get(
                                                            existe_fk_col[4]) == col_value else obj
                                                        for obj in new_result_dict
                                                    ]

                                document[new_column_name] = new_result_dict

                            if infos_join[0] not in tabelas_join_verificadas:
                                tabelas_join_verificadas.append(infos_join[0])

                if num_foreign_keys == 0:
                    if convert_value(value):
                        document[column_name] = convert_value(value)
                    else:
                        if (value is None and INSERT_NULL_FIELDS) or value is not None:
                            document[column_name] = value

                elif num_foreign_keys > 0:
                    fk_info = verifica_campo_pk(pg_connection, table, column_name)

                    if fk_info and fk_info[0] != table:
                        # Quantidade de tabelas que referenciam a tabela referenciada (Tabela B)
                        num_references_keys_tabela_referenciada = busca_quantidades_referencias(pg_connection, fk_info[0])
                        if num_references_keys_tabela_referenciada == 1:
                            pg_cursor3 = pg_connection.cursor()
                            pg_cursor3.execute(f"SELECT * FROM {fk_info[0]} WHERE {fk_info[1]} = {value};")
                            foreign_object = pg_cursor3.fetchone()

                            column_names = [desc[0] for desc in pg_cursor3.description]
                            if foreign_object:
                                column_name = fk_info[0]
                                result_dict = {col_name: col_value for col_name, col_value in zip(column_names, foreign_object)}

                                fk_info_subtable = ''
                                col_value_name = ''
                                col_value_subtable = ''
                                for j, col_value in enumerate(foreign_object):
                                    col_name = column_names[j]  # Nome da coluna
                                    fk_info_subtable = verifica_campo_pk(pg_connection, fk_info[0], col_name)

                                    if fk_info_subtable:
                                        result_dict[fk_info_subtable[0]] = result_dict.pop(col_name)

                                        # Verificar se a subtabela (Tabela C) que
                                        # está contida em Tabela B somente tem uma referencia
                                        num_references_keys_referenced_table = busca_quantidades_referencias(pg_connection, fk_info_subtable[0])

                                        if num_references_keys_referenced_table == 1:
                                            pg_cursor10 = pg_connection.cursor()
                                            pg_cursor10.execute(f"SELECT * FROM {fk_info_subtable[0]} WHERE {fk_info_subtable[1]} = {col_value};")
                                            values = pg_cursor10.fetchone()
                                            column_names_referenced = [desc[0] for desc in pg_cursor10.description]
                                            col_value_subtable = {col_name: col_value for col_name, col_value in zip(column_names_referenced, values)}
                                            col_value_name = fk_info_subtable[0]

                                            for name, valor in enumerate(column_names_referenced):
                                                if name > 0:
                                                    is_pk = verifica_campo_pk(pg_connection, fk_info_subtable[0], valor)

                                                    if is_pk:
                                                        col_value_subtable[is_pk[0]] = col_value_subtable.pop(valor)

                                            if fk_info_subtable[0] not in tabelas_verificadas:
                                                tabelas_verificadas.append(fk_info_subtable[0])

                                if table not in tabelas_verificadas:
                                    tabelas_verificadas.append(table)

                                if fk_info[0] not in tabelas_verificadas:
                                    tabelas_verificadas.append(fk_info[0])

                                for key, valor in result_dict.items():
                                    if convert_value(valor) and ((valor is None and INSERT_NULL_FIELDS) or valor is not None):
                                        result_dict[key] = convert_value(valor)
                                    elif valor is None and INSERT_NULL_FIELDS is False:
                                        result_dict.pop(key)
                                document[column_name] = result_dict

                                if col_value_name and col_value_subtable:
                                    if (col_value_subtable is None and INSERT_NULL_FIELDS) or col_value_subtable is not None:
                                        result_dict[col_value_name] = col_value_subtable
                            else:
                                if (value is None and INSERT_NULL_FIELDS) or value is not None:
                                    document[column_name] = value
                        else:
                            document[fk_info[0]] = value
                    else:
                        if convert_value(value) and ((value is None and INSERT_NULL_FIELDS) or value is not None):
                            document[column_name] = convert_value(value)
                        elif (value is None and INSERT_NULL_FIELDS) or value is not None:
                            document[column_name] = value
            mongo_collection.insert_one(document)

    if INSERT_OBJECT_ID_REFERENCES:
        collection_names = mongo_db.list_collection_names()

        # Imprimir o conteúdo de todos os documentos em cada coleção
        for collection_name in collection_names:
            collection = mongo_db[collection_name]
            documents = collection.find()
            for document in documents:
                for collumn, value in document.items():
                    update_dict = {}
                    if isinstance(value, int):
                        coluna_pk = busca_campo_pk(pg_connection, collumn)
                        if coluna_pk is not None:
                            fk_info = verifica_campo_pk(pg_connection, collection_name, coluna_pk[0])
                            if fk_info and fk_info[0] != collection_name:
                                referenced_collection = mongo_db[fk_info[0]]
                                matching_document = referenced_collection.find_one({fk_info[1]: value})
                                if matching_document:
                                    mongo_db[collection_name].update_one(document,  {"$set": {collumn: ObjectId(matching_document['_id'])}})
                    if isinstance(value, dict):
                        for key, val in value.items():
                            if isinstance(val, int):
                                coluna_pk = busca_campo_pk(pg_connection, key)
                                if coluna_pk is not None:
                                    fk_info = verifica_campo_pk(pg_connection, collection_name, coluna_pk[0])
                                    if fk_info and fk_info[0] != collection_name:
                                        referenced_collection = mongo_db[fk_info[0]]
                                        matching_document = referenced_collection.find_one({fk_info[1]: val})
                                        if matching_document:
                                            update_dict[f"{collumn}.{key}"] = ObjectId(matching_document['_id'])
                            if isinstance(val, dict) and collumn != key:
                                for k, v in val.items():
                                    if isinstance(v, int):
                                        coluna_pk = busca_campo_pk(pg_connection, k)
                                        if coluna_pk is not None:
                                            fk_info = verifica_campo_pk(pg_connection, key, coluna_pk[0])
                                            if fk_info and fk_info[0] != key:
                                                referenced_collection = mongo_db[fk_info[0]]
                                                matching_document = referenced_collection.find_one({fk_info[1]: v})
                                                if matching_document:
                                                    update_dict[f"{collumn}.{key}.{k}"] = ObjectId(matching_document['_id'])
                    if update_dict:
                        mongo_db[collection_name].update_one({"_id": document["_id"]}, {"$set": update_dict})

except Exception as e:
    print("Erro:", e)
    traceback_str = traceback.format_exc()

    # Imprime o traceback
    print(traceback_str)
finally:
    pg_cursor.close()
    pg_connection.close()
    mongo_client.close()