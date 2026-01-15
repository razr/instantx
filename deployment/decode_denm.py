# decode_denm_folder.py
import sys
import os
import asn1tools
from binascii import unhexlify
import json

# Path to your ASN.1 folder
ASN_FOLDER = "eventPublisher/asn"

# Collect all .asn files in the folder
asn_files = [os.path.join(ASN_FOLDER, f) for f in os.listdir(ASN_FOLDER) if f.endswith(".asn")]

if not asn_files:
    print("No ASN.1 files found in 'asn' folder")
    sys.exit(1)

# Compile all ASN.1 files into one spec
try:
    spec = asn1tools.compile_files(asn_files, codec='uper', any_defined_by_choices=None, encoding='utf-8', numeric_enums=False)
except Exception as e:
    print("Failed to compile ASN.1 files:", e)
    sys.exit(1)

# Read input hex string from argument
if len(sys.argv) < 2:
    print("Usage: python decode_denm_folder.py <hex_string>")
    sys.exit(1)

input_hex = sys.argv[1]

# Convert hex to bytes
try:
    payload = unhexlify(input_hex)
except Exception as e:
    print("Failed to convert input to bytes:", e)
    sys.exit(1)

# Decode the message
try:
    decoded = spec.decode('DENM', payload)
    print(json.dumps(decoded, indent=2))
except Exception as e:
    print("Failed to decode DENM message:", e)

