#!/usr/bin/env python
# coding: utf-8


# Import libraries required to find pyspark installations on jupyter notebook
import findspark
findspark.init()
findspark.find()
import pyspark

# Import the required pyspark libraries that will help us explode the list of checkin dates for each business 
# into individual rows 
from pyspark.sql.functions import col, split
from pyspark.sql.functions import explode


# Import SparkSession from Pyspark
from pyspark.sql import SparkSession

# Create spark object with the necessary configuration
spark = SparkSession.builder .appName('EDA') .master('local') .enableHiveSupport() .getOrCreate()


# Read all the input files (stored on HDFS in JSON format) and create a spark dataframe on top of it
review = spark.read.json('hdfs://hadoop102:8020/yelp_data/review.json')

business = spark.read.json('hdfs://hadoop102:8020/yelp_data/business.json')
checkin = spark.read.json('hdfs://hadoop102:8020/yelp_data/checkin.json')


# create a temporary view on top of each dataframe for querying using Spark SQL
review.createOrReplaceTempView("review")
business.createOrReplaceTempView("business")
checkin.createOrReplaceTempView("checkin")


# Since there are thousands of categories, we will focus our analysis only on categories such as restaurant, pizza & sandwich.
business_subset = spark.sql("select b.*, row_number() over(partition by b.state order by b.review_count desc) as rnk from business b where (lower(categories) like '%restaurant%' or lower(categories) like '%pizza%' or lower(categories) like '%sandwich%')")

business_subset.createOrReplaceTempView("business_subset")


# Join reviews with subset of businesses to get it's required details.
business_reviews=spark.sql("select r.business_id, r.review_id, r.date, r.useful, r.stars, b.city, b.state, b.latitude, b.longitude, b.name, b.postal_code from review r inner join (select * from business_subset b where rnk<=50) b on r.business_id=b.business_id")


# Split the string column on the basis of comma to create a list of dates
checkin_date_list=checkin.select(col("business_id"), split(col("date"), ",\s*").alias("date"))

# Converting the array of dates into individual rows
checkin_explode=checkin_date_list.withColumn("date", explode(checkin_date_list.date))

# Create a temporary view for querying data in Spark SQL
checkin_explode.createOrReplaceTempView("checkin_explode")

# Filter data for subset of categories and locations as we did in above steps
checkin_explode_subset=spark.sql("select c.business_id, c.date from checkin_explode c inner join (select * from business_subset b where rnk<=50) b on c.business_id=b.business_id")


# Write spark datframe to HDFS
#Chekins transformation was done in Pig
checkin_explode_subset.write.csv('/yelp_data/checkins_by_date_by_business')
business_reviews.write.csv('/yelp_data/business_reviews')

