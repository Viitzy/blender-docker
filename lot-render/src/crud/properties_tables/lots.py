from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import Dict, Any, List
from decimal import Decimal
import numpy as np

from shared.utils.constants import LOT_STATUS_ID_DISPONIVEL


def get_lot_details(db: Session, lot_id: int):
    sql_query = """
            select l.lot_id,
                    l.title,
                    l.link,
                    l.condominium_fee,
                    l.viva_real_code,
                    l.processed,
                    l.latitude,
                    l.longitude,
                    l.description,
                    l.weight,
                    s.street_name           as street,
                    la.number,
                    la.complement,
                    la.postal_code,
                    c.condominium_name,
                    n.neighborhood_name     as neighborhood,
                    ci.city_name,
                    st.state_name,
                    st.state_acr,
                    co.country_name,
                    stat.lot_status_name,
                    lp.price                as lot_price,
                    lar.area                as lot_area,
                    CASE
                        WHEN la.number = 'N/A' THEN 'N'
                        ELSE 'Y'
                        END                 AS complete_address,
                    CONCAT(s.street_name, ', ', la.number, ', ', n.neighborhood_name, ', ', ci.city_name, ', ', st.state_name, ', ',
                            co.country_name) AS lot_address,
                    ARRAY [
                        'https://storage.yandexcloud.net/apartment-images/2.jpg',
                        'https://storage.yandexcloud.net/apartment-images/2.jpg',
                        'https://storage.yandexcloud.net/apartment-images/2.jpg',
                        'https://storage.yandexcloud.net/apartment-images/2.jpg'
                        ]                   AS lot_images,
                    5                       as rating,
                    1                       as region_id
                from properties.lots l
                        join properties.lot_addresses la on l.lot_id = la.lot_id
                        join global.addresses a on la.address_id = a.address_id
                        join global.street s on a.street_id = s.street_id
                        join global.neighborhoods n on a.neighborhood_id = n.neighborhood_id
                        join global.cities ci on n.city_id = ci.city_id
                        join global.states st on ci.state_id = st.state_id
                        join global.countries co on st.country_id = co.country_id
                        join properties.lot_status_history ls ON l.lot_status_history_id = ls.lot_status_history_id
                        join properties.lot_status stat on ls.lot_status_id = stat.lot_status_id
                        join properties.lot_price_history lp ON l.lot_price_history_id = lp.lot_price_history_id
                        join properties.lot_area_history lar ON l.lot_area_history_id = lar.lot_area_history_id
                        join global.condominiums c on la.condominium_id = c.condominium_id
                where la.number != 'N/A'
            AND l.lot_id = :lot_id
            AND ls.lot_status_id = :lot_status_id
            """

    lot = (
        db.execute(
            text(sql_query),
            {"lot_id": lot_id, "lot_status_id": LOT_STATUS_ID_DISPONIVEL},
        )
        .mappings()
        .first()
    )
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    # montar resposta
    lot_price = float(lot.lot_price) if lot.lot_price else 0.0
    lot_area = float(lot.lot_area) if lot.lot_area else 0.0

    # obter o endereço completo
    complete_address = (
        "Y"
        if all(
            [
                lot.street and lot.street != "NaN",
                lot.number is not None,
                lot.neighborhood and lot.neighborhood != "NaN",
            ]
        )
        else "N"
    )
    lot_address = f"{lot.street}, {lot.number}, {lot.neighborhood}, {lot.city_name}, {lot.state_name}, {lot.country_name}"

    # retornar os dados do lote
    lot_data = {
        "lot_id": lot.lot_id,
        "title": lot.title or lot.neighborhood or "",
        "lot_area": lot_area,
        "lot_address": lot_address,
        "latitude": float(lot.latitude) if lot.latitude else None,
        "longitude": float(lot.longitude) if lot.longitude else None,
        "lot_price": lot_price,
        "complete_address": complete_address,
        "city": lot.city_name,
        "state": lot.state_name,
        "country": lot.country_name,
        "neighborhood": lot.neighborhood,
        "rating": 5,
        "lot_images": ", ".join(
            ["https://storage.yandexcloud.net/apartment-images/2.jpg"] * 4
        ),
    }

    return lot_data


