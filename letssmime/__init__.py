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

def generate_private_key(args, datastore):
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    return key_pem

def send_application(args, datastore):
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
    return args.revocation_password

def ask_for_collection_password(args, datastore):
    collection_password = input('Collection password: ').strip()
    return collection_password

def retrieve_certificate_chain(args, datastore):
    collection_password = datastore['collection_password.txt'].decode('utf-8')
    certificate = comodo.retrieve_certificate_chain(collection_password)
    return certificate

def create_pkcs12_bundle(args, datastore):
    pkcs12 = subprocess.check_output(['openssl', 'pkcs12', '-export',
        '-out', '-',
        '-inkey', datastore.path('private_key.pem'),
        '-in', datastore.path('certificate_chain.pem'),
        '-passout', 'pass:',
    ])
    return pkcs12

def main():
    steps = [
        ('private_key.pem', generate_private_key, 'Generating private key...'),
        ('revocation_password.txt', send_application, 'Sending application to Comodo...'),
        ('collection_password.txt', ask_for_collection_password, 'An email has been sent to your inbox containing a "collection password".'),
        ('certificate_chain.pem', retrieve_certificate_chain, 'Retrieving certificate chain from Comodo...'),
        ('certificate_key_bundle.p12', create_pkcs12_bundle, 'Creating PKCS12 bundle...'),
    ]
    try:
        args = get_args()
        datastore = DataStore(args.email_address)
        for desired_file, generating_func, status_message in steps:
            if desired_file not in datastore:
                print(status_message)
                datastore[desired_file] = generating_func(args, datastore)
        print('Done! Your files are located at', datastore.storage_path)
    except Exception as ex:
        print()
        print('Oops, something bad happened:')
        traceback.print_exc()
        print()
    finally:
        if sys.stdin.isatty() and sys.stdout.isatty():
            print('Press Enter to exit')
            input()

