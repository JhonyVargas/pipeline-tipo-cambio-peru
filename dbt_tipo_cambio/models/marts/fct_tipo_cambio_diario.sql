-- Tabla de hechos diaria con métricas para análisis de negocio.

with base as (

    select * from {{ ref('stg_tipo_cambio') }}

)

select
    fecha,
    year(fecha)                                   as anio,
    month(fecha)                                  as mes,
    tc_compra,
    tc_venta,
    round((tc_compra + tc_venta) / 2, 4)          as tc_promedio,
    round(tc_venta - tc_compra, 4)                as spread,
    round(
        (tc_venta / lag(tc_venta) over (order by fecha) - 1) * 100, 4
    )                                             as var_diaria_pct,
    round(avg(tc_venta) over (
        order by fecha rows between 6 preceding and current row
    ), 4)                                         as media_movil_7d,
    round(avg(tc_venta) over (
        order by fecha rows between 29 preceding and current row
    ), 4)                                         as media_movil_30d
from base
order by fecha