def search_lots_relevant_locations(db: Session, q: str, limit: int = 5):
    # obter sugestões
    query = """
        SELECT CASE
                WHEN c.condominium_id is not null THEN 'Condomínio'
                ELSE 'Bairro'
                END         AS type,
            CASE
                WHEN c.condominium_id is not null THEN c.condominium_id
                ELSE n.neighborhood_id
                END         AS id,
            CASE
                WHEN c.condominium_id is not null THEN c.condominium_name
                ELSE neighborhood_name
                END         AS value,
            count(l.lot_id) AS count,
            ci.city_name    as reference,
            1               AS priority
        FROM properties.lots l
                join properties.lot_addresses la on l.lot_id = la.lot_id
                join global.addresses a on la.address_id = a.address_id
                join global.street s on a.street_id = s.street_id
                join global.neighborhoods n on a.neighborhood_id = n.neighborhood_id
                join global.cities ci on n.city_id = ci.city_id
                join global.states st on ci.state_id = st.state_id
                join global.countries co on st.country_id = co.country_id
                join properties.lot_status_history ls ON l.lot_status_history_id = ls.lot_status_history_id
                left join global.condominiums c on la.condominium_id = c.condominium_id
        WHERE unaccent(c.condominium_name) ilike unaccent(:query) or unaccent(n.neighborhood_name) ilike unaccent(:query)
        AND ls.lot_status_id = :lot_status_id
        GROUP BY c.condominium_id, c.condominium_name, n.neighborhood_id, n.neighborhood_name, ci.city_id

        UNION ALL

        SELECT 'Cidade'        AS type,
            ci.city_id       AS id,
            ci.city_name     AS value,
            count(l.lot_id) AS count,
            st.state_acr    as reference,
            2               AS priority
        FROM properties.lots l
                join properties.lot_addresses la on l.lot_id = la.lot_id
                join global.addresses a on la.address_id = a.address_id
                join global.street s on a.street_id = s.street_id
                join global.neighborhoods n on a.neighborhood_id = n.neighborhood_id
                join global.cities ci on n.city_id = ci.city_id
                join global.states st on ci.state_id = st.state_id
                join global.countries co on st.country_id = co.country_id
                join properties.lot_status_history ls ON l.lot_status_history_id = ls.lot_status_history_id
                left join global.condominiums c on la.condominium_id = c.condominium_id
        WHERE unaccent(ci.city_name) ILIKE unaccent(:query)
        AND ls.lot_status_id = :lot_status_id
        GROUP BY ci.city_id, ci.city_name, st.state_acr

        UNION ALL

        SELECT 'Estado'        AS type,
            st.state_id      AS id,
            st.state_name    AS value,
            count(l.lot_id) AS count,
            co.country_name as reference,
            3               AS priority
        FROM properties.lots l
                join properties.lot_addresses la on l.lot_id = la.lot_id
                join global.addresses a on la.address_id = a.address_id
                join global.street s on a.street_id = s.street_id
                join global.neighborhoods n on a.neighborhood_id = n.neighborhood_id
                join global.cities ci on n.city_id = ci.city_id
                join global.states st on ci.state_id = st.state_id
                join global.countries co on st.country_id = co.country_id
                join properties.lot_status_history ls ON l.lot_status_history_id = ls.lot_status_history_id
                left join global.condominiums c on la.condominium_id = c.condominium_id
        WHERE unaccent(st.state_name) ilike unaccent(:query)
        AND ls.lot_status_id = :lot_status_id
        GROUP BY st.state_id, st.state_name, co.country_name

        ORDER BY count desc, priority
        LIMIT :limit
    """

    params = {"query": f"%{q}%"} if len(q) >= 3 else {"query": f"{q}%%"}
    params["limit"] = limit
    params["lot_status_id"] = LOT_STATUS_ID_DISPONIVEL
    locations = db.execute(text(query), params).fetchall()

    response = {"locations": locations}

    return response


