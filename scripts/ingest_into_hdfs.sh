# create directory to store the input files
hadoop fs -mkdir /yelp_data

# Import input files in HDFS
hadoop fs -put review.json /yelp_data/
hadoop fs -put business.json /yelp_data/
hadoop fs -put checkin.json /yelp_data/
