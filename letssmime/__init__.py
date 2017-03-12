import argparse
import os
import random
import string
import subprocess

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import requests

from .spkac import create_spkac
from .comodo import send_application, retrieve_certificate_chain
from .datastore import DataStore

def random_string(n):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(n))

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--first-name')
    parser.add_argument('--last-name')
    parser.add_argument('--email-address')
    parser.add_argument('--country', default='1224', help='Defaults to United States.')
    parser.add_argument('--revocation-password')
    return complete_args_interactive(parser.parse_args())

def complete_args_interactive(args):
    if not args.first_name:
        args.first_name = input('First name: ').strip()
    if not args.last_name:
        args.last_name = input('Last name: ').strip()
    if not args.email_address:
        args.email_address = input('Email address: ').strip()
    if not args.revocation_password:
        args.revocation_password = random_string(16)
    return args

def main():
    args = get_args()
    datastore = DataStore(args.email_address)

    if 'private_key.pem' not in datastore:
        print('Generating private key...')
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        datastore['private_key.pem'] = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

    if 'revocation_password.txt' not in datastore:
        print('Sending application to Comodo...')
        private_key = serialization.load_pem_private_key(
            datastore['private_key.pem'],
            password=None,
            backend=default_backend()
        )
        spkac = create_spkac(private_key)
        send_application(args.first_name, args.last_name, args.email_address, args.country, spkac, args.revocation_password)
        datastore['revocation_password.txt'] = args.revocation_password

    if 'collection_password.txt' not in datastore:
        print('An email has been sent to', args.email_address, 'containing a "collection password".')
        collection_password = input('Collection password: ').strip()
        datastore['collection_password.txt'] = collection_password

    if 'certificate_chain.pem' not in datastore:
        print('Retrieving certificate chain...')
        collection_password = datastore['collection_password.txt'].decode('utf-8')
        certificate = retrieve_certificate_chain(collection_password)
        datastore['certificate_chain.pem'] = certificate

    if 'certificate_key_bundle.p12' not in datastore:
        print('Creating PKCS12 bundle...')
        pkcs12 = subprocess.check_output(['openssl', 'pkcs12', '-export',
            '-out', '-',
            '-inkey', datastore.path('private_key.pem'),
            '-in', datastore.path('certificate_chain.pem'),
            '-passout', 'pass:',
        ])
        datastore['certificate_key_bundle.p12'] = pkcs12

    print('Done! Your files are in', datastore.storage_path)