def get_lot_list(
    db: Session,
    south: float,
    west: float,
    north: float,
    east: float,
    skip: int,
    limit: int,
    condominium_id: int,
    neighborhood_id: int,
    city_id: int,
    state_id: int,
    price_min: float,
    price_max: float,
    area_min: float,
    area_max: float,
    only_condos: bool,
    except_condos: bool,
    complete_address: bool,
):
    order_by_clause = f"ORDER BY l.weight ASC"

    # Build the SQL query
    sql_select = """
    select l.lot_id,
       l.title,
       l.link,
       l.condominium_fee,
       c.condominium_id,
       n.neighborhood_id,
       l.viva_real_code,
       l.processed,
       l.latitude,
       l.longitude,
       l.description,
       l.weight,
       s.street_name           as street,
       la.number,
       la.complement,
       la.postal_code,
       c.condominium_name,
       n.neighborhood_name     as neighborhood,
       ci.city_name,
       st.state_name,
       st.state_acr,
       co.country_name,
       stat.lot_status_name,
       lp.price                as lot_price,
       lar.area                as lot_area,
       CASE 
                    WHEN la.number = 'N/A' THEN 'N'
                    ELSE 'Y'
                END AS complete_address,
       CONCAT(s.street_name, ', ', la.number, ', ', n.neighborhood_name, ', ', ci.city_name, ', ', st.state_name, ', ',
              co.country_name) AS lot_address,
       ARRAY [
           'https://storage.yandexcloud.net/apartment-images/2.jpg',
           'https://storage.yandexcloud.net/apartment-images/2.jpg',
           'https://storage.yandexcloud.net/apartment-images/2.jpg',
           'https://storage.yandexcloud.net/apartment-images/2.jpg'
           ]                   AS lot_images,
       5                       as rating
from properties.lots l
    """

    sql_joins = """
    join properties.lot_addresses la on l.lot_id = la.lot_id
         join global.addresses a on la.address_id = a.address_id
         join global.street s on a.street_id = s.street_id
         join global.neighborhoods n on a.neighborhood_id = n.neighborhood_id
         join global.cities ci on n.city_id = ci.city_id
         join global.states st on ci.state_id = st.state_id
         join global.countries co on st.country_id = co.country_id
         join properties.lot_status_history ls ON l.lot_status_history_id = ls.lot_status_history_id
         join properties.lot_status stat on ls.lot_status_id = stat.lot_status_id
         join properties.lot_price_history lp ON l.lot_price_history_id = lp.lot_price_history_id
         join properties.lot_area_history lar ON l.lot_area_history_id = lar.lot_area_history_id
    """

    # Only add region join if needed
    if only_condos:
        sql_joins += "join global.condominiums c on la.condominium_id = c.condominium_id\n"
    else:
        sql_joins += "left join global.condominiums c on la.condominium_id = c.condominium_id\n"

    # Conditionally add reference joins
    params_sql = {}

    # Start building the WHERE clause
    sql_where = f"WHERE ls.lot_status_id = {LOT_STATUS_ID_DISPONIVEL}\n"

    if except_condos:
        sql_where += "AND c.condominium_id IS NULL\n"

    if complete_address:
        sql_where += "AND la.number != 'N/A'\n"

    # Add filters to the list
    filter_conditions = [
        (
            price_min,
            "lp.price >= :price_min",
            "price_min",
        ),
        (
            price_max,
            "lp.price <= :price_max",
            "price_max",
        ),
        (
            area_min,
            "lar.area >= :area_min",
            "area_min",
        ),
        (
            area_max,
            "lar.area <= :area_max",
            "area_max",
        ),
        (
            condominium_id,
            "c.condominium_id = :condominium_id",
            "condominium_id",
        ),
        (city_id, "ci.city_id = :city_id", "city_id"),
        (state_id, "st.state_id = :state_id", "state_id"),
        (
            neighborhood_id,
            "n.neighborhood_id = :neighborhood_id",
            "neighborhood_id",
        ),
    ]

    # Loop through filter conditions
    for value, condition, param_name in filter_conditions:
        if value is not None:
            sql_where += f" AND {condition}"
            params_sql[param_name] = value

    # Handle BETWEEN conditions for latitude and longitude if not all zero
    if not (north == 0 and south == 0 and west == 0 and east == 0):
        between_conditions = [
            (
                (south, north),
                "l.latitude BETWEEN :south AND :north",
                ["south", "north"],
            ),
            (
                (west, east),
                "l.longitude BETWEEN :west AND :east",
                ["west", "east"],
            ),
        ]

        for (start, end), condition, param_names in between_conditions:
            if start is not None and end is not None:
                sql_where += f" AND {condition}"
                params_sql[param_names[0]] = start
                params_sql[param_names[1]] = end

    # Assemble the final SQL query
    sql_query = f"""
    {sql_select}
    {sql_joins}
    {sql_where}
    {order_by_clause}
    LIMIT :limit OFFSET :offset
    """
    params_sql["limit"] = limit
    params_sql["offset"] = skip * 12

    # Execute the query
    result = db.execute(text(sql_query), params_sql)
    lot_results = result.fetchall()

    # New query to get the total count
    sql_count_query = f"""
    SELECT COUNT(*) AS total_count
    FROM properties.lots l
    {sql_joins}
    {sql_where}
    """
    total_count_result = db.execute(text(sql_count_query), params_sql).scalar()

    # Build the meta object
    page = skip + 1

    return {
        "lot_list": [dict(lot) for lot in lot_results],
        "meta": {
            "total_count": total_count_result,
            "per_page": 12,
            "page": page,
            "returned_count": len(lot_results),
        },
    }


