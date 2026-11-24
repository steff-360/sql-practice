import datetime, os, sys

colombia_tz = datetime.timezone(datetime.timedelta(hours=-5))
now_col = datetime.datetime.now(colombia_tz)
today = now_col.date()
date_str = today.isoformat()
idx = (now_col.timetuple().tm_yday - 1) % 15

challenges = [
    ("schemas", "productos.sql", """\
-- Schema: Catalogo de Productos con categorias e inventario
CREATE TABLE categorias (
    id     SERIAL PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL UNIQUE,
    slug   VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE productos (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(150) NOT NULL,
    descripcion  TEXT,
    precio       NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
    stock        INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    categoria_id INT REFERENCES categorias(id) ON DELETE SET NULL,
    activo       BOOLEAN DEFAULT TRUE,
    creado_en    TIMESTAMP DEFAULT NOW(),
    actualizado  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_productos_categoria ON productos(categoria_id);
CREATE INDEX idx_productos_activo    ON productos(activo);

INSERT INTO categorias (nombre, slug) VALUES
  ('Electronica', 'electronica'), ('Ropa', 'ropa'), ('Hogar', 'hogar');

INSERT INTO productos (nombre, precio, stock, categoria_id) VALUES
  ('Laptop Pro 15', 2500000, 10, 1),
  ('Auriculares Bluetooth', 150000, 50, 1),
  ('Camiseta Basica', 35000, 100, 2),
  ('Lampara LED', 45000, 30, 3);
"""),
    ("schemas", "pedidos.sql", """\
-- Schema: Sistema de Pedidos con detalle de items
CREATE TABLE clientes (
    id       SERIAL PRIMARY KEY,
    nombre   VARCHAR(100) NOT NULL,
    email    VARCHAR(150) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    ciudad   VARCHAR(60)
);

CREATE TABLE pedidos (
    id          SERIAL PRIMARY KEY,
    cliente_id  INT REFERENCES clientes(id),
    estado      VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente','pagado','enviado','cancelado')),
    total       NUMERIC(12,2) DEFAULT 0,
    fecha       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pedido_items (
    id          SERIAL PRIMARY KEY,
    pedido_id   INT REFERENCES pedidos(id) ON DELETE CASCADE,
    producto_id INT REFERENCES productos(id),
    cantidad    INT NOT NULL CHECK (cantidad > 0),
    precio_unit NUMERIC(10,2) NOT NULL
);

-- Trigger para actualizar total automaticamente
CREATE OR REPLACE FUNCTION actualizar_total_pedido()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE pedidos SET total = (
    SELECT COALESCE(SUM(cantidad * precio_unit), 0)
    FROM pedido_items WHERE pedido_id = COALESCE(NEW.pedido_id, OLD.pedido_id)
  ) WHERE id = COALESCE(NEW.pedido_id, OLD.pedido_id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_total_pedido
AFTER INSERT OR UPDATE OR DELETE ON pedido_items
FOR EACH ROW EXECUTE FUNCTION actualizar_total_pedido();
"""),
    ("schemas", "empleados.sql", """\
-- Schema: Recursos Humanos con jerarquia de reportes
CREATE TABLE departamentos (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(80) NOT NULL,
    piso    INT
);

CREATE TABLE empleados (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    cargo         VARCHAR(80),
    salario       NUMERIC(12,2),
    depto_id      INT REFERENCES departamentos(id),
    jefe_id       INT REFERENCES empleados(id),  -- autorreferencia
    fecha_ingreso DATE DEFAULT CURRENT_DATE,
    activo        BOOLEAN DEFAULT TRUE
);

INSERT INTO departamentos (nombre, piso) VALUES ('Desarrollo', 2), ('QA', 2), ('Administracion', 1);
INSERT INTO empleados (nombre, email, cargo, salario, depto_id) VALUES
  ('Stefani Sanchez', 'stefani@empresa.com', 'Full Stack Developer', 4500000, 1);
"""),
    ("queries", "join-examples.sql", """\
-- Ejemplos de JOINs: INNER, LEFT, RIGHT, FULL, CROSS
-- Basado en el schema de pedidos y productos

-- INNER JOIN: solo pedidos con items
SELECT p.id, c.nombre AS cliente, pi.cantidad, pr.nombre AS producto
FROM pedidos p
INNER JOIN clientes c    ON c.id = p.cliente_id
INNER JOIN pedido_items pi ON pi.pedido_id = p.id
INNER JOIN productos pr   ON pr.id = pi.producto_id;

-- LEFT JOIN: todos los clientes, con o sin pedidos
SELECT c.nombre, COUNT(p.id) AS total_pedidos
FROM clientes c
LEFT JOIN pedidos p ON p.cliente_id = c.id
GROUP BY c.id, c.nombre
ORDER BY total_pedidos DESC;

-- SELF JOIN: empleado y su jefe directo
SELECT e.nombre AS empleado, j.nombre AS jefe
FROM empleados e
LEFT JOIN empleados j ON j.id = e.jefe_id;

-- Encontrar productos nunca pedidos
SELECT pr.nombre FROM productos pr
LEFT JOIN pedido_items pi ON pi.producto_id = pr.id
WHERE pi.id IS NULL;
"""),
    ("queries", "window-functions.sql", """\
-- Window Functions: RANK, ROW_NUMBER, LAG, LEAD, SUM acumulado

-- Ranking de productos por ventas totales
SELECT
    pr.nombre,
    SUM(pi.cantidad) AS unidades_vendidas,
    RANK() OVER (ORDER BY SUM(pi.cantidad) DESC) AS ranking
FROM productos pr
JOIN pedido_items pi ON pi.producto_id = pr.id
GROUP BY pr.id, pr.nombre;

-- Comparar ventas de cada mes con el mes anterior (LAG)
SELECT
    DATE_TRUNC('month', fecha) AS mes,
    SUM(total) AS ventas,
    LAG(SUM(total)) OVER (ORDER BY DATE_TRUNC('month', fecha)) AS mes_anterior,
    SUM(total) - LAG(SUM(total)) OVER (ORDER BY DATE_TRUNC('month', fecha)) AS diferencia
FROM pedidos
WHERE estado = 'pagado'
GROUP BY DATE_TRUNC('month', fecha)
ORDER BY mes;

-- Acumulado de ventas (running total)
SELECT
    fecha::date,
    total,
    SUM(total) OVER (ORDER BY fecha) AS acumulado
FROM pedidos
WHERE estado = 'pagado'
ORDER BY fecha;
"""),
    ("queries", "cte-examples.sql", """\
-- CTEs (Common Table Expressions): legibilidad y reutilizacion

-- CTE simple: clientes con alto valor
WITH clientes_vip AS (
    SELECT cliente_id, SUM(total) AS valor_total
    FROM pedidos WHERE estado = 'pagado'
    GROUP BY cliente_id HAVING SUM(total) > 1000000
)
SELECT c.nombre, v.valor_total
FROM clientes_vip v
JOIN clientes c ON c.id = v.cliente_id
ORDER BY v.valor_total DESC;

-- CTE recursiva: jerarquia de empleados (arbol de reportes)
WITH RECURSIVE jerarquia AS (
    SELECT id, nombre, jefe_id, 0 AS nivel, nombre AS ruta
    FROM empleados WHERE jefe_id IS NULL
    UNION ALL
    SELECT e.id, e.nombre, e.jefe_id, h.nivel + 1, h.ruta || ' > ' || e.nombre
    FROM empleados e
    JOIN jerarquia h ON h.id = e.jefe_id
)
SELECT nivel, nombre, ruta FROM jerarquia ORDER BY ruta;

-- Multiples CTEs encadenados
WITH ventas_mes AS (
    SELECT DATE_TRUNC('month', fecha) AS mes, SUM(total) AS total
    FROM pedidos WHERE estado = 'pagado' GROUP BY 1
),
promedio AS (SELECT AVG(total) AS prom FROM ventas_mes)
SELECT mes, total, ROUND(total / prom * 100, 1) AS pct_vs_promedio
FROM ventas_mes, promedio ORDER BY mes;
"""),
    ("queries", "subqueries.sql", """\
-- Subqueries: escalares, en FROM, correlacionadas, EXISTS

-- Subquery escalar: precio promedio del catalogo
SELECT nombre, precio,
  ROUND(precio - (SELECT AVG(precio) FROM productos), 2) AS diferencia_vs_promedio
FROM productos ORDER BY diferencia_vs_promedio DESC;

-- Subquery en FROM (derivada)
SELECT dept_stats.*
FROM (
    SELECT depto_id, COUNT(*) AS empleados, AVG(salario) AS salario_promedio
    FROM empleados WHERE activo = TRUE
    GROUP BY depto_id
) AS dept_stats
WHERE salario_promedio > 3000000;

-- Subquery correlacionada: pedido mas reciente por cliente
SELECT c.nombre, (
    SELECT MAX(fecha) FROM pedidos p WHERE p.cliente_id = c.id
) AS ultimo_pedido
FROM clientes c;

-- EXISTS: clientes que hayan hecho al menos un pedido pagado
SELECT nombre FROM clientes c
WHERE EXISTS (
    SELECT 1 FROM pedidos p
    WHERE p.cliente_id = c.id AND p.estado = 'pagado'
);
"""),
    ("queries", "indexes-optimization.sql", """\
-- Estrategias de indexacion y optimizacion de queries

-- Ver tamano de tablas e indices
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Indice parcial: solo productos activos con stock bajo
CREATE INDEX idx_stock_bajo ON productos(stock) WHERE activo = TRUE AND stock < 10;

-- Indice compuesto para busquedas frecuentes
CREATE INDEX idx_pedidos_cliente_fecha ON pedidos(cliente_id, fecha DESC);

-- Indice de expresion: buscar por email en minuscula
CREATE INDEX idx_clientes_email_lower ON clientes(LOWER(email));

-- EXPLAIN ANALYZE para analizar un query
EXPLAIN ANALYZE
SELECT p.*, c.nombre FROM pedidos p
JOIN clientes c ON c.id = p.cliente_id
WHERE p.estado = 'pendiente' AND p.fecha > NOW() - INTERVAL '30 days';

-- Buscar queries lentos (requiere pg_stat_statements)
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
"""),
    ("queries", "transactions.sql", """\
-- Transacciones: ACID, SAVEPOINT, ROLLBACK

-- Transaccion de pago de pedido
BEGIN;
  -- Verificar stock disponible
  SELECT id, stock FROM productos WHERE id = 1 FOR UPDATE;

  -- Descontar stock
  UPDATE productos SET stock = stock - 2 WHERE id = 1 AND stock >= 2;

  -- Si no hubo cambio, rollback
  -- (manejo en aplicacion: verificar rowcount)

  -- Actualizar estado del pedido
  UPDATE pedidos SET estado = 'pagado' WHERE id = 1;

  -- Registrar en log de pagos (tabla no mostrada)
  INSERT INTO pagos (pedido_id, monto, metodo) VALUES (1, 150000, 'tarjeta');

COMMIT;

-- SAVEPOINT para rollback parcial
BEGIN;
  INSERT INTO clientes (nombre, email) VALUES ('Test', 'test@test.com');
  SAVEPOINT sp1;

  INSERT INTO pedidos (cliente_id, estado) VALUES (currval('clientes_id_seq'), 'pendiente');
  -- Si algo falla:
  ROLLBACK TO sp1;
  -- continuar sin el pedido pero con el cliente

COMMIT;
"""),
    ("queries", "upsert-patterns.sql", """\
-- UPSERT: INSERT ... ON CONFLICT para operaciones idempotentes

-- Upsert simple por clave unica
INSERT INTO clientes (nombre, email, ciudad)
VALUES ('Ana Garcia', 'ana@example.com', 'Bogota')
ON CONFLICT (email) DO UPDATE SET
  nombre   = EXCLUDED.nombre,
  ciudad   = EXCLUDED.ciudad;

-- Upsert con condicion (solo si cambia algo)
INSERT INTO productos (nombre, precio, stock, categoria_id)
VALUES ('Laptop Gaming', 3200000, 5, 1)
ON CONFLICT (id) DO UPDATE SET
  precio = EXCLUDED.precio,
  stock  = EXCLUDED.stock
WHERE productos.precio <> EXCLUDED.precio OR productos.stock <> EXCLUDED.stock;

-- Upsert ignorando conflictos (DO NOTHING)
INSERT INTO categorias (nombre, slug)
SELECT unnest(ARRAY['Libros', 'Deportes', 'Electronica']),
       unnest(ARRAY['libros', 'deportes', 'electronica'])
ON CONFLICT (slug) DO NOTHING;

-- Conteo de visitas (increment o insert)
INSERT INTO page_views (url, views) VALUES ('/home', 1)
ON CONFLICT (url) DO UPDATE SET views = page_views.views + 1;
"""),
    ("queries", "recursive-cte.sql", """\
-- CTEs Recursivas: arboles, grafos, secuencias

-- Generar serie de fechas (alternativa a generate_series)
WITH RECURSIVE fechas AS (
    SELECT '2026-01-01'::DATE AS fecha
    UNION ALL
    SELECT fecha + 1 FROM fechas WHERE fecha < '2026-01-31'
)
SELECT fecha, TO_CHAR(fecha, 'Day') AS dia_semana FROM fechas;

-- Recorrer arbol de categorias anidadas
WITH RECURSIVE cat_tree AS (
    SELECT id, nombre, NULL::INT AS padre_id, 0 AS nivel
    FROM categorias WHERE padre_id IS NULL
    UNION ALL
    SELECT c.id, c.nombre, c.padre_id, t.nivel + 1
    FROM categorias c JOIN cat_tree t ON t.id = c.padre_id
)
SELECT REPEAT('  ', nivel) || nombre AS categoria FROM cat_tree ORDER BY nivel, nombre;

-- Sumar ventas acumuladas por mes con recursion (alternativa a window)
WITH RECURSIVE meses AS (
    SELECT DATE_TRUNC('month', MIN(fecha)) AS mes FROM pedidos
    UNION ALL
    SELECT mes + INTERVAL '1 month' FROM meses
    WHERE mes < DATE_TRUNC('month', NOW())
)
SELECT m.mes, COALESCE(SUM(p.total), 0) AS ventas
FROM meses m
LEFT JOIN pedidos p ON DATE_TRUNC('month', p.fecha) = m.mes AND p.estado = 'pagado'
GROUP BY m.mes ORDER BY m.mes;
"""),
    ("queries", "json-operations.sql", """\
-- Operaciones JSON en PostgreSQL: JSONB, path, agregacion

-- Columna JSONB en tabla de configuracion
CREATE TABLE configuraciones (
    id      SERIAL PRIMARY KEY,
    entidad VARCHAR(50),
    config  JSONB
);

INSERT INTO configuraciones (entidad, config) VALUES
  ('app', '{"theme":"dark","lang":"es","features":{"notifications":true,"analytics":false}}'),
  ('api', '{"rate_limit":100,"timeout":30,"cors":["localhost","kjlpo.netlify.app"]}');

-- Acceder a valores anidados
SELECT entidad, config->>'theme', config->'features'->>'notifications'
FROM configuraciones WHERE entidad = 'app';

-- Buscar en arrays JSONB
SELECT * FROM configuraciones
WHERE config->'cors' ? 'localhost';

-- Actualizar un campo anidado
UPDATE configuraciones
SET config = jsonb_set(config, '{features,analytics}', 'true')
WHERE entidad = 'app';

-- Agregar JSONB en queries (construir objeto resultado)
SELECT jsonb_build_object(
    'total_pedidos', COUNT(*),
    'monto_total',   SUM(total),
    'cliente',       MAX(c.nombre)
) AS resumen
FROM pedidos p JOIN clientes c ON c.id = p.cliente_id
GROUP BY p.cliente_id;
"""),
    ("queries", "performance-tips.sql", """\
-- Tips de rendimiento y queries comunes de diagnostico

-- Conexiones activas
SELECT pid, usename, application_name, state, query_start,
  NOW() - query_start AS duracion, left(query, 100) AS query_preview
FROM pg_stat_activity WHERE state != 'idle' ORDER BY duracion DESC;

-- Tablas con mas escrituras (candidatas a optimizar)
SELECT relname, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
FROM pg_stat_user_tables ORDER BY n_tup_upd + n_tup_del DESC LIMIT 10;

-- Indices no usados (candidatos a eliminar)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes WHERE idx_scan = 0 ORDER BY tablename;

-- Bloat de tablas (espacio desperdiciado)
SELECT tablename,
  pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS total,
  pg_size_pretty(pg_relation_size(tablename::regclass)) AS table_only
FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(tablename::regclass) DESC;

-- VACUUM y ANALYZE para mantenimiento
VACUUM ANALYZE pedidos;
VACUUM ANALYZE productos;
"""),
    ("queries", "stored-procedures.sql", """\
-- Procedimientos almacenados y funciones en PL/pgSQL

-- Funcion: calcular descuento por volumen
CREATE OR REPLACE FUNCTION calcular_descuento(precio NUMERIC, cantidad INT)
RETURNS NUMERIC AS $$
BEGIN
  RETURN CASE
    WHEN cantidad >= 100 THEN precio * 0.80
    WHEN cantidad >= 50  THEN precio * 0.90
    WHEN cantidad >= 10  THEN precio * 0.95
    ELSE precio
  END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

SELECT nombre, precio, calcular_descuento(precio, 50) AS precio_con_descuento
FROM productos;

-- Procedimiento: procesar pedido completo
CREATE OR REPLACE PROCEDURE procesar_pedido(
    p_cliente_id INT, p_items JSONB
) LANGUAGE plpgsql AS $$
DECLARE
    v_pedido_id INT;
    v_item JSONB;
BEGIN
    INSERT INTO pedidos (cliente_id) VALUES (p_cliente_id) RETURNING id INTO v_pedido_id;
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        INSERT INTO pedido_items (pedido_id, producto_id, cantidad, precio_unit)
        SELECT v_pedido_id,
               (v_item->>'producto_id')::INT,
               (v_item->>'cantidad')::INT,
               precio
        FROM productos WHERE id = (v_item->>'producto_id')::INT;
    END LOOP;
    COMMIT;
END;
$$;
"""),
    ("queries", "triggers.sql", """\
-- Triggers para auditoría y validaciones automaticas

-- Tabla de auditoria generica
CREATE TABLE auditoria (
    id         SERIAL PRIMARY KEY,
    tabla      VARCHAR(50),
    operacion  VARCHAR(10),
    registro   JSONB,
    usuario    VARCHAR(50) DEFAULT current_user,
    fecha      TIMESTAMP DEFAULT NOW()
);

-- Trigger generico de auditoria
CREATE OR REPLACE FUNCTION fn_auditar()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO auditoria (tabla, operacion, registro)
  VALUES (TG_TABLE_NAME, TG_OP, row_to_json(COALESCE(NEW, OLD)));
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tgr_auditar_productos
AFTER INSERT OR UPDATE OR DELETE ON productos
FOR EACH ROW EXECUTE FUNCTION fn_auditar();

-- Trigger de validacion: precio no puede bajar mas del 50%
CREATE OR REPLACE FUNCTION fn_validar_precio()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.precio < OLD.precio * 0.5 THEN
    RAISE EXCEPTION 'El precio no puede reducirse mas del 50%% en un solo cambio';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tgr_precio_productos
BEFORE UPDATE ON productos
FOR EACH ROW WHEN (OLD.precio IS DISTINCT FROM NEW.precio)
EXECUTE FUNCTION fn_validar_precio();
"""),
]

folder, name, content = challenges[idx]
os.makedirs(folder, exist_ok=True)
base_target = os.path.join(folder, f"{date_str}-{name}")
target = base_target
v = 2
while os.path.exists(target):
    target = os.path.join(folder, f"{date_str}-v{v}-{name}")
    v += 1
with open(target, "w") as f:
    f.write(content)
print(f"Created: {target}")
