-- Resumen anual del tipo de cambio venta.

with diario as (

    select * from {{ ref('fct_tipo_cambio_diario') }}

),

anual as (

    select
        anio,
        count(*)                              as dias_habiles,
        arg_min(tc_venta, fecha)              as apertura,
        arg_max(tc_venta, fecha)              as cierre,
        max(tc_venta)                         as maximo,
        min(tc_venta)                         as minimo,
        round(avg(tc_venta), 4)               as promedio_venta,
        round(stddev_samp(var_diaria_pct), 4) as volatilidad_pct
    from diario
    group by anio

)

select
    *,
    round((cierre / apertura - 1) * 100, 3) as var_anual_pct
from anual
order by anio
