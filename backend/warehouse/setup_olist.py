"""Build the Olist e-commerce database from the Kaggle CSVs in data/olist/.

    python -m backend.warehouse.setup_olist   (or: make data-olist)

Cleaning done here, so the agent sees a tidy schema:
- short table names (olist_orders_dataset.csv -> orders)
- date columns cast to TIMESTAMP
- English category names joined into products
- zip code prefixes kept as text, so leading zeros survive
"""
from pathlib import Path

import duckdb

from backend.warehouse import DATASET_PATHS

CSV_DIR = Path("data/olist")


def csv(name: str, **types: str) -> str:
    """read_csv(...) call for one file. `types` forces column types where auto-detect is wrong."""
    path = CSV_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Download the Olist dataset from Kaggle into {CSV_DIR}/.")
    type_map = ", ".join(f"'{col}': '{typ}'" for col, typ in types.items())
    return f"read_csv('{path}', header=true" + (f", types={{{type_map}}})" if types else ")")


TABLES = {
    "customers": f"""
        SELECT * FROM {csv("olist_customers_dataset", customer_zip_code_prefix="VARCHAR")}
    """,
    "sellers": f"""
        SELECT * FROM {csv("olist_sellers_dataset", seller_zip_code_prefix="VARCHAR")}
    """,
    "orders": f"""
        SELECT
            order_id, customer_id, order_status,
            CAST(order_purchase_timestamp AS TIMESTAMP)      AS order_purchase_timestamp,
            CAST(order_approved_at AS TIMESTAMP)             AS order_approved_at,
            CAST(order_delivered_carrier_date AS TIMESTAMP)  AS order_delivered_carrier_date,
            CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
            CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date
        FROM {csv("olist_orders_dataset")}
    """,
    "order_items": f"""
        SELECT
            order_id, order_item_id, product_id, seller_id,
            CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,
            price, freight_value
        FROM {csv("olist_order_items_dataset")}
    """,
    "order_payments": f"""
        SELECT * FROM {csv("olist_order_payments_dataset")}
    """,
    "order_reviews": f"""
        SELECT
            review_id, order_id, review_score, review_comment_title, review_comment_message,
            CAST(review_creation_date AS TIMESTAMP)    AS review_creation_date,
            CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp
        FROM {csv("olist_order_reviews_dataset")}
    """,
    # English category name joined in. Two categories have no translation in the
    # source file, so we fall back to the Portuguese name rather than lose them.
    # The source column names misspell "length" ("lenght"); fixed here so the LLM
    # doesn't have to guess the typo.
    "products": f"""
        SELECT
            p.product_id,
            COALESCE(t.product_category_name_english, p.product_category_name) AS product_category,
            p.product_category_name AS product_category_name_pt,
            p.product_name_lenght        AS product_name_length,
            p.product_description_lenght AS product_description_length,
            p.product_photos_qty, p.product_weight_g,
            p.product_length_cm, p.product_height_cm, p.product_width_cm
        FROM {csv("olist_products_dataset")} AS p
        LEFT JOIN {csv("product_category_name_translation")} AS t
            ON p.product_category_name = t.product_category_name
    """,
    # The raw file has ~1M rows for ~19k zip prefixes (many points per prefix).
    # Joining customers to it directly would multiply every row, so we keep one
    # row per prefix with the average coordinates and the most common city/state.
    "geolocation": f"""
        SELECT
            geolocation_zip_code_prefix AS zip_code_prefix,
            AVG(geolocation_lat)        AS lat,
            AVG(geolocation_lng)        AS lng,
            MODE(geolocation_city)      AS city,
            MODE(geolocation_state)     AS state
        FROM {csv("olist_geolocation_dataset", geolocation_zip_code_prefix="VARCHAR")}
        GROUP BY geolocation_zip_code_prefix
    """,
}


def main() -> None:
    path = Path(DATASET_PATHS["olist"])
    if path.exists():
        print(f"{path} already exists, nothing to do. Delete it to regenerate.")
        return
    conn = duckdb.connect(str(path))
    try:
        for table, select in TABLES.items():
            conn.execute(f'CREATE TABLE "{table}" AS {select}')
            count = conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            print(f"  {table:<15} {count:>9,} rows")
    except Exception:
        # Don't leave a half-built database behind; it would be skipped next run.
        conn.close()
        path.unlink(missing_ok=True)
        raise
    conn.close()
    print(f"Created {path}")


if __name__ == "__main__":
    main()
