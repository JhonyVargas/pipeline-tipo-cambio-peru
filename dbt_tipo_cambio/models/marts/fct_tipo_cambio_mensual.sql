-- Resumen mensual: apertura, cierre, máximo, mínimo (OHLC), promedio y volatilidad.

with diario as (

    select * from {{ ref('fct_tipo_cambio_diario') }}

),

mensual as (

    select
        date_trunc('month', fecha)::date      as periodo,
        anio,
        mes,
        count(*)                              as dias_habiles,
        arg_min(tc_venta, fecha)              as apertura,
        arg_max(tc_venta, fecha)              as cierre,
        max(tc_venta)                         as maximo,
        min(tc_venta)                         as minimo,
        round(avg(tc_venta), 4)               as promedio_venta,
        round(avg(tc_compra), 4)              as promedio_compra,
        round(avg(spread), 4)                 as spread_promedio,
        round(stddev_samp(var_diaria_pct), 4) as volatilidad_pct
    from diario
    group by 1, 2, 3

)

select
    *,
    round((cierre / lag(cierre) over (order by periodo) - 1) * 100, 3) as var_mensual_pct
from mensual
order by periodo
