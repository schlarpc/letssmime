# Let's S/MIME

Automatically gets S/MIME certificates signed by Comodo. I really just wanted this for use with Mumble, but I guess you can use it for email too. Vaguely inspired by the ease of use of Let's Encrypt.

Requires the `openssl` tool for creating the PKCS12 bundle at the end, which makes me sad. I just can't bring myself to do more ASN.1 manipulation right now. There's work in progress to get the needed stuff added to `cryptography`, which would make it much easier: https://github.com/pyca/cryptography/issues/2860

Run it with `python3 -m letssmime`.
