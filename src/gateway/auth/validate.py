import socket
import selectors
BUFFER_SIZE = 4096

def SendData(b, soc, ep, read=False):
    if not IsConnected(soc):
        print("Connection closed!")
        raise Exception("Disconnected")

    b = TCPPack(b)

    arg = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    arg.settimeout(5)
    try:
        arg.connect(ep)
        arg.sendall(b)

        if read:
            ReadData(soc)
    except Exception as ex:
        print(f"SendData: {ex}")
        raise

def ReadData(soc, wait=0):
    if not IsConnected(soc):
        print("Connection closed!")
        raise Exception("Disconnected")

    try:
        data = soc.recv(BUFFER_SIZE)
        if len(data) == 0:
            print("The remote end has closed the connection.")
            raise Exception("Disconnected")

        process_response(data)

    except Exception as ex:
        print(f"ReadMessages: {ex}")
        raise

def IO_Handler(soc, mask):
    if mask & selectors.EVENT_READ:
        ReadData(soc)

def IsConnected(soc):
    try:
        return soc.fileno() != -1
    except:
        return False


def TCPPack(b):
    a = bytearray()
    len_b = len(b) // 4

    if not efSent:
        efSent = True
        a.append(0xEF)

    if len_b >= 0x7F:
        a.append(0x7F)
        a.extend(struct.pack('<I', len_b))
    else:
        a.append(len_b)

    a.extend(b)  # only data, no sequence number, no CRC32

    return bytes(a)
def process_response(data):
    print(f"Received data: {data}")
    
class UnencryptedMessage:
    def __init__(self, auth_key: int, message_id: int, data: bytes):
        self.auth_key_id = auth_key
        self.message_id = message_id
        self.data_length = len(data)
        self.message_data = data
        self.message_type = self.B2Hr(data, 0, 4)
        a = bytearray()
        a.extend(self.auth_key_id.to_bytes(8, byteorder='little', signed=True))
        a.extend(self.message_id.to_bytes(8, byteorder='little', signed=True))
        a.extend(self.data_length.to_bytes(4, byteorder='little', signed=True))
        a.extend(self.message_data)
        self.data = bytes(a)

    def __str__(self):
        return f"""
        raw_data: {self.B2H(self.data)}
     auth_key_id: {self.i2H(self.auth_key_id)}  {self.auth_key_id}
      message_id: {self.i2H(self.message_id)}  {self.message_id}
     data_length: {self.i2H(self.data_length)}  {self.data_length}
    message_data: {self.B2H(self.message_data)}
    message_type: {self.message_type}
        """

    @staticmethod
    def B2H(b: bytes) -> str:
        return ''.join('{:02X}'.format(x) for x in b)

    @staticmethod
    def B2Hr(b: bytes, start: int, length: int) -> str:
        return UnencryptedMessage.B2H(b[start:start+length])

    @staticmethod
    def i2H(i: int) -> str:
        return '{:016X}'.format(i)


def send_unencrypted(m: UnencryptedMessage):
    print(m, end='', flush=True)
    SendData(m.data, True)

def send_encrypted(m: EncryptedMessage):
    print(m, end='', flush=True)
    SendData(m.data, True)
