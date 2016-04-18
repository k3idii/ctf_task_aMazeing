__author__ = 'keidii'

import SocketServer
import socket
import random
import threading
from time import sleep, time
import hashlib
import logging

import maze

GAMES = {}
TIMEOUT = 90 * 50 * 200    # how log token is valid
        #  ^    ^---^-- size of map 
        #  '- request per second
        #  
        #   max time estimation
        #

KEEP_WORKING = True
CTRL_SERVERS = list()
WAIT_FOR_STR = 10

MSG_POLL_TIME = 0.01  #

# TCP STUFF  ---->

CTRL_PORTS = [31337, 31338, 31336, 31339]
CHAL_RANGE = [322,450] 
SCREEN_PORT = 1337
LISTEN_ADDR = '0.0.0.0'

# < ----

STORY = """
Hello !
Welcome adventurer.
U need to Xplore this cave in order to get treasure !

But first - need to open the gate !
Hint:
  spell need to starts with 'DrgnS'
"""


class TheGame:
  def __init__(self):
    self.created_at = time()
    self.token = hashlib.sha1(str(self.created_at + time())).hexdigest()  # rly random !
    self.start, self.end, self.maze = maze.fuck_generate_maze()
    # show_maze(self.maze) # <- DONT DO IT AT PROD !! 
    self.pos = list(self.start)
    self.is_active = True
    self.messages = []
    self.lock = threading.Lock()

  def get_messages(self, clear=True):
    self.lock.acquire()
    m = self.messages[:]
    if clear:
      self.messages = []
    self.lock.release()
    return m

  def push(self, m):
    self.lock.acquire()
    self.messages.append(m)
    self.lock.release()

  def go_to(self, p):
    return self.maze[p[0], p[1]]

  def move(self, w):
    dst = maze.move(self.pos, w)
    val = self.go_to(dst)
    if val == maze.FINISH:
      return self.push("YOU WIN !, but wait, did you SEE the treasure ?")
    if val == maze.EMPTY:
      self.pos = dst
      return self.push("Ok ! Continue !")
    self.push("Can't go there ... ")


def show_maze(m):
  import matplotlib.pyplot as pyplot

  pyplot.figure(figsize=(15, 5))
  pyplot.imshow(m, cmap=pyplot.cm.binary, interpolation='nearest')
  pyplot.xticks([]), pyplot.yticks([])
  pyplot.show()


def is_good_string(s, chal):
  if not s.startswith("DrgnS"):
    return False
  d = hashlib.sha1(s).hexdigest().upper()
  #print "HEX : ", d
  if d.startswith(chal):
    return True
  return False


def send_slow(sock, msg, t=0.1):
  for ln in msg.split("\n"):
    for c in ln:
      sock.send(c)
      sleep(t)
    sock.send("\n")
    sleep(3 * t)


def handle_screen(sock, client_address, _):
  token = None
  speed = 0.01
  logging.info("SCREEN: new client " + `client_address`)
  try:
    chal = "%X" % random.randint( *CHAL_RANGE )
    send_slow(sock, STORY, speed)
    send_slow(sock, " sha one of spell need to starts with 0x{0} ... ".format(chal), speed)
    send_slow(sock, "... you have {0} seconds ... ...".format(WAIT_FOR_STR), speed)
    sock.settimeout(WAIT_FOR_STR)
    ln = sock.recv(100)
    if not is_good_string(ln.strip(), chal):
      logging.info("Client: {0} - Invalid challenge".format(`client_address`))
      sock.sendall("Nope ;(\n")
      return
    logging.info("Client: {0} - starting game".format(`client_address`))
    sock.send("OK !\nLaunch the game !\n")
    game = TheGame()
    token = game.token
    GAMES[token] = game  # register the game
    sock.sendall(" Your at {0} ".format(game.pos))
    sock.sendall(" Your secret is : {0} (valid {1} sec)\n".format(token, TIMEOUT))
    while KEEP_WORKING:  # the-grate-loop !
      sleep(MSG_POLL_TIME)  # pool time
      msgs = game.get_messages()
      for m in msgs:
        sock.sendall("GAME: {0} \n".format(m))
      if not game.is_active or token not in GAMES:
        sock.sendall("Game Over !\n\n")
        break
    del GAMES[token]  # remove reference !
  except Exception as e:
    logging.error("SCREEN: client " + `client_address` + " fail : " + `e`)
  if token is not None:  # cleanup
    if token in GAMES:
      del GAMES[token]


def handle_control(sock, client_address, server):
  logging.info("CTRL: new client :" + `client_address`)
  token_len = 40  # len sha1.hexdigest
  try:
    sock.settimeout(1)
    while KEEP_WORKING:
      try:
        ln = sock.recv(token_len + 10).strip()
      except socket.timeout:
        # print "TIMEOUT !"
        continue
      if not ln or len(ln) < 2:
        logging.info("CTRL - client disconnect")
        return  # disconnect !
      elif len(ln) != token_len:
        sock.sendall("uhm .. need token ;(\n")
      elif ln not in GAMES:
        sock.sendall("uhm ... token not valid\n")
      else:
        GAMES[ln].move(server.srv_data)
      # ACTION !
  except Exception as e:
    logging.error("CTRL - client fail:" + `e`)
  logging.info("CTRL - client end ")

def timeout_thread():
  logging.info("Starting om om om killer thread ... ")
  while KEEP_WORKING:
    sleep(2)
    logging.info("Omomom: Looking for expired sessions ... ")
    now = time()
    keys = GAMES.keys()
    for k in keys:
      try:
        GAMES[k].lock.acquire()
        t = GAMES[k].created_at
        if now - t > TIMEOUT:
          logging.info("Omomom: Killing token :" + k)
          GAMES[k].is_active = False
          GAMES[k].messages.append("TIME is OUT !")
        GAMES[k].lock.release()
      except Exception as e:
        logging.warn("Omomom: exception :" + `e`)
  logging.info("Omomom: thread end ")


class ThreadTcpServer(SocketServer.ThreadingTCPServer):
  allow_reuse_address = True


def ctrl_server_thread(listen_on, srv_data):
  try:
    global CTRL_SERVERS
    srv = ThreadTcpServer(listen_on, handle_control)
    srv.srv_data = srv_data
    CTRL_SERVERS.append(srv)
    logging.info("CTRL ({0}) UP ... ".format(`srv_data`))
    srv.serve_forever()
    logging.info("CTRL ({0}) DOWN ... ".format(`srv_data`))
  except Exception as e:
    logging.error("CTRL ({0},{1}) FAIL : {2}".format(listen_on, srv_data, `e`))


def main():
  global KEEP_WORKING
  try:
    maze.load_flag()
    th = threading.Thread(target=timeout_thread)
    th.start()
    for i in range(4):
      listen_on = (LISTEN_ADDR, CTRL_PORTS[i])
      th = threading.Thread(target=ctrl_server_thread, args=(listen_on, maze.WAYS[i],))
      th.start()
    # keep main server in main thread:
    s = ThreadTcpServer((LISTEN_ADDR, SCREEN_PORT), handle_screen)
    s.serve_forever()
  except KeyboardInterrupt:
    logging.warn("Interrupt !")
  except Exception as e:
    logging.error("Main loop error :" + `e`)
  KEEP_WORKING = False
  for srv in CTRL_SERVERS:
    srv.shutdown()


def sanity_check():
  maze.load_flag()
  a, b, c = maze.fuck_generate_maze()
  show_maze(c)


if __name__ == '__main__':
  # <if log stdout>
  import sys

  logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
  # </if>

  main()
  KEEP_WORKING = False  # failsafe ;-)
