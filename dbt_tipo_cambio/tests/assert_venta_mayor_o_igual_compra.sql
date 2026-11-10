-- Regla de negocio: el precio de venta no debería ser menor que el de compra.
-- En la fuente del BCRP existen unos pocos días históricos con esta anomalía
-- (diferencias < 0.01), por eso se marca como ADVERTENCIA y no detiene el pipeline.
{{ config(severity='warn') }}

select *
from {{ ref('fct_tipo_cambio_diario') }}
where tc_venta < tc_compra
