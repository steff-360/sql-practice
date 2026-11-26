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
