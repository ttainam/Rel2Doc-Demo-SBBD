
# Configurações do PostgreSQL
PG_CONFIG = {
    'dbname': 'rental',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost'
}

# Configurações do MongoDB
MONGO_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'dbname': 'rental5',
}

# Insere o objectId nos campos Foreign Key que ficaram com ID.
INSERT_OBJECT_ID_REFERENCES = 1

# Insere os campos com valores null
# Por conceito: bancos NoSQL não deveriam inserir valores não significativos.
INSERT_NULL_FIELDS = 1
