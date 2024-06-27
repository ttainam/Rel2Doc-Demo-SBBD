
# Configurações do PostgreSQL
PG_CONFIG = {
    'dbname': 'dbname_value',
    'user': 'user_value',
    'password': 'password_value',
    'host': 'host_value'
}

# Configurações do MongoDB
MONGO_CONFIG = {
    'host': 'MONGOHOST',
    'port': 27014,
    'dbname': 'MONGODBNAME',
}

# Insere o objectId nos campos Foreign Key que ficaram com ID.
INSERT_OBJECT_ID_REFERENCES = INSERT_OBJECT_ID_REFERENCES_VALUE

# Insere os campos com valores null
# Por conceito: bancos NoSQL não deveriam inserir valores não significativos.
INSERT_NULL_FIELDS = INSERT_NULL_FIELDS_VALUE
