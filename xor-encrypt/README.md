This script allows for the encryption and decryption of text using the XOR cipher method.

# Usage
## Encrypting text
```sh
python3 ./script.py "text_to_encrypt" "key" -v
```

## Decrypting text
```sh
python3 ./script.py "encrypted_text_in_hex" "key" -v --decrypt
```

where:
- `text_to_encrypt` is the plain text that you want to encrypt.
- `key` is the key used for encryption or decryption. The key is repeated if it is shorter than the text.
- `encrypted_text_in_hex` is the encrypted text in hexadecimal form that needs to be decrypted.
- `-v` or `--verbose` (optional) flag to enable verbose output.
- `-d` or `--decrypt` flag to indicate that the script should perform decryption on the provided hex input.
