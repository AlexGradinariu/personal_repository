''' convert_dlt.py
' This Python script converts DLT files or single DLT Messages.
' It is based on pure Python, and tested with Python v. 3.6
'
' Available Functions:
' decode_dlt_message(f) - f is a Binary Stream with a single DLT Message (if
'                         f contains multiple DLT Messages, only the first is decoded
'                         (return is a dict)
' decode_dlt_buffered_reader(f) - f is a Binary Stream containing multiple DLT
'                                encoded messages (return array of dicts)
'
' Creation Date: 2021-10-13
' Last Updated: 2022-10-20
' Author: Christopher Haccius (christopher.haccius@continental-corporation.com)
' Copyright: 2021 Continental Automotive GmbH
'''

import datetime

dlt_pattern_position = 0 # global variable to store the last correct position of the DLT Pattern '44 4C 54 01'
                         # so we can jump back and continue looking for the next fit in case of corrupted messages

def bits(byte):
    ''' Convert a byte (input) into an array of 8 bits'''
    bit = format(ord(byte), '08b')
    return bit[::-1]

def convert_float(bytes_in):
    ''' convert the input of bytes into a floating point number'''
    if len(bytes_in) == 2:
        mantissa = 10
        exponent = 5
    elif len(bytes_in) == 4:
        mantissa = 23
        exponent = 8
    elif len(bytes_in) == 8:
        mantissa = 52
        exponent = 11
    elif len(bytes_in) == 16:
        mantissa = 112
        exponent = 15
    else:
        return None

    bitsequence = "".join([bits(chr(byte)) for byte in bytes_in])
    bitsequence = bitsequence[::-1] # reverse order of bits

    sign_bit = bitsequence[0]
    sign = -1 if sign_bit == 1 else 1

    exponent_bits = bitsequence[1:(exponent+1)]
    exp_sum = 0
    for cnt in range(exponent):
        if exponent_bits[-(cnt + 1)] == '1':
            exp_sum += pow(2, cnt)
    exp = (exp_sum - 127)

    mantissa_bits = '1' + bitsequence[(exponent + 1):(mantissa + exponent + 1)]
    mant_sum = 0
    for cnt in range(mantissa):
        if mantissa_bits[cnt] == '1':
            mant_sum += pow(2, exp - cnt)

    float_val = sign * mant_sum

    return float_val

def decode_type_info(bytes_in):
    ''' decode the Type Info header of each Payload argument '''
    if len(bytes_in) != 4:
        print("ERROR: Insufficient bytes to decode payload type.")
        return [None, 'None', None]

    bitsequence = "".join([bits(chr(byte)) for byte in bytes_in])

    tyle = None
    if bitsequence[0:4] == '1000':
        tyle = 1 # length of type in byte
    elif bitsequence[0:4] == '0100':
        tyle = 2 # length of type in byte
    elif bitsequence[0:4] == '1100':
        tyle = 4 # length of type in byte
    elif bitsequence[0:4] == '0010':
        tyle = 8 # length of type in byte
    elif bitsequence[0:4] == '1010':
        tyle = 16 # length of type in byte
    else:
        tyle = None

    payload_type = None
    vari = False # variable info used?
    fixp = False # fixed point used?
    trai = False # trace info available?
    
    if bitsequence[4] == '1':
        payload_type = 'BOOL'
    elif bitsequence[5] == '1':
        payload_type = 'SINT'
    elif bitsequence[6] == '1':
        payload_type = 'UINT'
    elif bitsequence[7] == '1':
        payload_type = 'FLOA'
    elif bitsequence[8] == '1':
        payload_type = 'ARAY'
    elif bitsequence[9] == '1':
        payload_type = 'STRG'
    elif bitsequence[10] == '1':
        payload_type = 'RAWD'
    elif bitsequence[11] == '1':
        vari = True
    elif bitsequence[12] == '1':
        fixp = True
    elif bitsequence[13] == '1':
        trai = True
    elif bitsequence[14] == '1':
        payload_type = 'STRU'

    string_coding = None
    if payload_type == 'STRG':
        if bitsequence[15:18] == '000':
            string_coding = 'ASCII'
        elif bitsequence[15:18] == '100':
            string_coding = 'UTF-8'

    return [tyle, payload_type, string_coding, vari, fixp, trai]

