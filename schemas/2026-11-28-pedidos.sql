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
