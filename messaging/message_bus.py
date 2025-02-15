import zmq
import threading
import base64
import cv2
import json
from node_table import NodeTable
import netif_util
import collections
from datetime import datetime,timedelta
import ntplib
from time import ctime
import time

#
# Decorator for threading methods in a class
#
def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper


class MessageBus(object):
    def __init__(self, device_name, listen_port, role):
        self.ctx = zmq.Context()
        self.device_name = device_name
        self.listen_port = listen_port
        self.role = role
        self.handlers = collections.defaultdict(set)
        self.node_table = NodeTable()
        self.run_message_listener()

    #
    # Creates a socket for listening messages from other nodes
    # (both controllers and cameras).
    #
    @threaded
    def run_message_listener(self):
        print('[MESSAGING] Starting ZMQ listener... device_name:{}, port:{}'.format(self.device_name, self.listen_port))

        sock = self.ctx.socket(zmq.REP)
        sock.bind('tcp://*:{}'.format(self.listen_port))
        while True:
            data = sock.recv()
            msg = data.decode()
            self.handle_message(msg)
            ack_msg = '{}.{}'.format(self.device_name, 'ack')
            sock.send(ack_msg.encode())

    #
    # Sends a JSON Object through the ZeroMQ socket
    #
    def send_message_json(self, target_ip, target_port, msg_dict):
        sock = self.ctx.socket(zmq.REQ)
        sock.connect('tcp://{}:{}'.format(target_ip, target_port))
        print('[MESSAGING] sending msg to {}:{} (type: {})'.format(target_ip, target_port, msg_dict['type']))
        sock.send_json(msg_dict)
        rep = sock.recv().decode()
        # print(' - Reply from receiver: {}'.format(rep))

    @threaded
    def send_message_json_scheduled(self, target_ip, target_port, msg_dict, seconds):
        time.sleep(seconds)
        self.send_message_json(target_ip, target_port, msg_dict)

    #
    # Sends a plain-text string through the ZeroMQ socket
    #
    def send_message_str(self, target_ip, target_port, msg_str):
        sock = self.ctx.socket(zmq.REQ)
        sock.connect('tcp://{}:{}'.format(target_ip, target_port))
        #print('[MESSAGING] sending msg to {}:{}'.format(target_ip, target_port))
        sock.send_string(msg_str)
        rep = sock.recv().decode()
        # print(' - Reply from receiver: {}'.format(rep))

    #
    # Retrieves an IPv4 address and a port number for
    # listening messages.
    #
    def get_my_node_info(self, iface_name):
        netif_list = netif_util.get_netif_list()
        for netif_item in netif_list:
            if netif_item['name'] == iface_name:
                return {'ip': netif_item['ipv4'], 'port': self.listen_port}
        return None

    #
    # Registers a callback function for handling received messages.
    # The parameter includes a message dictionary.
    #
    def register_callback(self, msg_type, callback):
        self.handlers[msg_type].add(callback)

    @threaded
    def handle_message(self, msg):
        try:
            msg_dict = json.loads(msg)

            if 'type' in msg_dict:
                if msg_dict['type'] == 'join':
                    # Reply to the client with the list of all joined nodes
                    for handler in self.handlers.get('join', []):
                        handler(msg_dict)
                elif msg_dict['type'] == 'device_list':
                    for handler in self.handlers.get('device_list', []):
                        handler(msg_dict)
                elif msg_dict['type'] == 'img_e1-1':
                    for handler in self.handlers.get('img_e1-1', []):
                        handler(msg_dict)
                elif msg_dict['type'] == 'img_e1-2':
                    for handler in self.handlers.get('img_e1-2', []):
                        handler(msg_dict)
                elif msg_dict['type'] == 'img_e2':
                    for handler in self.handlers.get('img_e2', []):
                        handler(msg_dict)
                elif msg_dict['type'] == 'img_p':
                    for handler in self.handlers.get('img_p', []):
                        handler(msg_dict)
                elif msg_dict['type'] == 'handoff_request':
                    for handler in self.handlers.get('handoff_request', []):
                        handler(msg_dict)
                elif msg_dict['type'] == 'neighbor_op':
                    for handler in self.handlers.get('neighbor_op', []):
                        handler(msg_dict)
                elif msg_dict['type'] == 'control_op':
                    for handler in self.handlers.get('control_op', []):
                        handler(msg_dict)
                else:
                    pass
            else:
                # Key 'type' does not exist. Discard the message.
                pass

        except json.decoder.JSONDecodeError:
            print(' - Error: invalid JSON format.')
            return
        except Exception as e:
            print(' [cam1]- Error: general unknown error.')
            print(str(e))
            return

    @staticmethod # e1-1
    def create_raw_message(img, framecnt, encode_param, device_name,timegap=timedelta()): # e1-1 (send frames no matter what)
        _, encimg = cv2.imencode('.jpg', img, encode_param)
        encstr = base64.b64encode(encimg).decode('ascii')
        now = datetime.utcnow()+timegap
        curTime = now.strftime('%H:%M:%S.%f') # string format
        json_msg = {'type': 'img_e1-1', 'img_string': encstr, 'time': curTime, 'framecnt': framecnt, 'device_name': device_name}
        return json.dumps(json_msg)

    @staticmethod # e1-2
    def create_raw_req_message(img, framecnt, encode_param, device_name,timegap=timedelta()): # e1-2 (send frames upon request)
        _, encimg = cv2.imencode('.jpg', img, encode_param)
        encstr = base64.b64encode(encimg).decode('ascii')
        now = datetime.utcnow()+timegap
        curTime = now.strftime('%H:%M:%S.%f') # string format
        json_msg = {'type': 'img_e1-2', 'img_string': encstr, 'time': curTime, 'framecnt': framecnt, 'device_name': device_name}
        return json.dumps(json_msg)

    @staticmethod
    def create_e2_message(img, framecnt, encode_param, device_name, coord, timegap=timedelta()): # e1-2 (send frames upon request)
        _, encimg = cv2.imencode('.jpg', img, encode_param)
        encstr = base64.b64encode(encimg).decode('ascii')
        now = datetime.utcnow()+timegap
        curTime = now.strftime('%H:%M:%S.%f') # string format
        json_msg = {'type': 'img_e2', 'img_string': encstr, 'time': curTime, 'framecnt': framecnt, 'device_name': device_name, 'coordinates': coord}
        return json.dumps(json_msg)


    @staticmethod # p: to server
    def create_det_message(img, framecnt, encode_param, device_name,timegap=timedelta()): # e2 & p (send frame + rects)
        _, encimg = cv2.imencode('.jpg', img, encode_param)
        encstr = base64.b64encode(encimg).decode('ascii')
        now = datetime.utcnow()+timegap
        curTime = now.strftime('%H:%M:%S.%f') # string format
        json_msg = {'type': 'img_e1-1', 'img_string': encstr, 'time': curTime, 'framecnt': framecnt, 'device_name': device_name}
        return json.dumps(json_msg)


    @staticmethod # p: to another dev
    def create_message_list_numpy_handoff(img, encode_param, device_name,timegap=timedelta()): # p (send template to next machine)
        _, encimg = cv2.imencode('.jpg', img, encode_param)
        encstr = base64.b64encode(encimg).decode('ascii')
        now = datetime.utcnow()+timegap
        curTime = now.strftime('%H:%M:%S.%f') # string format
        json_msg = {'type': 'handoff_request', 'img_string': encstr, 'time': curTime, 'device_name': device_name}
        return json.dumps(json_msg)
