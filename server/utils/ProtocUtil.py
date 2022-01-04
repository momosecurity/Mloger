# -*- coding: utf-8 -*-
import struct


def GetDynamicWireFormat(data, start, end):
    wire_type = data[start] & 0x7
    firstByte = data[start]
    if (firstByte & 0x80) == 0:
        field_number = (firstByte >> 3)
        return (start + 1, wire_type, field_number)
    else:
        byteList = []
        pos = 0
        while True:
            if start + pos >= end:
                return (None, None, None)
            oneByte = data[start + pos]
            byteList.append(oneByte & 0x7F)
            pos = pos + 1
            if oneByte & 0x80 == 0x0:
                break

        newStart = start + pos

        index = len(byteList) - 1
        field_number = 0
        while index >= 0:
            field_number = (field_number << 0x7) + byteList[index]
            index = index - 1

        field_number = (field_number >> 3)
        return (newStart, wire_type, field_number)


def RetrieveInt(data, start, end):
    pos = 0
    byteList = []
    while True:
        if start + pos >= end:
            return (None, None, False)
        oneByte = data[start + pos]
        byteList.append(oneByte & 0x7F)
        pos = pos + 1
        if oneByte & 0x80 == 0x0:
            break

    newStart = start + pos

    index = len(byteList) - 1
    num = 0
    while index >= 0:
        num = (num << 0x7) + byteList[index]
        index = index - 1
    return (num, newStart, True)


def ParseRepeatedField(data, start, end, message, depth=0):
    while start < end:
        (num, start, success) = RetrieveInt(data, start, end)
        if success == False:
            return False
        message.append(num)
    return True


def ParseData(data, start, end, messages, depth=0):
    ordinary = 0
    while start < end:
        (start, wire_type, field_number) = GetDynamicWireFormat(data, start, end)
        if start == None:
            return False

        if wire_type == 0x00:  # Varint
            # (num, start, success) = RetrieveInt(data, start+1, end)
            (num, start, success) = RetrieveInt(data, start, end)
            if success == False:
                return False

            messages['%02d:%02d:Varint' % (field_number, ordinary)] = num
            ordinary = ordinary + 1

        elif wire_type == 0x01:  # 64-bit
            num = 0
            pos = 7
            while pos >= 0:
                # if start+1+pos >= end:
                if start + pos >= end:
                    return False
                # num = (num << 8) + ord(data[start+1+pos])
                num = (num << 8) + data[start + pos]
                pos = pos - 1

            # start = start + 9
            start = start + 8
            try:
                floatNum = struct.unpack('d', struct.pack('q', int(hex(num), 16)))
                floatNum = floatNum[0]
            except:
                floatNum = None

            if floatNum != None:
                messages['%02d:%02d:64-bit' % (field_number, ordinary)] = floatNum
            else:
                messages['%02d:%02d:64-bit' % (field_number, ordinary)] = num

            ordinary = ordinary + 1


        elif wire_type == 0x02:  # Length-delimited
            (stringLen, start, success) = RetrieveInt(data, start, end)
            if success == False:
                return False
            messages['%02d:%02d:embedded message' % (field_number, ordinary)] = {}
            if start + stringLen > end:
                messages.pop('%02d:%02d:embedded message' % (field_number, ordinary), None)
                return False

            ret = ParseData(data, start, start + stringLen,
                            messages['%02d:%02d:embedded message' % (field_number, ordinary)], depth + 1)
            # print '%d:%d:embedded message' % (field_number, ordinary)
            if ret == False:
                messages.pop('%02d:%02d:embedded message' % (field_number, ordinary), None)
                try:
                    data[start:start + stringLen].decode('utf-8')
                    messages['%02d:%02d:string' % (field_number, ordinary)] = data[start:start + stringLen].decode(
                        'utf-8')
                except:
                    messages['%02d:%02d:repeated' % (field_number, ordinary)] = []
                    ret = ParseRepeatedField(data, start, start + stringLen,
                                             messages['%02d:%02d:repeated' % (field_number, ordinary)], depth + 1)
                    if ret == False:
                        messages.pop('%02d:%02d:repeated' % (field_number, ordinary), None)
                        hexStr = ['0x%x' % x for x in data[start:start + stringLen]]
                        hexStr = ':'.join(hexStr)
                        messages['%02d:%02d:bytes' % (field_number, ordinary)] = hexStr

            ordinary = ordinary + 1
            # start = start+2+stringLen
            start = start + stringLen

        elif wire_type == 0x05:  # 32-bit
            num = 0
            pos = 3
            while pos >= 0:

                # if start+1+pos >= end:
                if start + pos >= end:
                    return False
                # num = (num << 8) + ord(data[start+1+pos])
                num = (num << 8) + data[start + pos]
                pos = pos - 1

            # start = start + 5
            start = start + 4
            try:
                floatNum = struct.unpack('f', struct.pack('i', int(hex(num), 16)))
                floatNum = floatNum[0]
            except:
                floatNum = None

            if floatNum != None:
                messages['%02d:%02d:32-bit' % (field_number, ordinary)] = floatNum
            else:
                messages['%02d:%02d:32-bit' % (field_number, ordinary)] = num

            ordinary = ordinary + 1


        else:
            return False

    return True


def GenValueList(value):
    valueList = []
    # while value > 0:
    while value >= 0:
        oneByte = (value & 0x7F)
        value = (value >> 0x7)
        if value > 0:
            oneByte |= 0x80
        valueList.append(oneByte)
        if value == 0:
            break

    return valueList


