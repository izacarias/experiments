#!/usr/bin/env python3
import os
import csv
import argparse
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Dump all data from InfluxDB bucket 'dtn' to CSV.")
    parser.add_argument("--output-file", "-o", default="export.csv", help="Name of the output CSV file")
    args = parser.parse_args()

    url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    token = os.getenv('INFLUXDB_TOKEN')
    org = os.getenv('INFLUXDB_ORG')
    bucket = os.getenv('INFLUXDB_BUCKET', 'dtn')

    print(f"Exporting data from InfluxDB")
    print(f"URL: {url}")
    print(f"Org: {org}")
    print(f"Bucket: {bucket}")

    with InfluxDBClient(url=url, token=token, org=org) as client:
        query_str = f'from(bucket: "{bucket}") |> range(start: 0)'
        tables = client.query_api().query(query_str, org=org)

        # Collect all column names
        columns = set()
        for table in tables:
            for record in table.records:
                columns.update(record.values.keys())
        columns = sorted(columns)

        with open(args.output_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            for table in tables:
                for record in table.records:
                    writer.writerow(record.values)

if __name__ == "__main__":
    main()