def find_next_dlt_pattern(dlt_stream):
    ''' find the next DLT pattern (Hex: 44 4C 54 01) in stream'''
    #dlt_stream.seek(-4, 1) # move back 4 bytes from current position
    dlt_stream.seek(dlt_pattern_position + 1, 0) # move to position of last good DLT pattern + 1
    byte = True
    counter = 0
    while byte:
        byte = dlt_stream.read(1)
        counter += 1
        if byte.hex() == '44':
            byte = dlt_stream.read(1)
            counter += 1
            if byte.hex() == '4c':
                byte = dlt_stream.read(1)
                counter += 1
                if byte.hex() == '54':
                    byte = dlt_stream.read(1)
                    counter += 1
                    if byte.hex() == '01':
                        print("DLT Pattern found, " + str(counter-4) + "bytes skipped.")
                        return True
    return False

def decode_external_storage_header(dlt_stream):
    ''' Decode the DLT External Storage Header of a message'''
    global dlt_pattern_position
    # read 4 bytes and check for DLT Pattern
    dlt_pattern = dlt_stream.read(4)
    if dlt_pattern == b'':
        print("End of DLT Stream reached - decoding complete.")
        return False
    if not dlt_pattern.hex() == '444c5401':
        print("DLT Pattern mismatch: " + dlt_pattern.hex() + ", searching for next match...")
        success = find_next_dlt_pattern(dlt_stream) # search for DLT pattern
        if not success:
            return False
    #record the current position as the position where the dlt pattern '44 4C 54 01' was found
    dlt_pattern_position = dlt_stream.tell()

    # read Timestamp from DLT Header
    date = datetime.datetime.fromtimestamp(int.from_bytes(dlt_stream.read(4), byteorder='little'))
    microsec = int.from_bytes(dlt_stream.read(4), byteorder='little')

    # read ECU ID
    ecu_id_raw = dlt_stream.read(4)
    ecu_id = str(ecu_id_raw, 'Latin-1') if ecu_id_raw else "N/A"

    return [date, microsec, ecu_id]

def decode_standard_header(dlt_stream):
    ''' Decode the DLT Standard Header of a message '''
    # persist first position of standard header in order to know the length of the payload
    pos = dlt_stream.tell()

    # read HTYP byte
    htyp = bits(dlt_stream.read(1))
    mcnt_ = dlt_stream.read(1) # read Message Counter
    leng_ = dlt_stream.read(2) # read Length
    byte_order = 'little' if htyp[1] == 0 else 'big' # read and convert byte order
    mcnt = int.from_bytes(mcnt_, byteorder=byte_order) # convert Message Counter based on byte order
    leng_ = int.from_bytes(leng_, byteorder=byte_order) # convert Length based on byte order
    leng = [leng_, pos] # create tuple of message length and first position of standard header

		# defaults for optional
    ecu = "N/A"
    seid = 0
    tmsp = 0.0
    if htyp[2] == '1':
        ecu = str(dlt_stream.read(4), 'Latin-1') # ECU ID
    if htyp[3] == '1':
        seid = int.from_bytes(dlt_stream.read(4), byteorder=byte_order) # Session ID
    if htyp[4] == '1':
        tmsp = float(int.from_bytes(dlt_stream.read(4), byteorder=byte_order))/10000 # Timestamp

    return [htyp, mcnt, leng, byte_order, ecu, seid, tmsp]

