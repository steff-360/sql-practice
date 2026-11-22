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
