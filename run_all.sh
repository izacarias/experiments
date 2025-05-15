# Run all experiments with link loss probability
sudo INFLUXDB_BUCKET=dtn05 LINK_LOSS=0.5 ./network.py
sudo INFLUXDB_BUCKET=dtn10 LINK_LOSS=1.0 ./network.py
sudo INFLUXDB_BUCKET=dtn15 LINK_LOSS=1.5 ./network.py
sudo INFLUXDB_BUCKET=dtn20 LINK_LOSS=2.0 ./network.py
sudo INFLUXDB_BUCKET=dtn25 LINK_LOSS=2.5 ./network.py
sudo INFLUXDB_BUCKET=dtn30 LINK_LOSS=3.0 ./network.py
sudo INFLUXDB_BUCKET=dtn35 LINK_LOSS=3.5 ./network.py
sudo INFLUXDB_BUCKET=dtn40 LINK_LOSS=4.0 ./network.py