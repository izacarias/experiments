import requests
from requests.auth import HTTPBasicAuth
import os
from mininet.log import debug

# Load ONOS credentials from environment variables
onos_url = os.getenv('ONOS_URL', 'http://localhost:8181')
onos_username = os.getenv('ONOS_USERNAME', 'onos')
onos_password = os.getenv('ONOS_PASSWORD', 'rocks')

onos_link_history = {}  # Historical data storage

def onos_get_links():
    """Gets links from ONOS."""
    url = '%s/onos/v1/links' % onos_url
    response = requests.get(url, auth=HTTPBasicAuth(onos_username, onos_password))
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get links from ONOS: {response.status_code} {response.text}")


def onos_get_port_stats(device_id, port_id):
    """Gets port statistics from ONOS."""
    url = "%s/onos/v1/statistics/ports/%s/%s" % (onos_url, device_id, port_id)
    response = requests.get(url, auth=HTTPBasicAuth(onos_username, onos_password))
    response.raise_for_status()
    return response.json()


def onos_get_link_usage():
    """Calculates link usage based on ONOS statistics."""
    global onos_link_history
    return_value = []
    links = onos_get_links()
    for link in links['links']:
        src_device = link['src']['device']
        src_port = link['src']['port']
        dst_device = link['dst']['device']

        # Get statistics for the source device
        src_stats = onos_get_port_stats(src_device, src_port)
        current_bytes = src_stats.get('statistics')[0].get('ports')[0].get('bytesSent')
        current_duration = src_stats.get('statistics')[0].get('ports')[0].get('durationSec')

        # Get historical data
        link_key = (src_device, src_port)
        prev_stats = onos_link_history.get(link_key, {'bytes': current_bytes, 'duration': current_duration})

        # Calculate delta values
        bytes_delta = current_bytes - prev_stats['bytes']
        duration_delta = current_duration - prev_stats['duration']

        # Calculate data rate
        datarate = (bytes_delta * 8) / duration_delta if duration_delta > 0 else 0

        # Update historical data
        onos_link_history[link_key] = {
            'bytes': current_bytes,
            'duration': current_duration
        }
        debug("Datarate for %s to %s: %d bps \n" % (src_device, dst_device, datarate))
        return_value.append((src_device, dst_device, datarate))
    return return_value