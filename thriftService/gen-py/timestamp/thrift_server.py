

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import TimestampService
from timestamp_handler import TimestampHandler

def main():
    handler = TimestampHandler()
    processor = TimestampService.Processor(handler)
    transport = TSocket.TServerSocket(port=10000)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    print("Thrift timestamp service is served")
    server.serve()

if __name__ == "__main__":
    main()
