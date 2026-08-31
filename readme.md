
# Pipeline de ETL y Limpieza de Datos de Ventas

Este proyecto se realizo un proceso de extracción, transformación y carga (ETL) sobre un conjunto de datos de ventas en Python (Pandas/SQLAlchemy) y crea un modelo de datos tipo copo de nieve en **PostgreSQL**.

---

## Estructura del Proyecto

```Python
.
├── docker-compose.yml       # Configuración para levantar PostgreSQL en un contenedor
├── exercise.py              # Script principal de Python (ETL y carga a la BD)
├── ventas_2trimestres_2026.csv # Archivo CSV con los datos de origen
├── .env                     # Variables de entorno (credenciales)
├── requirements.txt         # Librerías de Python necesarias
└── README.md                # Documentación del proyecto
```

**Variables de entorno**

Para conectarte a la base de datos utilice este formato: 

DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ventas_db

El script limpia los textos (quita duplicados por minúsculas, mayúsculas o tildes en categorías, ciudades y canales), calcula los montos de descuento/totales y genera la siguiente estructura relacional:

### Tabla de Hechos (Fact Table)

* **`fact_ventas`** : Registro principal de ventas.
* `order_id` *(Primary Key)*
* `order_date`
* `customer_id` *(FK -> dim_customer)*
* `product_id` *(FK -> dim_products)*
* `category_id` *(FK -> dim_category)*
* `region_id` *(FK -> dim_region)*
* `payment_method_id` *(FK -> dim_payment_method)*
* `sales_channel_id` *(FK -> dim_saleschannel)*
* `quantity`
* `unit_price`
* `total_amount`
* `discount_pct`
* `discount_amount`

### Tablas de Dimensión (Dimensions)

* **`dim_customer`** : `customer_id`  *(PK)* , `customer_name`
* **`dim_category`** : `category_id`  *(PK)* , `category_name`
* **`dim_products`** : `product_id`  *(PK)* , `product_name`, `category_id` *(FK)*
* **`dim_region`** : `region_id`  *(PK)* , `region`
* **`dim_saleschannel`** : `sales_channel_id`  *(PK)* , `sales_channel`
* **`dim_payment_method`** : `payment_method_id`  *(PK)* , `payment_method`



**Instruciones de ejecucion**

Para levantar la base de datos PostgreSQL usando el archivo `docker-compose.yml`, ejecuta en tu terminal:

docker-compose up -d


**TechNova Retail**

TechNova es una tienda de tecnología y accesorios que vende en Colombia por 3 canales (Online, Marketplace, Tienda Física), en varias ciudades, con un catálogo de 10 productos en 5 categorías (Audio, Electrónica, Hogar Inteligente, Cómputo, Accesorios).

El problema de negocio real que enfrenta cualquier retailer como este: factura, pero no sabe si crece de forma sana. Puede estar vendiendo más unidades pero con más descuento (perdiendo margen), concentrado en pocos clientes (riesgo de dependencia), o creciendo solo por un canal mientras los otros se estancan. Ahí es donde entran los datos.

### Preguntas de Negocio a Resolver (Objetivos Analíticos)

Para garantizar un crecimiento sano y aportar valor gerencial, se plantea el análisis de Power BI con las siguientes preguntas claves: 

* **Pregunta de negocio:** ¿Cuánto dinero real nos queda libre después de restar las devoluciones cada mes?
* **Tipo de gráfico:** Gráfico de KPI (*Ventas netas y ventas Netas Mes Anterior*).
* **¿Por qué este gráfico?:** Permite ver la evolución en el tiempo y comparar el desempeño actual frente al mes anterior o la meta establecida.
* **Hallazgos:**
  * Ventas netas alcanzadas: **909,60 mil**.

---

## 2. Impacto de Descuentos en Ventas

* **Pregunta de negocio:** ¿Otorgar mayores porcentajes de descuento realmente impulsa un mayor volumen de ventas?
* **Tipo de gráfico:** Gráfico Combinado (*Relación de descuentos vs ventas*).
* **¿Por qué este gráfico?:** Relaciona dos datos diferentes en una misma línea de tiempo: el dinero ganado (barras) y el nivel de descuento (línea).
* **Hallazgos:**
  * Dar más descuento no asegura más ventas.
  * **Febrero** tuvo el mayor descuento, pero la venta fue menor que en meses siguientes.
  * **Junio** logró las ventas más altas (más de 6 mill.) con uno de los descuentos más bajos.

---

## 3. Distribución por Canal de Venta

* **Pregunta de negocio:** De los 3 canales (Online, Tienda Física, Marketplace), ¿cuál concentra el mayor porcentaje de ventas?
* **Tipo de gráfico:** Gráfico de Anillo (*Ventas totales por canal*).
* **¿Por qué este gráfico?:** Muestra de forma rápida cómo se reparte el 100% de los ingresos entre pocos canales.
* **Hallazgos:**
  * Total facturado entre todos los canales: **29,27 millones**.
  * **Online:** Lidera con el **45,29%** del total.
  * **Tienda Física:** Ocupa el segundo lugar con **33,87%**.
  * **Marketplace:** Representa el **20,84%**.

---

## 4. Análisis de Productos (Ticket Alto vs Frecuencia)

* **Pregunta de negocio:** ¿Qué productos tienen el mayor valor por compra (ticket promedio) pero pocas transacciones, y cuál es su aporte al total?
* **Tipo de gráfico:** Gráfico de Dispersión / Burbujas (*Total de Transacciones, ticket promedio y ventas netas*) junto a Barras (*Productos más vendidos*).
* **¿Por qué este gráfico?:** El gráfico de burbujas evalúa 3 variables juntas: número de ventas (eje X), ticket promedio (eje Y) y volumen de dinero (tamaño de la burbuja).
* **Hallazgos:**
  * El **Smartwatch Fit 3** es el producto estrella con el ticket promedio más alto (cerca de 0,5 mill.) y aporta casi 8 millones a las ventas totales.
  * Mantiene ventas altas en dinero a pesar de no ser el producto con más transacciones.

---

## 5. Ventas por Región y Canal

* **Pregunta de negocio:** ¿Cuál ciudad o región genera mayor volumen de ventas y cómo se reparten los canales ahí?
* **Tipo de gráfico:** Mapa de Burbujas / Tartas (*Ventas totales por región y canales*).
* **¿Por qué este gráfico?:** Muestra la ubicación geográfica real y la mezcla de canales que domina en cada zona.
* **Hallazgos:**
  * **Bogotá** y la zona central concentran la mayor cantidad de ventas.
  * En las ciudades principales (Bogotá, Cali y zona Costa), las compras se dividen principalmente entre el canal **Online** y la **Tienda Física**, dejando a **Marketplace** en último lugar.
