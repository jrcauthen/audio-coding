
def uniform_encode(number: int, num_bits: int, max_range: int, quant_type='midtread') -> str:
    
    '''
    encode a signal using uniform bin sizes.
    
    ---
    
    INPUTS:
        
        number: number to be encoded
        
        num_bits: number of bits used to encode the number
        
        max_range: maximum value onto which the number can be mapped. values higher
            than max_range will be clipped to max_range. values lower than -max_range
            will be clipped to -max_range
            
        quant_type: quantization scheme to be applied. options include 'midtread'
            and 'midrise'
        
    
    OUTPUTS:
    
        bit_string: the encoded value in bits
        code*s: the signed codeword        
    
    '''
    
    if number >= 0:
        s = 1
        s_bit = 0
    else:
        s = -1
        s_bit = 1
    if quant_type == 'midrise':
        if abs(number) >= max_range:
            code = 2**(num_bits - 1) - 1
        else:
            code = int(2**(num_bits - 1) * abs(number))
    
    else:
        if abs(number) >= max_range:
            code = 2**(num_bits-1) - 1
        else:
            code = int(((2**num_bits - 1)*abs(number) + 1)/2)
    bit_string = str(s_bit) + format(code,'b').zfill(num_bits-1)
    return bit_string, code*s



def uniform_decode(code: str, num_bits: int, quant_type='midtread') -> float:
    
    '''
    decode encoded signal using uniform bin sizes.
    
    ---
    
    INPUTS: 
        code: integer number to be decoded
        
        num_bits: length of code word in bits
        
        quant_type: quantization scheme to be applied. options are 'midtread' and 
            'midrise'
    
    OUTPUTS:
        s*number: the signed decoded code word
    '''
    
    s = 2*int(code & 2**(num_bits-1) == 0) - 1 
        
    if quant_type == 'midrise':
        number = (abs(code) + 0.5) / 2**(num_bits - 1)
    else:
        number = 2 * abs(code) / (2**num_bits-1)
    
    return s * number

    

def count_zeros(code: int, R: int) -> int:
    
    '''
    count the number of leading zeros in a code word
    
    ---
    
    INPUTS:
        code: integer number / binary code
        
        R: number of bits in the codeword
    
    OUTPUTS:
        num_zeros: number of leading zeros in code word
    '''

    if code == 0: 
        return R-1  # don't consider the sign bit
    
    num_zeros = 0
    while (1 << (R-2) & code) == 0:     # avoid the sign bit
        num_zeros += 1
        code <<= 1
    return num_zeros


def flp_encode(number: int, Rs: int, Rm: int) -> str:
    '''
    floating point midtread encoder
    at high level inputs, R ~ Rm + 1 (approximates a uniform quantizer)
    
    ---
    
    INPUTS:
        Rs/scale bits/exponent - describe the size of the quantization bins
        
        Rm/amplitude bits/mantissa - describe the size of the signal to be quantized
        
        total bits/sample R = Rs + Rm
        
    OUTPUTS:
        scale: scale bits - describe the quantization bin size
        mantissa: mantissa bits - describe the size of the signal to be encoded
    '''
    
    # first, uniformly quantize the input signal using the highest # of bits
    # for which the the floating point quantizer is comparable
    
    # scaling bits keep track of the # of leading zeros in the uniformly quantized codes
    # so that they can be stripped off the code - scale starts at 0 when there are 
    # seven leading zeros and counts up to 7 as the number of zeros decrease
    
    # mantissa bits are used to store the highest order bits in the remaining code

    
    R = 2**Rs - 1 + Rm
    encoded = uniform_encode(number, R, 1, 'midtread')
    
    # AND code and 2**(R-1) to get sign
    s = int(encoded[1]&(1 << (R-1))!=0)
    
    num_zeros = count_zeros(abs(encoded[1]),R, encoded[0])
    
    mantissa  = s << (Rm-1)
    if num_zeros < (2**Rs - 1):
        scale = 2**Rs - 1 - num_zeros     
        shift = (R - num_zeros - Rm - 1)
        mask = (2**(Rm-1) - 1) << shift
        mantissa+= (mask & abs(encoded[1])) >> shift
    
    else:
        scale = 0
        mantissa+= abs(encoded[1])
        
    
    return scale, mantissa



def flp_decode(scale: int, mantissa: int, Rs: int, Rm: int) -> float:
    
    '''
    floating point midtread decoder
    
    ---
    
    INPUTS:
        scale - number of left shifts necessary to apply to the stripped off code (scale increases
                as the number of leading zeros decreases) - scale bits describe the 
                size of the de/quantization bins
                
        mantissa - describe the size of the signal to be quantized/dequantized
        
        Rs - scale bits
        
        Rm - mantissa bits
        
    OUTPUTS:
        number: the decoded value
    
    -----
    
    1.) left-shift by number of leading zeros
    2a.) if scale is not zero, left-shift by 1 and add 1
    2b.) left-shift by Rm and add the mantissa bits
    3.) if scale > 1, left shift by 1 and add 1 - then left-shift by the length
         of the code
    4.)  get the absolute value of the code
    5.) multiply code by the sign
    6.) uniformly dequantize the code
    '''
    
    R = 2**(Rs) -1 + Rm
    s = int(mantissa&(2**(Rm-1))!=0)
    sign = 1 if s == 0 else -1 
    code = 1
    code <<= 2**Rs - 1 - scale   # 1.)
    mask = 2**(Rm-1) - 1
    
    if scale != 0:
        code = (code << 1) + 1  # 2a.)
        
    code <<= (Rm - 1)           # 2b.)
    code |= (mantissa & mask)
    
    if scale > 1:
        code = (code << 1) + 1  # 3.)
        code <<= (R-len(bin(code)[2:]))
    
    code &= (2**(R-1) - 1)      # 4.)
    code *= sign                # 5.)

    number = uniform_decode(code,R,'midtread')  # 6.)

    return number

    
x_max = 1   # maximum input range
x_min = -1  # minimum input range
input_voltage = 0.001
Rs = 3
Rm = 5
R = 8
qtype = 'midtread'

encoded = uniform_encode(input_voltage, R, x_max, qtype)
decoded = uniform_decode(encoded[1], R, qtype)

scale, mantissa = flp_encode(input_voltage, Rs, Rm, qtype)
flp_decoded = flp_decode(scale, mantissa,'midtread',Rs,Rm)