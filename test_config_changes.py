#!/usr/bin/env python3
import re

# Test config modification
test_config = """
system.traffic_gen = MetadataTrafficGen(
    burst_size=50,
    burst_interval='1ms',
    request_latency='4us'
)
"""

params = {"burst_size": 200, "burst_interval": "2ms", "request_latency": "10us"}

# Apply regex changes
result = test_config
result = re.sub(r'burst_size=\d+', f'burst_size={params["burst_size"]}', result)
result = re.sub(r'burst_interval=["\'][^"\']+["\']', f'burst_interval=\'{params["burst_interval"]}\'', result)
result = re.sub(r'request_latency=["\'][^"\']+["\']', f'request_latency=\'{params["request_latency"]}\'', result)

print("BEFORE:")
print(test_config)
print("\nAFTER:")
print(result)
print("\n✅ Config modification works!")
