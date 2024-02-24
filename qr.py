import codecs
import os
import sys
import time
import binascii

def readfile(folder, filename): # reads a file and turns it into a hexdump.
    with open(f'{folder}/{filename}', 'rb') as f:
        for chunk in iter(lambda: f.read(), b''):
            hex_dump = codecs.encode(chunk, 'hex')
    return hex_dump

def writefile(folder, filename, data): # writes a new file with the edited data.
    thing = f'{data}'[2:][:-1].upper()
    thing2 = binascii.unhexlify(thing)
    with open(f'{folder}/{filename}', 'wb') as f: # overwrites data to the quest files.
        f.write(thing2)
    print(f'Written new data to {folder}/{filename}.')

def readvalues(bytes): # gets necessary values to get the pointers and stuff.
    end_pointerl = hex(int(len(bytes)/2))[-4:]
    end_pointer = f'{end_pointerl[-2:] + end_pointerl[:-2]}'.encode('utf-8')
    hex_qspl = bytes[464:468].decode()                          # quest start of all-text pointer in hexadecimal, little endian.
    hex_qsp = int(f'0x{hex_qspl[-2::] + hex_qspl[:-2:]}', 0)*2  # quest start of all-text pointer in decimal, converted to big endian multiplied by 2 to account for 2 characters making up 1 byte.
    hex_tspl = bytes[hex_qsp:hex_qsp+4].decode()                # quest all of the text section in hex, little endian. At this point, everything after it is text for the quest (title,obj,desc,sub).
    hex_tsp = int(f'0x{hex_tspl[-2::] + hex_tspl[:-2:]}', 0)*2  # quest all of the text section in decimal, multiplied by 2 and converted to big endian.
    quest_pointers = bytes[hex_qsp:hex_qsp+64]                  # all the quest text section POINTERS in a row. (title, mainobj, sideA, sideB, successcond, failcond, contractor, desc).
    indv_p = [quest_pointers[i:i+4] for i in range(0, len(quest_pointers), 4)] # above but put into a list to separate them.
    indv_ps = [indv_p[0].decode(), indv_p[2].decode(), indv_p[4].decode(), indv_p[6].decode(), indv_p[8].decode(), indv_p[10].decode(), indv_p[12].decode(), indv_p[14].decode()] # above, decoded to LE hex.
    indv_psv = [] # pre-populated list for individual pointers decoded to decimal and turned to BE (big endian).

    # get the individual text pointers in decimal, BE.
    for i in range(len(indv_ps)):
        indv_psv.append(int(f'0x{indv_ps[i][-2::] + indv_ps[i][:-2:]}', 0))

    # return a dictionary of useful values.
    return {'textpointer' : hex_qsp, 'alltext' : hex_tsp, 'qp' : quest_pointers, 'indv_psv' : indv_psv, 'indv_ps': indv_ps, 'endpointer' : end_pointer,
            'dif1' : (indv_psv[1]-indv_psv[0]), 'dif2' : (indv_psv[2]-indv_psv[1]), 'dif3' : (indv_psv[3]-indv_psv[2]), 'dif4' : (indv_psv[4]-indv_psv[3]), 
            'dif5' : (indv_psv[5]-indv_psv[4]), 'dif6' : (indv_psv[6]-indv_psv[5]), 'dif7' : (indv_psv[7]-indv_psv[6]) }

def populatepointers(bytes, maintext, mainvalues): # populate all pointers.
    # get the index of the end of the file and turn it into hex. This will be pointing to where all the text pointers are.
    new_pointerl = hex(int(len(bytes)/2))[2:]
    # get the new pointers for quest text by looking at the offset of the edited version.
    np1 = hex(int(new_pointerl, 16) + 32)[2:]
    np2 = hex(int(np1,16) + (mainvalues['dif1']))[2:]
    np3 = hex(int(np2,16) + (mainvalues['dif2']))[2:]
    np4 = hex(int(np3,16) + (mainvalues['dif3']))[2:]
    np5 = hex(int(np4,16) + (mainvalues['dif4']))[2:]
    np6 = hex(int(np5,16) + (mainvalues['dif5']))[2:]
    np7 = hex(int(np6,16) + (mainvalues['dif6']))[2:]
    np8 = hex(int(np7,16) + (mainvalues['dif7']))[2:]
    
    # swap first 2 characters with last 2 characters for new_pointer, place it in the general text pointer spot and turn new pointers into a list for next step.
    # in the case of the pointer starting on a new row of bytes, add a 0 to prevent uneven data length.
    if len(new_pointerl) == 3: new_pointer = f'{new_pointerl[-2:] + "0" + new_pointerl[:-2]}'.encode('utf-8')
    else: new_pointer = f'{new_pointerl[-2:] + new_pointerl[:-2]}'.encode('utf-8')
    bytes = bytes[:464] + new_pointer + bytes[468:]
    newpointers = [np1,np2,np3,np4,np5,np6,np7,np8]
    
    # set newly converted quest text pointers to readable bytes for the quest file.
    newpointersconverted = b''
    for pointer in newpointers:
        newpointersconverted += (pointer[-2:] + pointer[:-2]).encode() + b'0000'
    # add the new pointers together with all the edited text.
    bytes = bytes + newpointersconverted + maintext
    return bytes

if sys.argv[1] and sys.argv[2]:
    try:
        # get relevant information from the edited quest, such as text.
        hex_main = readfile(sys.argv[1], sys.argv[2])
        mainv = readvalues(hex_main)
        maintext = hex_main[mainv['alltext']:]

        # loop through all other files to edit them.
        for file in os.listdir(f'{os.getcwd()}/{sys.argv[1]}'):
            if file != sys.argv[2]: 
                hex_file = readfile(sys.argv[1], file)
                hexfv = readvalues(hex_file)

                newfiledata = populatepointers(hex_file, maintext, mainv)
                writefile(sys.argv[1], file, newfiledata)

    except Exception as e: # throws an exception if something's wrong. report this back to me.
        print(f"Error: {e}")
else: # standard reporting to user of incorrect usage.
    print("Use this script by running it in your cmd.\nExample: py qr.py foldername editedfile\npy qr.py 55693 55693d0.bin\nExiting in 5 seconds.")
    time.sleep(5)