def decode_extended_header(dlt_stream, byte_order):
    ''' Decode the DLT Extended Header of a message '''
    msin = bits(dlt_stream.read(1))
    noar = int.from_bytes(dlt_stream.read(1), byteorder=byte_order) # number of arguments
    apid = str(dlt_stream.read(4), 'Latin-1')
    ctid = str(dlt_stream.read(4), 'Latin-1')

    return [msin, noar, apid, ctid]

def decode_message_info(msin_bits):
    ''' Decode the DLT Message Info byte '''
    mode = 'verbose' if msin_bits[0] == '1' else 'non-verbose'
    if msin_bits[1:4] == '000':
        msg_type = 'DLT Log Message'
        if msin_bits[4:8] == '1000':
            msg_type_info = 'DLT Log Fatal'
        elif msin_bits[4:8] == '0100':
            msg_type_info = 'DLT Log Error'
        elif msin_bits[4:8] == '1100':
            msg_type_info = 'DLT Log Warning'
        elif msin_bits[4:8] == '0010':
            msg_type_info = 'DLT Log Info'
        elif msin_bits[4:8] == '1010':
            msg_type_info = 'DLT Log Debug'
        elif msin_bits[4:8] == '0110':
            msg_type_info = 'DLT Log Verbose'
        else:
            msg_type_info = 'not defined'
    elif msin_bits[1:4] == '100':
        msg_type = 'DLT Trace Message'
        if msin_bits[4:8] == '1000':
            msg_type_info = 'DLT Trace Variable'
        elif msin_bits[4:8] == '0100':
            msg_type_info = 'DLT Trace Function In'
        elif msin_bits[4:8] == '1100':
            msg_type_info = 'DLT Trace Function Out'
        elif msin_bits[4:8] == '0010':
            msg_type_info = 'DLT Trace State'
        elif msin_bits[4:8] == '1010':
            msg_type_info = 'DLT Trace VFB'
        else:
            msg_type_info = 'not defined'
    elif msin_bits[1:4] == '010':
        msg_type = 'DLT Network Message'
        if msin_bits[4:8] == '1000':
            msg_type_info = 'DLT Network Trace IPC'
        elif msin_bits[4:8] == '0100':
            msg_type_info = 'DLT Network Trace CAN'
        elif msin_bits[4:8] == '1100':
            msg_type_info = 'DLT Network Trace FlexRay'
        elif msin_bits[4:8] == '0010':
            msg_type_info = 'DLT Network Trace MOST'
        elif msin_bits[4:8] == '1010':
            msg_type_info = 'DLT Network Trace Ethernet'
        elif msin_bits[4:8] == '0110':
            msg_type_info = 'DLT Network Trace SomeIP'
        else:
            msg_type_info = 'User Defined DLT Network'
    elif msin_bits[1:4] == '110':
        msg_type = 'DLT Control Message'
        if msin_bits[4:8] == '1000':
            msg_type_info = 'DLT Control Request'
        elif msin_bits[4:8] == '0100':
            msg_type_info = 'DLT Control Response'
        else:
            msg_type_info = 'not defined'
    else:
        msg_type = 'not defined'
        msg_type_info = 'not defined'

    return [mode, msg_type, msg_type_info]


