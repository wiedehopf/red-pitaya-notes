from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_STREAM
from signal import signal, SIGINT
from struct import pack
from sys import exit

rates = {32000:0, 64000:1, 128000:2, 256000:3, 512000:4, 1024000:5, 2048000:6}

parser = ArgumentParser()

parser.add_argument('--addr', help = 'IP address of the Red Pitaya board', required = True)
parser.add_argument('--freq', help = 'center frequency in Hz (0 - 61440000)', type = int, required = True)
parser.add_argument('--rate', help = 'sample rate (20000, 50000, 100000, 250000, 500000, 1250000, 2500000)', type = int, required = True)
parser.add_argument('--corr', help = 'frequency correction in ppm (-100 - 100)', type = float, required = True)
parser.add_argument('--file', help = 'output file', required = True)

args = parser.parse_args()

if args.freq < 0 or args.freq > 62500000:
  parser.print_help()
  exit(1)

if args.rate not in rates:
  parser.print_help()
  exit(1)

if args.corr < -100 or args.corr > 100:
  parser.print_help()
  exit(1)

ctrl_sock = socket(AF_INET, SOCK_STREAM)
ctrl_sock.settimeout(5)
try:
  ctrl_sock.connect((args.addr, 1001))
except:
  print('error: could not connect to', args.addr)
  exit(1)
ctrl_sock.settimeout(None)

data_sock = socket(AF_INET, SOCK_STREAM)
data_sock.settimeout(5)
try:
  data_sock.connect((args.addr, 1001))
except:
  print('error: could not connect to', args.addr)
  exit(1)
data_sock.settimeout(None)

ctrl_sock.send(pack('<I', 0))
ctrl_sock.send(pack('<I', 0<<28 | int((1.0 + 1e-6 * args.corr) * args.freq)))
ctrl_sock.send(pack('<I', 1<<28 | rates[args.rate]))

data_sock.send(pack('<I', 1))

interrupted = False

def signal_handler(signal, frame):
  global interrupted
  interrupted = True

signal(SIGINT, signal_handler)

try:
  f = open(args.file, 'wb')
except:
  print('error: could not open', args.file)
  exit(1)

data = data_sock.recv(4096)
while data and not interrupted:
  f.write(data)
  data = data_sock.recv(4096)
