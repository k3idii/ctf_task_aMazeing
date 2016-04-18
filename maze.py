import numpy
import random
import collections

__author__ = 'keidii'



HOW_HARD = 3
FLAG_SIZE = (11, 85)
MAZE_SIZE = (int(HOW_HARD * FLAG_SIZE[0]), int(HOW_HARD * FLAG_SIZE[1]))
SPARE_SIZE = (MAZE_SIZE[0] - FLAG_SIZE[0], MAZE_SIZE[1] - FLAG_SIZE[1])
WAYS = [(0, 1), (1, 0), (-1, 0), (0, -1)]

EMPTY = 0
UNK = 1
WALL = 2
START = 3
FINISH = 4

FLAG_DATA = {}

FLAG_SOURCE = """
_____________________________#________________________________________________#
_### _________________###___##_______#__#_####_####______#___#______###__###__##
_#__#________________#______#________#__#____#_#_________#___#_________#____#__#
_#__#_#_##__##__###___##___##__####__####___#__###__#_##_#___#_###__ ##__###___##
____#__#___#__#_#__#____#___#__#_#_#____#__#___#_____#___#___#_#__#____#_#__#__#
_###___#____###_#__#_###____#__#_#_#____#_####_####__#____###__#__#_###__#__#__#
______________#_____________##________________________________________________##
____________###______________#________________________________________________#
"""

def load_flag():
  global FLAG_DATA
  space = [" ", "_", "."]
  lines = FLAG_SOURCE.split("\n")
  rows = len(lines)
  cols = max(map(len,lines))
  img = numpy.zeros( (rows+1, cols+1), dtype=bool)
  for i in range(rows):
    line = lines[i]
    for j,c in zip(range(len(line)), line):
      if c not in space:
        img[i, j] = 1
  FLAG_DATA['rows'] = rows
  FLAG_DATA['cols'] = cols
  FLAG_DATA['img'] = img


def load_flag_from_file_old1():
  FLAG_FILE = "base.txt"
  global FLAG_DATA
  space = [" ", "_", "."]
  f = open(FLAG_FILE, 'r', )
  l1 = f.readline()
  rows, cols = map(int, l1.strip().split(","))
  tgt = numpy.zeros((rows + 1, cols + 1), dtype=bool)
  for i in range(rows):
    line = f.readline().strip()
    for j, c in zip(range(len(line)), line):
      if c not in space:
        tgt[i, j] = 1
  FLAG_DATA['rows'] = rows
  FLAG_DATA['cols'] = cols
  FLAG_DATA['img'] = tgt


def move(a, b):
  return a[0] + b[0], a[1] + b[1]


def paint_flag(tgt, ox, oy, v=0):
  for i in range(FLAG_DATA['rows']):
    for j in range(FLAG_DATA['cols']):
      if FLAG_DATA['img'][i, j]:
        tgt[ox + i, oy + j] = v


def generate_maze():
  def make_maze(w, h, enter_here=None, exit_here=None):
    flag_pos = (random.randint(10, SPARE_SIZE[0]), random.randint(10, SPARE_SIZE[1]))

    if enter_here is None:
      enter_here = (5, 5)
    if exit_here is None:
      exit_here = (w - 3, h - 3)
    shape = (w + 1, h + 1)
    the_maze = numpy.ones(shape, dtype=numpy.int8)

    def ask(p):
      return the_maze[p[0], p[1]]

    def mark(p, v):
      the_maze[p[0], p[1]] = v

    the_maze[enter_here] = START
    the_maze[exit_here] = FINISH

    the_maze[0, :] = the_maze[-1, :] = WALL
    the_maze[:, 0] = the_maze[:, -1] = WALL
    the_maze[1, :] = the_maze[-2, :] = WALL
    the_maze[:, 1] = the_maze[:, -2] = WALL



    queue = collections.deque()
    paths = WAYS[:]
    for i in range(4):
      tgt = move(enter_here,WAYS[i])
      mark(tgt, EMPTY)
      queue.append(tgt)
      tgt = move(exit_here,WAYS[i])
      mark(tgt, EMPTY)

    #queue.append(enter_here)
    while len(queue) > 0:
      e = queue.pop()
      random.shuffle(paths)
      #n = random.randint(2, random.randint(3, 4))  # number of paths
      n = random.randint(2,4)
      for w in paths[n:]:
        tgt = move(e, w)
        if ask(tgt) == UNK:
          mark(tgt, WALL)
      for w in paths[:n]:
        tgt = move(e, w)
        if ask(tgt) == UNK:
          mark(tgt, EMPTY)
          queue.append(tgt)

    for i in range(FLAG_SIZE[0]):
      for j in range(FLAG_SIZE[1]):
        the_maze[flag_pos[0] + i, flag_pos[1] + j] = 0

    paint_flag(the_maze, flag_pos[0], flag_pos[1], v=2)
    return enter_here, exit_here, the_maze

  return make_maze(*MAZE_SIZE)


def fuck_generate_maze():
  for i in range(10):  # in case shit fail ;-D
    try:
      return generate_maze()
    except Exception as e:
      print "FUCK ! retry ", `e`, str(e)
