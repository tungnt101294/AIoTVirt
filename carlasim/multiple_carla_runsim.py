import json
import multiple_carla
import time
import argparse
from tqdm import tqdm

def createstartendzones(counts):
    

def main():
    connections = {
        1: [2,3,4,5,6,7,8,9],
        2: [1,4,5,6,7,8,9],
        3: [1,2,6,7,8,9],
        4: [1,2,6,7,8,9],
        5: [1,2,6,7,8,9],
        6: [1,2,3,4,7,8,9],
        7: [1,2,3,4,5,6,9],
        8: [1,2,3,4,5,6,9],
        9: [1,2,3,4,5,6,7]
    }

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        action="store",
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-s', '--startzone',
        metavar='s',
        default=1,
        type=int,
        action="store",
        help='Start zone (default: 1)')
    argparser.add_argument(
        '-ez', '--endzone',
        default=9,
        type=int,
        action="store",
        help='End zone (default: 2)')
    argparser.add_argument(
        '--config',
        default='10_camera_new_config.ini',
        help='path to the configuration file (default: "config.ini")')
    argparser.add_argument(
        '--run',
        default=0,
        type=int)
    argparser.add_argument(
        '-ci', '--conn_index',
        default=0,
        type=int)

    args = argparser.parse_args()
    paths = None

    with open("paths_4x4.json", "r") as f:
        paths = json.load(f)
    startzone = args.startzone
    port = args.port
    config = args.config
    run = args.run
    conn_index = args.conn_index
    startset, endset = createstartendzones(100)

    print(startzone)
    for endzone in tqdm(connections[startzone][conn_index:]):
        endzone = int(endzone)
        counter = run
        tracks = paths["{}-{}".format(startzone, endzone)]
        tracks = tracks[run:]
        for path in tqdm(tracks):
            start = time.time()
             #* basically have multiple 
            client = multiple_carla.BasicSynchronousClient(startzone, endzone, counter)
            client.parse_config(config)
            client.connect_client(port)
            client.game_loop(path)
            counter += 1
            print(time.time() - start)
            time.sleep(1)
        run = 0

if __name__ == '__main__':
    main()