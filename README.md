# Rel2Doc:  Migrating Data from Relational to Document-Oriented Databases

Article on ERBD 2024: https://sol.sbc.org.br/index.php/erbd/article/view/28489

# Instructions for use:

## 1. Install python
https://www.python.org/downloads/

## 2. Install pip
https://pip.pypa.io/en/stable/installation/

## 3. install packages
Go to folder /pyFiles and run the command:

```pycon
  pip install -r requirements.txt
```

## 4. Copy file
Go to base directory and run:
```
  cp .env-example .env
```

## 5. install composer & dependences
https://getcomposer.org/

After install, go to base directory and run:
```
composer install
```
## 6. Run
```php
symfony server:start
```
## 7. Use
Acess route http://localhost:8000/, put your sistems data and begin process.
![image](https://github.com/ttainam/migration_demo/assets/20916133/b865873b-a5b4-44fb-b0dc-5a6abce5a56f)


## ATENTION !
Verifiy these php.ini params:

```php
max_input_time = -1;
max_execution_time = 600;
```

# Help?
[EN-US] https://github.com/ttainam/tcc/blob/main/docs.md#file-documentation


[PT-BR] https://github.com/ttainam/tcc/blob/main/docs.md#documenta%C3%A7%C3%A3o-dos-arquivos
