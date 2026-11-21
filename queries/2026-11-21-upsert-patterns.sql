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
