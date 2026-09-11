"""Run outside Vercel: PySpark computes hourly means with Spark SQL."""
import json
from pathlib import Path
from pyspark.sql import SparkSession

ROOT = Path(__file__).resolve().parents[1]
spark = SparkSession.builder.appName('HoraLivre').config('spark.sql.session.timeZone','UTC').getOrCreate()
try:
    spark.read.option('header',True).csv(str(ROOT/'data/kaggle.csv')).createOrReplaceTempView('attendance')
    result = spark.sql('''
      WITH observations AS (
        SELECT pmod(dayofweek(to_timestamp(substring(date,1,19))) + 5, 7) AS weekday,
               hour(to_timestamp(substring(date,1,19))) AS hour, CAST(number_people AS DOUBLE) AS people
        FROM attendance
      ), hourly AS (
        SELECT weekday, hour, avg(people) AS mean_people, count(*) AS samples
        FROM observations WHERE weekday IS NOT NULL AND hour IS NOT NULL AND people >= 0
        GROUP BY weekday, hour
      ) SELECT weekday, hour,
        CAST(round(mean_people / greatest(max(mean_people) OVER (), 1) * 100) AS INT) AS score,
        samples FROM hourly ORDER BY weekday, hour
    ''')
    rows = [row.asDict() for row in result.collect()]
    if not rows:
        raise ValueError('Empty Spark output')
    (ROOT/'data/spark_profiles.json').write_text(json.dumps(rows),encoding='utf-8')
finally:
    spark.stop()
