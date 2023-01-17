# -*- coding: utf-8 -*-
"""

Version number: 0.1
Date created: 01.02.2023
Author: Justin Cauthen

---

Lossy text encoder to map 7 bit ASCII characters onto only 5 bits


"""
from typing import List, Dict
from bitstring import BitArray


# get the m lowest bits from any unsigned integer
def get_m_bits(num: int, m: int) -> str:
    b = bin(num)[2:]
    assert num >= 0
    assert len(b) >= m
    return b[-m:]


# write m bits to the nth location of an array of bytes
def write_m_bits(bits: str, n: int, byte_array: bytearray) -> bytearray:
    new_byte_array = []
    bit_string = ''.join([bin(i)[2:] for i in byte_array])
    bit_string = bit_string[:n] + bits + bit_string[n+len(bits):]
    for i in range(0,len(bit_string),8):
        new_byte_array.append(int(bit_string[i:i+8],2))
    return bytearray(new_byte_array)



# def access_bit(data, num):
#     base = int(num // 8)
#     shift = int(num % 8)
#     return (int(data[base]) >> shift) & 0x1

    

codebook = {
    'a': '00000',
    'b': '00001',
    'c': '00010',
    'd': '00011',
    'e': '00100',
    'f': '00101',
    'g': '00110',
    'h': '00111',
    'i': '01000',
    'j': '01001',
    'k': '01010',
    'l': '01011',
    'm': '01100',
    'n': '01101',
    'o': '01110',
    'p': '01111',
    'q': '10000',
    'r': '10001',
    's': '10010',
    't': '10011',
    'u': '10100',
    'v': '10101',
    'w': '10110',
    'x': '10111',
    'y': '11000',
    'z': '11001',
    '?': '11010',
    '!': '11011',
    ',': '11100',
    '0': '01110',
    '1': '01011',
    '2': '10001',
    '3': '00100',
    '4': '00000',
    '5': '10010',
    '6': '00110',
    '7': '10011',
    '8': '00001',
    '9': '10000',
    'capital': '11110',
    'special': '11111'}
    
special_character_codebook = {
    '"': '00000',
    "'": '00001',
    '#': '00010',
    '$': '00011',
    "%": '00100',
    '&': '00101',
    '(': '00110',
    ')': '00111',
    '*': '01000',
    '+': '01001',
    ':': '01010',
    '-': '01011',
    ';': '01100',
    '<': '01101',
    '>': '01110',
    '@': '01111',
    '[':' 10000',
    ']': '10001',
    '^': '10010',
    '_': '10011',
    '=' : '10100',
    '{': '10101',
    '}': '10110',
    '~': '10111',
    '|': '11000',
    '/': '11001',
    '.': '11010',
    ' ': '11011',
    '\n': '11100'
    }

inverse_codebook = {v:k for (k,v) in codebook.items()}
inverse_special_character_codebook = {v:k for (k,v) in special_character_codebook.items()}


def encode_file(src: str, out:str, codebooks: List[Dict]) -> None:
    codebook = codebooks[0]
    special_character_codebook = codebooks[1]
    bitstring = ''
    with open(src, 'rb') as f:
        text = f.read()
        
        for character in text.decode('ascii'):
            if character in special_character_codebook:
                bitstring += codebook['special']
                bitstring += special_character_codebook[character]
            elif character.isupper():
                bitstring += codebook['capital']
                bitstring += codebook[character.lower()]
            else:
                bitstring += codebook[character]
        extra = 8-(len(bitstring) % 8)
        
        # filling out the bitstring to fit into bytes
        # the number of "extra" bits are returned and passed to the decoder
        # in order to ignore the "extra" bits
        if len(bitstring) % 8 != 0:
            bitstring += '0' * extra
        
    encoded_string = ''
    
    out = open(out,'wb')
    for b in range(0,len(bitstring),8):
        encoded_string += hex(int(bitstring[b:b+8],2))  # represented in hex form
        out.write(int((bitstring[b:b+8]),2).to_bytes(1, byteorder='big'))
    out.close()
    f.close()
    return extra


def decode_file(src: str, out: str, codebooks: List[Dict], extra_bits: int) -> None:
    
    inverse_codebook = codebooks[0]
    special_character_codebook = codebooks[1]
    
    special = capital = 0
    decoded_text = ''
    f = open(src, 'rb')
    encoded_text = BitArray(f.read()).bin[:-extra_bits]
    #encoded_text = ''.join([bin(i)[2:] for i in encoded_text])
    for i in range(0,len(encoded_text),5):
        byte = encoded_text[i:i+5]
        
        if byte == '11110':
            capital = 1
        elif byte == '11111':
            special = 1
        
        elif len(byte) == 5:
            if capital == 1:
                decoded_text += inverse_codebook[byte].upper()
                capital = 0
            elif special == 1:
                decoded_text += special_character_codebook[byte]
                special = 0
            else:
                decoded_text += inverse_codebook[byte]
            
    o = open(out,'wb')
    o.write(bytes(decoded_text,'ascii'))
    f.close()
    o.close()
    return (encoded_text,decoded_text)


# for text_sample.txt,
# compression ratio = 1.069
# gain of ~6.45%
extra = encode_file('text_sample.txt', 'encoded_text.txt', [codebook, special_character_codebook])
decoded_file = decode_file('encoded_text.txt','decoded_text.txt', [inverse_codebook, inverse_special_character_codebook],extra)
