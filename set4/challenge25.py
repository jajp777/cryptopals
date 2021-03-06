"""
Break "random access read/write" AES CTR
----------------------------------------

Back to CTR. Encrypt the recovered plaintext from this file (the ECB exercise)
under CTR with a random key (for this exercise the key should be unknown to
you, but hold on to it).

Now, write the code that allows you to "seek" into the ciphertext, decrypt, and
re-encrypt with different plaintext. Expose this as a function, like,
"edit(ciphertext, key, offet, newtext)".

Imagine the "edit" function was exposed to attackers by means of an API call
that didn't reveal the key or the original plaintext; the attacker has the
ciphertext and controls the offset and "new text".

Recover the original plaintext.

Food for thought.
A folkloric supposed benefit of CTR mode is the ability to easily
"seek forward" into the ciphertext; to access byte N of the ciphertext, all you
need to be able to do is generate byte N of the keystream. Imagine if you'd
relied on that advice to, say, encrypt a disk.
"""

"""
Relevant article: http://en.wikipedia.org/wiki/Disk_encryption_theory
In particular:
    "The third property is generally non-controversial. However, it indirectly
     prohibits the use of stream ciphers, since stream ciphers require, for
     their security, that the same initial state not be used twice (which would
     be the case if a sector is updated with different data)"
The third property being:
    "[assume an adversary] can modify unused sectors on the disk and then
     request their decryption."
"""

import binascii
import random
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def b642hex(s):
    """
    FROM: set1/challenge6
    """
    return binascii.hexlify(binascii.a2b_base64(s))

def xorstr(s1, s2):
    """
    FROM: set2/challenge10
    """

    def xor(c1, c2):
        return chr(ord(c1) ^ ord(c2))

    return ''.join([xor(s1[i], s2[i]) for i in range(len(s1))])

def rand_bytes(strlen):
    """
    FROM: set2/challenge11
    """
    return ''.join(map(chr,
                       [random.randint(0, 255) for _ in range(strlen)]))

def pkcs7_pad(s, length):
    """
    FROM: set2/challenge9
    """

    pad = length - len(s) % length
    return s + chr(pad) * pad

def aes_ecb_decrypt(k, ct):
    cipher = Cipher(algorithms.AES('YELLOW SUBMARINE'), modes.ECB(),
                    backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ct) + decryptor.finalize()

class SessionOracle:

    __BLOCKSIZE = 16

    def __init__(self):
        self.__key = rand_bytes(self.__BLOCKSIZE)
        self.__nonce = rand_bytes(self.__BLOCKSIZE)
        self.__cipher = Cipher(algorithms.AES(self.__key),
                               modes.CTR(self.__nonce),
                               backend=default_backend())

    def encrypt(self, pt):
        encryptor = self.__cipher.encryptor()
        return encryptor.update(pt) + encryptor.finalize()

    def __decrypt(self, ct):
        decryptor = self.__cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()

    def edit(self, ct, offset, newtext):
        """
        Changes the underlying PT from an input CT at offset @offset to the
        string @newtext. Returns the new corresponding CT.

        @param ct [str]: Input CT string
        @param offset [int]: Index to insert @newtext
        @param newtext [str]: New text to insert
        @returns [str]: Newly encrypted CT
        """
        pt = self.__decrypt(ct)
        ptnew = pt[:offset] + newtext + pt[offset+len(newtext):] # Splice
        return self.encrypt(ptnew)

def decrypt(oracle, ct):
    """
    Since C XOR P = E_k(keystream), we have C XOR P = C' XOR P'. Thus, for the
    original CT C, an edited PT P', and the new CT C', the original PT
    P = C XOR P' XOR C'.

    @param oracle [SessionOracle]: Object providing the edit() function
    @param ct [str]: Input CT
    @returns [str]: Corresponding PT
    """

    new_pt = 'A'*len(ct)
    return xorstr(xorstr(ct, new_pt), oracle.edit(ct, 0, new_pt))

if __name__=='__main__':
    with open('challenge25.txt', 'r') as f:
        input_ct = b642hex(''.join([line.strip() for line in f])).decode('hex')
        input_key = 'YELLOW SUBMARINE'
        input_pt = aes_ecb_decrypt(input_key, input_ct)
    oracle = SessionOracle()
    ct = oracle.encrypt(input_pt)
    print decrypt(oracle, ct)
