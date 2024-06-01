import argparse
from itertools import cycle

def xor_encrypt_decrypt(data, key, is_hex=False):
    from itertools import cycle
    if is_hex:
        data = bytes.fromhex(data)

    if isinstance(data, bytes):
        return ''.join(chr(char ^ ord(k)) for char, k in zip(data, cycle(key)))
    else:
        return ''.join(chr(ord(char) ^ ord(k)) for char, k in zip(data, cycle(key)))

def main():
    parser = argparse.ArgumentParser(description='XOR Encryption/Decryption Tool')
    parser.add_argument('text', help='Text to encrypt/decrypt')
    parser.add_argument('key', help='Encryption key')
    parser.add_argument("-d", "--decrypt", dest="decrypt", action="store_true", help="Decrypt the input (input should be in hex)")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.decrypt:
        decrypted = xor_encrypt_decrypt(args.text, args.key, is_hex=True)
        if args.verbose:
            print(f"Encrypted (hex): {args.text}")
            print(f"Key: {args.key}")
            print(f"Decrypted: {decrypted}")
        else:
            print(decrypted)
    else:
        encrypted = xor_encrypt_decrypt(args.text, args.key)
        encrypted_hex = ''.join(format(ord(x), '02x') for x in encrypted)
        if args.verbose:
            print(f"Original: {args.text}")
            print(f"Key: {args.key}")
            print(f"Encrypted (hex): {encrypted_hex}")
        else:
            print(encrypted_hex)

if __name__ == '__main__':
    main()
