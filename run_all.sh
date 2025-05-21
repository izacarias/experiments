# Clean all Mininet Interfaces
sudo mn -c

# Run all experiments with link loss probability
# sudo INFLUXDB_BUCKET=dtn05 LINK_LOSS=0.5 ./network.py
# sudo INFLUXDB_BUCKET=dtn10 LINK_LOSS=1.0 ./network.py
# sudo INFLUXDB_BUCKET=dtn15 LINK_LOSS=1.5 ./network.py
# sudo INFLUXDB_BUCKET=dtn20 LINK_LOSS=2.0 ./network.py
sudo INFLUXDB_BUCKET=dtn25 LINK_LOSS=2.5 ./network.py
sudo INFLUXDB_BUCKET=dtn30 LINK_LOSS=3.0 ./network.py
sudo INFLUXDB_BUCKET=dtn35 LINK_LOSS=3.5 ./network.py
sudo INFLUXDB_BUCKET=dtn40 LINK_LOSS=4.0 ./network.py

######################################################
# INFLUXDB_BUCKET=dtn05 python3 ./tools/influx-exporter.py -o nwloss-05-v3.csv
# INFLUXDB_BUCKET=dtn10 python3 ./tools/influx-exporter.py -o nwloss-10-v3.csv
# INFLUXDB_BUCKET=dtn15 python3 ./tools/influx-exporter.py -o nwloss-15-v3.csv
# INFLUXDB_BUCKET=dtn20 python3 ./tools/influx-exporter.py -o nwloss-20-v3.csv
# INFLUXDB_BUCKET=dtn25 python3 ./tools/influx-exporter.py -o nwloss-25-v4.csv
# INFLUXDB_BUCKET=dtn30 python3 ./tools/influx-exporter.py -o nwloss-30-v4.csv
# INFLUXDB_BUCKET=dtn35 python3 ./tools/influx-exporter.py -o nwloss-35-v4.csv
# INFLUXDB_BUCKET=dtn40 python3 ./tools/influx-exporter.py -o nwloss-40-v4.csv