def WriteValue(value, output):
    byteWritten = 0
    # while value > 0:
    while value >= 0:
        oneByte = (value & 0x7F)
        value = (value >> 0x7)
        if value > 0:
            oneByte |= 0x80
        output.append(oneByte)
        byteWritten += 1
        if value == 0:
            break

    return byteWritten


def WriteVarint(field_number, value, output):
    byteWritten = 0
    wireFormat = (field_number << 3) | 0x00
    # output.append(wireFormat)
    # byteWritten += 1
    byteWritten += WriteValue(wireFormat, output)
    # while value > 0:
    while value >= 0:
        oneByte = (value & 0x7F)
        value = (value >> 0x7)
        if value > 0:
            oneByte |= 0x80
        output.append(oneByte)
        byteWritten += 1
        if value == 0:
            break

    return byteWritten


def Write64bitFloat(field_number, value, output):
    byteWritten = 0
    wireFormat = (field_number << 3) | 0x01
    # output.append(wireFormat)
    # byteWritten += 1
    byteWritten += WriteValue(wireFormat, output)

    bytesStr = struct.pack('d', value)
    # n = 2
    # bytesList = [bytesStr[i:i + n] for i in range(0, len(bytesStr), n)]
    # i = len(bytesList) - 1
    # while i >= 0:
    #    output.append(int(bytesList[i],16))
    #    byteWritten += 1
    #    i -= 1
    for i in range(0, len(bytesStr)):
        output.append(bytesStr[i])
        byteWritten += 1

    return byteWritten


def Write64bit(field_number, value, output):
    byteWritten = 0
    wireFormat = (field_number << 3) | 0x01
    byteWritten += WriteValue(wireFormat, output)
    # output.append(wireFormat)
    # byteWritten += 1

    for i in range(0, 8):
        output.append(value & 0xFF)
        value = (value >> 8)
        byteWritten += 1

    return byteWritten


def Write32bitFloat(field_number, value, output):
    byteWritten = 0
    wireFormat = (field_number << 3) | 0x05
    # output.append(wireFormat)
    # byteWritten += 1
    byteWritten += WriteValue(wireFormat, output)

    bytesStr = struct.pack('f', value)
    # n = 2
    # bytesList = [bytesStr[i:i + n] for i in range(0, len(bytesStr), n)]
    # i = len(bytesList) - 1
    # while i >= 0:
    #    output.append(int(bytesList[i],16))
    #    byteWritten += 1
    #    i -= 1
    for i in range(0, len(bytesStr)):
        output.append(bytesStr[i])
        byteWritten += 1

    return byteWritten


def Write32bit(field_number, value, output):
    byteWritten = 0
    wireFormat = (field_number << 3) | 0x05
    # output.append(wireFormat)
    # byteWritten += 1
    byteWritten += WriteValue(wireFormat, output)

    for i in range(0, 4):
        output.append(value & 0xFF)
        value = (value >> 8)
        byteWritten += 1

    return byteWritten


def WriteRepeatedField(message, output):
    byteWritten = 0
    for v in message:
        byteWritten += WriteValue(v, output)
    return byteWritten


def ProtocEncode(messages, output=[]):
    byteWritten = 0
    # for key in sorted(messages.iterkeys(), key= lambda x: int(x.split(':')[0]+x.split(':')[1])):
    for key in sorted(messages.keys(), key=lambda x: int(x.split(':')[1])):
        keyList = key.split(':')
        field_number = int(keyList[0])
        wire_type = keyList[2]
        value = messages[key]

        if wire_type == 'Varint':
            byteWritten += WriteVarint(field_number, value, output)
        elif wire_type == '32-bit':
            if type(value) == type(float(1.0)):
                byteWritten += Write32bitFloat(field_number, value, output)
            else:
                byteWritten += Write32bit(field_number, value, output)
        elif wire_type == '64-bit':
            if type(value) == type(float(1.0)):
                byteWritten += Write64bitFloat(field_number, value, output)
            else:
                byteWritten += Write64bit(field_number, value, output)
        elif wire_type == 'embedded message':
            wireFormat = (field_number << 3) | 0x02
            byteWritten += WriteValue(wireFormat, output)
            index = len(output)
            tmpByteWritten = ProtocEncode(messages[key], output)
            valueList = GenValueList(tmpByteWritten)
            listLen = len(valueList)
            for i in range(0, listLen):
                output.insert(index, valueList[i])
                index += 1
            # output[index] = tmpByteWritten
            # print "output:", output
            byteWritten += tmpByteWritten + listLen
        elif wire_type == 'repeated':
            wireFormat = (field_number << 3) | 0x02
            byteWritten += WriteValue(wireFormat, output)
            index = len(output)
            tmpByteWritten = WriteRepeatedField(messages[key], output)
            valueList = GenValueList(tmpByteWritten)
            listLen = len(valueList)
            for i in range(0, listLen):
                output.insert(index, valueList[i])
                index += 1
            # output[index] = tmpByteWritten
            # print "output:", output
            byteWritten += tmpByteWritten + listLen
        elif wire_type == 'string':
            wireFormat = (field_number << 3) | 0x02
            byteWritten += WriteValue(wireFormat, output)

            bytesStr = [elem for elem in messages[key].encode()]

            byteWritten += WriteValue(len(bytesStr), output)

            output.extend(bytesStr)
            byteWritten += len(bytesStr)
        elif wire_type == 'bytes':
            wireFormat = (field_number << 3) | 0x02
            byteWritten += WriteValue(wireFormat, output)

            bytesStr = [int(byte, 16) for byte in messages[key].split(':')]
            byteWritten += WriteValue(len(bytesStr), output)

            output.extend(bytesStr)
            byteWritten += len(bytesStr)

    return byteWritten