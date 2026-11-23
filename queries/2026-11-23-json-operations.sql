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
