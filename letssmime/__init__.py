import argparse
import os
import random
import string
import subprocess
import sys
import traceback

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import requests

from . import spkac, comodo
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

def generate_private_key(datastore):
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

def send_application(datastore, args):
    private_key = serialization.load_pem_private_key(
        datastore['private_key.pem'],
        password=None,
        backend=default_backend()
    )
    comodo.send_application(
        args.first_name,
        args.last_name,
        args.email_address,
        args.country,
        spkac.create_spkac(private_key),
        args.revocation_password
    )
    datastore['revocation_password.txt'] = args.revocation_password

def ask_for_collection_password(datastore):
    collection_password = input('Collection password: ').strip()
    datastore['collection_password.txt'] = collection_password

def retrieve_certificate_chain(datastore):
    collection_password = datastore['collection_password.txt'].decode('utf-8')
    certificate = comodo.retrieve_certificate_chain(collection_password)
    datastore['certificate_chain.pem'] = certificate

def create_pkcs12_bundle(datastore):
    pkcs12 = subprocess.check_output(['openssl', 'pkcs12', '-export',
        '-out', '-',
        '-inkey', datastore.path('private_key.pem'),
        '-in', datastore.path('certificate_chain.pem'),
        '-passout', 'pass:',
    ])
    datastore['certificate_key_bundle.p12'] = pkcs12

def run_letssmime():
    args = get_args()
    datastore = DataStore(args.email_address)

    if 'private_key.pem' not in datastore:
        print('Generating private key...')
        generate_private_key(datastore)

    if 'revocation_password.txt' not in datastore:
        print('Sending application to Comodo...')
        send_application(datastore, args)

    if 'collection_password.txt' not in datastore:
        print('An email has been sent to', args.email_address, 'containing a "collection password".')
        ask_for_collection_password(datastore)

    if 'certificate_chain.pem' not in datastore:
        print('Retrieving certificate chain...')
        retrieve_certificate_chain(datastore)

    if 'certificate_key_bundle.p12' not in datastore:
        print('Creating PKCS12 bundle...')
        create_pkcs12_bundle(datastore)

    print('Done! Your files are in', datastore.storage_path)

def main():
    try:
        run_letssmime()
    except Exception as ex:
        print()
        print('Oops, something bad happened:')
        traceback.print_exc()
        print()
    finally:
        if sys.stdin.isatty() and sys.stdout.isatty():
            input('Press Enter to exit')

