# decode_denm.py
import sys
import asn1tools
from binascii import unhexlify

# Compile ASN.1 file
denm_spec = asn1tools.compile_files('DENM.asn', 'uper')

# Read hex string or raw bytes
input_hex = sys.argv[1]

# If you already have raw bytes, skip unhexlify
payload = unhexlify(input_hex) if isinstance(input_hex, str) else input_hex

try:
    decoded = denm_spec.decode('DENM-message', payload)
    import json
    print(json.dumps(decoded, indent=2))
except Exception as e:
    print("Failed to decode DENM message:", e)

