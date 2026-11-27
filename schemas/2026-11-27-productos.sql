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
