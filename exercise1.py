import os
from dotenv import load_dotenv
import pandas as pd 
import numpy as np 
from psycopg2 import OperationalError
from sqlalchemy import create_engine, text

load_dotenv()

#  Cargar archivo
df = pd.read_csv('ventas_2trimestres_2026.csv')

#  Formato de fechas
df['order_date'] = pd.to_datetime(
    df['order_date'].str.replace(r'^(\d{2})/(\d{2})/(\d{4})$', r'\3-\2-\1', regex=True),
    format='mixed',
    errors='coerce'
)

# Formato order_id
df['order_id'] = df['order_id'].astype(str)

# Rellenar clientes vacíos
df['customer_name'] = df['customer_name'].fillna('unknown customer')


# Arreglar categorías (quitar tildes y homogeneizar a un solo nombre)
df['category'] = df['category'].str.strip().replace({
    'Computación': 'Computacion',
    'computación': 'Computacion',
    'Electrónica': 'Electronica',
    'electrónica': 'Electronica',
    'electronica': 'Electronica',
    'ELECTRONICA': 'Electronica',
    'hogar inteligente': 'Hogar Inteligente',
    'audio': 'Audio',
    'accesorios': 'Accesorios'
}).str.title()

# Arreglar regiones
df['region'] = df['region'].str.strip().replace({
    'Bogotá': 'Bogota', 
    'bogotá': 'Bogota', 
    'bogota': 'Bogota',
    'Medellín': 'Medellin', 
    'medellín': 'Medellin', 
    'medellin': 'Medellin'
}).str.title()

# Arreglar canal de ventas
df['sales_channel'] = df['sales_channel'].str.strip().replace({
    'Tienda Física': 'Tienda Fisica',
    'tienda física': 'Tienda Fisica',
    'tienda fisica': 'Tienda Fisica'
}).str.title()

#  Descuentos y totales
df['discount_pct'] = df['discount_pct'].fillna(0)

calculated_total = df['quantity'] * df['unit_price'] * (1 - df['discount_pct'])
df['total_amount'] = df['total_amount'].fillna(calculated_total)
df['discount_amount'] = (df['quantity'] * df['unit_price'] * df['discount_pct'] / 100)

#  Quitar duplicados por orden

df = df.drop_duplicates(subset=['order_id'], keep='first').reset_index(drop=True)

# Conexión a PostgreSQL con variables de entorno

USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST", "localhost")  
PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print(f" Conexión exitosa a '{DB_NAME}' en {HOST}:{PORT}\n")
except OperationalError as e:
    print(f" Error de credenciales o red al conectar a PostgreSQL: {e}\n")
except Exception as e:
    print(f" Error inesperado: {e}\n")

#  Creación de Tablas de Dimensión 


Dim_customer = df[["customer_id", "customer_name"]].drop_duplicates().reset_index(drop=True)

Dim_category = df[['category']].drop_duplicates().rename(columns={'category': 'category_name'}).reset_index(drop=True)
Dim_category.insert(0, 'category_id', range(1, len(Dim_category) + 1))

Dim_products = (
    df[['product_id', 'product_name', 'category']]
    .drop_duplicates(subset=['product_id'], keep='first')
    .merge(Dim_category.rename(columns={'category_name': 'category'}), on='category', how='left')
    [['product_id', 'product_name', 'category_id']]
    .reset_index(drop=True)
)

Dim_region = df[['region']].drop_duplicates().reset_index(drop=True)
Dim_region.insert(0, 'region_id', range(1, len(Dim_region) + 1))

Dim_saleschannel = df[['sales_channel']].drop_duplicates().reset_index(drop=True)
Dim_saleschannel.insert(0, 'sales_channel_id', range(1, len(Dim_saleschannel) + 1))

Dim_payment_method = df[['payment_method']].drop_duplicates().reset_index(drop=True)
Dim_payment_method.insert(0, 'payment_method_id', range(1, len(Dim_payment_method) + 1))


# TABLA DE HECHOS 

fact_ventas = (
    df[[
        'order_id', 
        'order_date',
        'customer_id',
        'product_id',
        'payment_method',
        'region', 
        'sales_channel',
        'quantity', 
        'unit_price', 
        'total_amount', 
        'discount_pct', 
        'discount_amount'
    ]]
    .drop_duplicates()
    .merge(Dim_products[['product_id', 'category_id']], on='product_id', how='left')
    .merge(Dim_region[['region_id', 'region']], on='region', how='left')
    .merge(Dim_payment_method[['payment_method', 'payment_method_id']], on='payment_method', how='left')
    .merge(Dim_saleschannel[['sales_channel', 'sales_channel_id']], on='sales_channel', how='left')
    [[
        'order_id',
        'order_date',
        'customer_id',
        'product_id',
        'category_id',
        'region_id', 
        'payment_method_id',
        'sales_channel_id',
        'quantity',
        'unit_price', 
        'total_amount', 
        'discount_pct', 
        'discount_amount'
    ]]
    .drop_duplicates()
    .reset_index(drop=True)
)

#  Exportación de DataFrames a PostgreSQL
Dim_customer.to_sql("dim_customer", engine, if_exists="replace", index=False)
Dim_category.to_sql("dim_category", engine, if_exists="replace", index=False)
Dim_products.to_sql("dim_products", engine, if_exists="replace", index=False)
Dim_region.to_sql("dim_region", engine, if_exists="replace", index=False)
Dim_saleschannel.to_sql("dim_saleschannel", engine, if_exists="replace", index=False)
Dim_payment_method.to_sql("dim_payment_method", engine, if_exists="replace", index=False)
fact_ventas.to_sql("fact_ventas", engine, if_exists="replace", index=False)

#  Definición de Primary Keys y Foreign Keys
with engine.connect() as conn:
    # Claves Primarias (PK)
    conn.execute(text("ALTER TABLE dim_customer ADD PRIMARY KEY (customer_id);"))
    conn.execute(text("ALTER TABLE dim_category ADD PRIMARY KEY (category_id);"))
    conn.execute(text("ALTER TABLE dim_products ADD PRIMARY KEY (product_id);"))
    conn.execute(text("ALTER TABLE dim_payment_method ADD PRIMARY KEY (payment_method_id);"))
    conn.execute(text("ALTER TABLE dim_saleschannel ADD PRIMARY KEY (sales_channel_id);"))
    conn.execute(text("ALTER TABLE dim_region ADD PRIMARY KEY (region_id);"))
    conn.execute(text("ALTER TABLE fact_ventas ADD PRIMARY KEY (order_id);"))

    # Claves Foráneas (FK)
    conn.execute(
        text(
            "ALTER TABLE dim_products ADD CONSTRAINT fk_products_category "
            "FOREIGN KEY (category_id) REFERENCES dim_category(category_id);"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE fact_ventas ADD CONSTRAINT fk_ventas_customer "
            "FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id);"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE fact_ventas ADD CONSTRAINT fk_ventas_product "
            "FOREIGN KEY (product_id) REFERENCES dim_products(product_id);"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE fact_ventas ADD CONSTRAINT fk_ventas_region "
            "FOREIGN KEY (region_id) REFERENCES dim_region(region_id);"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE fact_ventas ADD CONSTRAINT fk_ventas_payment "
            "FOREIGN KEY (payment_method_id) REFERENCES dim_payment_method(payment_method_id);"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE fact_ventas ADD CONSTRAINT fk_ventas_channel "
            "FOREIGN KEY (sales_channel_id) REFERENCES dim_saleschannel(sales_channel_id);"
        )
    )
    
    conn.commit()

