-- Control de calidad: valores fuera de un rango razonable indican error en la fuente.
select *
from {{ ref('fct_tipo_cambio_diario') }}
where tc_venta not between 2.5 and 5.0
   or tc_compra not between 2.5 and 5.0