def get_lots_histogram(
    data: str,
    params: dict,
    db: Session,
    max_price_groups=50,
    max_area_groups=50,
):
    # Fetch all prices and areas with existing WHERE conditions
    price_query = f"""
    SELECT lp.price
    FROM properties.lots l
            join properties.lot_addresses la on l.lot_id = la.lot_id
            join global.addresses a on la.address_id = a.address_id
            join global.street s on a.street_id = s.street_id
            join global.neighborhoods n on a.neighborhood_id = n.neighborhood_id
            join global.cities ci on n.city_id = ci.city_id
            join global.states st on ci.state_id = st.state_id
            join global.countries co on st.country_id = co.country_id
            join properties.lot_status_history ls ON l.lot_status_history_id = ls.lot_status_history_id
            join properties.lot_status stat on ls.lot_status_id = stat.lot_status_id
            join properties.lot_price_history lp ON l.lot_price_history_id = lp.lot_price_history_id
            join properties.lot_area_history lar ON l.lot_area_history_id = lar.lot_area_history_id
            {data['joins']}
    WHERE stat.lot_status_id = {LOT_STATUS_ID_DISPONIVEL}
    AND lp.price IS NOT NULL
    AND l.latitude IS NOT NULL AND l.longitude IS NOT NULL
    {data['where_conditions']}
    """
    area_query = f"""
    SELECT lar.area
    FROM properties.lots l
            join properties.lot_addresses la on l.lot_id = la.lot_id
            join global.addresses a on la.address_id = a.address_id
            join global.street s on a.street_id = s.street_id
            join global.neighborhoods n on a.neighborhood_id = n.neighborhood_id
            join global.cities ci on n.city_id = ci.city_id
            join global.states st on ci.state_id = st.state_id
            join global.countries co on st.country_id = co.country_id
            join properties.lot_status_history ls ON l.lot_status_history_id = ls.lot_status_history_id
            join properties.lot_status stat on ls.lot_status_id = stat.lot_status_id
            join properties.lot_price_history lp ON l.lot_price_history_id = lp.lot_price_history_id
            join properties.lot_area_history lar ON l.lot_area_history_id = lar.lot_area_history_id
            {data['joins']}
    WHERE stat.lot_status_id = {LOT_STATUS_ID_DISPONIVEL}
    AND lar.area IS NOT NULL
    AND l.latitude IS NOT NULL AND l.longitude IS NOT NULL
    {data['where_conditions']}
    """

    prices = [
        row[0] for row in db.execute(text(price_query), params).fetchall()
    ]
    areas = [row[0] for row in db.execute(text(area_query), params).fetchall()]

    # Check if either prices or areas is empty
    if not prices or not areas:
        return {
            "price_groups": [],
            "area_groups": [],
            "matrix": [],
        }

    # Remove outliers
    def remove_outliers(data):
        data = [float(x) for x in data]
        Q1 = np.percentile(data, 25)
        Q3 = np.percentile(data, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return [x for x in data if lower_bound <= x <= upper_bound]

    filtered_prices = remove_outliers(prices)
    filtered_areas = remove_outliers(areas)

    # Calculate the range for prices and areas
    price_min, price_max = min(filtered_prices), max(filtered_prices)
    area_min, area_max = min(filtered_areas), max(filtered_areas)

    # Create price and area groups
    price_groups = np.linspace(price_min, price_max, max_price_groups + 1)
    area_groups = np.linspace(area_min, area_max, max_area_groups + 1)

    # Round the groups
    price_groups = np.round(price_groups / 10000) * 10000
    area_groups = np.round(area_groups / 10) * 10

    # Convert to list
    price_groups = price_groups.tolist()
    area_groups = area_groups.tolist()

    # Initialize the matrix
    matrix = np.zeros((max_price_groups, max_area_groups)).tolist()

    # Populate the matrix
    for price, area in zip(filtered_prices, filtered_areas):
        price_idx = np.searchsorted(price_groups, price, side="right") - 1
        area_idx = np.searchsorted(area_groups, area, side="right") - 1
        if (
            0 <= price_idx < max_price_groups
            and 0 <= area_idx < max_area_groups
        ):
            matrix[price_idx][area_idx] += 1

    return {
        "price_groups": price_groups[:-1],  # Exclude the last edge
        "area_groups": area_groups[:-1],  # Exclude the last edge
        "matrix": matrix,
    }


def get_lot_lat_lon(db: Session, lot_id: int):
    sql_query = """
    SELECT latitude, longitude FROM properties.lots 
    WHERE lot_id = :lot_id
    """
    return db.execute(text(sql_query), {"lot_id": lot_id}).fetchone()


def get_lot_region_lat_lon(db: Session, lot_id: int):
    sql_query = """
    SELECT 
        n.latitude as neighborhood_lat, 
        n.longitude as neighborhood_lon, 
	    c.latitude as condominium_lat, 
        c.longitude as condominium_lon 
    FROM properties.lots l 
    JOIN properties.lot_addresses la on l.lot_id = la.lot_id
    JOIN global.addresses a on la.address_id = a.address_id
    JOIN properties.lot_status_history ls ON l.lot_status_history_id = ls.lot_status_history_id
    LEFT JOIN global.neighborhoods n on a.neighborhood_id = n.neighborhood_id
    LEFT JOIN global.condominiums c on la.condominium_id = c.condominium_id
    WHERE l.lot_id = :lot_id
    AND ls.lot_status_id = :lot_status_id
    """
    return db.execute(
        text(sql_query),
        {"lot_id": lot_id, "lot_status_id": LOT_STATUS_ID_DISPONIVEL},
    ).fetchone()