def decode_payload(dlt_stream, mode, length, noar):
    ''' Decode the DLT Message Payload '''
    
    payload = []
    if mode == 'verbose':
        for _ in range(noar):
            type_info = dlt_stream.read(4)
            [tyle, payload_type, string_coding, vari, fixp, trai] = decode_type_info(type_info)
            #print([tyle, payload_type, string_coding])
            
            length_int = 0
            message = None
            if payload_type == 'STRG':
                length_raw = dlt_stream.read(2)
                length_int = int.from_bytes(length_raw, byteorder='little')
                msg = dlt_stream.read(length_int)
                if string_coding == 'ASCII':
                    message = str(msg, 'Latin-1')
                elif string_coding == 'UTF-8':
                    message = str(msg, 'utf-8')
                else:
                    print("Unknown String encoding")
            elif (payload_type == 'FLOA') or (payload_type == 'SINT') or (payload_type == 'UINT'):
                length_int = tyle
                msg = dlt_stream.read(length_int)
                if payload_type == 'FLOA':
                    message = convert_float(msg)
                elif payload_type == "UINT":
                    message = int.from_bytes(msg, byteorder='little', signed=False)
                elif payload_type == "SINT":
                    message = int.from_bytes(msg, byteorder='little', signed=True)
            elif payload_type == 'RAWD':
                length_raw = dlt_stream.read(2)
                length_int = int.from_bytes(length_raw, byteorder='little')
                msg = dlt_stream.read(length_int)
                message = msg
            elif payload_type == 'ARAY':
                print("Warning: Message Type 'ARAY' is not verified!")
                num_dim_raw = dlt_stream.read(2)
                #print(num_dim_raw)
                num_dim = int.from_bytes(num_dim_raw, byteorder='little', signed=False)
                total_items = 0
                #print(num_dim)
                num_entries = [None] * num_dim
                for c in range(num_dim): # iterate over number of dimensions
                    num_entries_raw = dlt_stream.read(2)
                    num_entries[c] = int.from_bytes(num_entries_raw, 'little', signed=False)
                    #print(num_entries[c])
                    total_items = total_items + num_entries[c]
                array_data = dlt_stream.read(total_items)
                message = array_data # TODO: for now just copy the raw data into the message body, needs to be converted to array of proper size and type
            else:
                print("Decoding of type " + payload_type + " not implemented.")
                length_int = 1

            payload.append(message)
    elif mode == 'non-verbose':
        #print(length)
        msg_id = int.from_bytes(dlt_stream.read(4), byteorder='little', signed=False)
        pos = dlt_stream.tell()
        # payload length = length indicated in standard header -
        #        (current position - starding position of standard header)
        payload_length = length[1] - (pos - length[0])
        payload_length = max(payload_length, 0)
        msg_binary = dlt_stream.read(payload_length)
        payload.append([msg_id, msg_binary])
    else:
        print("Log Mode (verbose / non-verbose) not specified.")

    #print(payload)
    return payload

def decode_dlt_message(dlt_stream):
    '''Decode a single DLT encoded Message (incl. all Headers)'''

    ### External Storage Header
    decoded_external_storage_header = decode_external_storage_header(dlt_stream)
    if not decoded_external_storage_header:
        return False
    [date, microsec, _] = decoded_external_storage_header # ecu id not needed, coming from Stnd Head

    ### Standard Header
    [htyp, mcnt, leng, byte_order, ecu, seid, tmsp] = decode_standard_header(dlt_stream)

    ### Extended Header (if set in HTYP Byte)
    if htyp[0] == '1':
        [msin, noar, apid, ctid] = decode_extended_header(dlt_stream, byte_order)
        [mode, msg_type, msg_type_info] = decode_message_info(msin)
    else:
        [msin, noar, apid, ctid] = [None, 0, "N/A", "N/A"]
        [mode, msg_type, msg_type_info] = ['non-verbose', 'not defined', 'not defined']

    ### Payload
    payload = decode_payload(dlt_stream, mode, leng, noar)


    decoded_message = {'Date':date,
    	      'Microsec':microsec,
    	      'MCNT':mcnt,
    	      'ECUID':ecu,
    	      'SEID':seid,
    	      'TMSP':tmsp,
    	      'MSTP':msg_type,
    	      'MTIN':msg_type_info,
    	      'Mode':mode,
    	      'NOAR':noar,
    	      'APID':apid,
    	      'CTID':ctid,
    	      'PayLoad':payload}
    	      	
    #print(decoded_message)

    return decoded_message

def decode_dlt_buffered_reader(dlt_stream):
    '''Decode Content from BufferedReader (e.g. a file)'''
    dlt_content = []
    while True:
        dlt_decoded = decode_dlt_message(dlt_stream)
        if dlt_decoded:
            dlt_content.append(dlt_decoded)
        else:
            break
    return dlt_content
