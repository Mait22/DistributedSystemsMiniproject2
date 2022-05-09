import rpyc
import sys
import time

if len(sys.argv) < 2:
   exit("Usage {} SERVER".format(sys.argv[0]))
server = sys.argv[1]
conn = rpyc.connect(server,18812)

def get_input(v):
   if sys.version_info >= (3, 0):
      return input(v)
   else:
      return raw_input(v)

while True:
   cmd = get_input(">> ").split()
   if not cmd:
      continue
   
   elif cmd[0] == 'program':
      if int(cmd[1]) < 1:
         print('Wrong command')
      else:
         conn.root.create_program(int(cmd[1]))
         
   elif cmd[0] == 'g-state':
      if len(cmd) == 3:
         res = conn.root.set_state(int(cmd[1]), (cmd[2]))
         for l in res:
            print(l)
      elif len(cmd) == 1:
         res = conn.root.set_state("", "")
         for l in res:
            print(l)
      else:
         print('Wrong command')
         
   elif cmd[0] == 'actual-order':
      if str(cmd[1]) == 'attack':
         res = conn.root.actual_order('attack')
         for l in res:
            print(l)
      elif str(cmd[1]) == 'retreat':
         res = conn.root.actual_order('retreat')
         for l in res:
            print(l)
      else:
         print("Wrong command")
       
   elif cmd[0] == 'g-add':
      if int(cmd[1]) >= 1:
         res = conn.root.g_add(int(cmd[1]))
         for l in res:
            print(l)
      else:
         print("Wrong command")
             
   elif cmd[0] == 'g-kill':
      if int(cmd[1]) >= 0:
         res = conn.root.g_kill(int(cmd[1]))
         for l in res:
            print(l)
      else:
         print("Wrong command")
   
   

