######################################################
#   Export all data from Influx
######################################################
# Set the data version
# INFLUXDB_BUCKET=dtn05 python3 ./tools/influx-exporter.py -o nwloss-05-v3.csv
# INFLUXDB_BUCKET=dtn10 python3 ./tools/influx-exporter.py -o nwloss-10-v3.csv
# INFLUXDB_BUCKET=dtn15 python3 ./tools/influx-exporter.py -o nwloss-15-v3.csv
# INFLUXDB_BUCKET=dtn20 python3 ./tools/influx-exporter.py -o nwloss-20-v3.csv
INFLUXDB_BUCKET=dtn25 python3 ./tools/influx-exporter.py -o nwloss-25-v4.csv
INFLUXDB_BUCKET=dtn30 python3 ./tools/influx-exporter.py -o nwloss-30-v4.csv
INFLUXDB_BUCKET=dtn35 python3 ./tools/influx-exporter.py -o nwloss-35-v4.csv
INFLUXDB_BUCKET=dtn40 python3 ./tools/influx-exporter.py -o nwloss-40-v4.csv
