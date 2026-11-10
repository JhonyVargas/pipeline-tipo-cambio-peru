-- Limpieza: convierte la fecha en texto del BCRP ('02.Ene.20') a DATE,
-- los valores de texto a número y descarta días sin dato ('n.d.').

with fuente as (

    select * from {{ source('bcrp', 'tipo_cambio_bcrp') }}

),

partes as (

    select
        cast(split_part(periodo, '.', 1) as integer)        as dia,
        lower(split_part(periodo, '.', 2))                   as mes_txt,
        2000 + cast(split_part(periodo, '.', 3) as integer)  as anio,
        try_cast(compra as double)                           as tc_compra,
        try_cast(venta  as double)                           as tc_venta,
        cargado_en
    from fuente

),

fechas as (

    select
        make_date(
            anio,
            case mes_txt
                when 'ene' then 1  when 'feb' then 2  when 'mar' then 3
                when 'abr' then 4  when 'may' then 5  when 'jun' then 6
                when 'jul' then 7  when 'ago' then 8  when 'set' then 9
                when 'sep' then 9  when 'oct' then 10 when 'nov' then 11
                when 'dic' then 12
            end,
            dia
        )                       as fecha,
        round(tc_compra, 4)     as tc_compra,
        round(tc_venta, 4)      as tc_venta,
        cargado_en
    from partes

)

select *
from fechas
where tc_compra is not null
  and tc_venta  is not null
