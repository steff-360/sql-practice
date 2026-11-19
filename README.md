# SQL Practice

Coleccion de ejercicios, retos y esquemas SQL con PostgreSQL y MySQL.

## Contenido

```
/schemas        - Disenos de base de datos con DDL
/queries        - Consultas de practica (SELECT, JOIN, subqueries)
/challenges     - Retos avanzados (window functions, CTEs)
```

## Como ejecutar

```bash
# PostgreSQL
psql -U postgres -d practice -f schemas/biblioteca.sql

# MySQL
mysql -u root -p practice < schemas/tienda.sql
```
