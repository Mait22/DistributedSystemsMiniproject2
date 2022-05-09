import rpyc
from rpyc.utils.server import ThreadedServer


from queue import Queue
import threading
import numpy as np
import random

from copy import copy, deepcopy

soliders = []
votes = []
queuesCommand = {}
queuesCross = {}

command = ""
_sentinel = object()


class solider(threading.Thread):
  def __init__(self,isPrimary,isHonest,ID,state, numSoliders):
    threading.Thread.__init__(self)
    self.isHonest = isHonest
    self.isPrimary = isPrimary
    self.ID = ID
    self.state = state
    self.actualOrder = "___"
    self.otherOpinions = []
    self.otherStates = {}
    self.numSoliders = numSoliders
    self.s1 = False
    self.s2 = False
    self.s3 = False
    self.s4 = False
    self.finish = False
    self.vote = ""
   
  ## Main general sends command to subordiantes 
  def sendCommand(self):
    global command
    global votes
    if self.isPrimary:
      self.actualOrder = command
      votes.append(command)
      self.vote = command
      for s in soliders:
        if not s.isPrimary:
          queuesCommand[s.ID].put(command)
          queuesCommand[s.ID].put(_sentinel)
    self.s1 = True
    #print("Here1")
    return True
  
  ## Receiving main general order from message queue        
  def getCommand(self):
    while True:
      data = queuesCommand[self.ID].get()
      if data is _sentinel or self.isPrimary:
        self.s2 = True
        #print("Here2")
        return True
      else: 
        self.actualOrder = data
        
  ## Main order received by leanding general is exchanged 
  def sendMessages(self):
    sent = 0
    #if not self.isPrimary:
    #  while sent < (self.numSoliders - 1):
    for s in soliders:
      ##print(s.ID)  
      if not s.isPrimary and (self.state == False):
        queuesCommand[s.ID].put("node down")
      elif not s.isPrimary and self.state:
        if self.isHonest:
          queuesCommand[s.ID].put(self.getActualOrder())
        else:
          flip = random.randint(0, 1)
          if flip == 0:
            queuesCommand[s.ID].put(self.getActualOrder())
          else:
            if self.getActualOrder() == "attack":
                queuesCommand[s.ID].put("retreat")
            elif self.getActualOrder() == "retreat":
              queuesCommand[s.ID].put("attack")
      sent += 1
    self.s3 = True
    #print("Here3")
    return True
  
  def receiveMessages(self):
    if not self.isPrimary:
      while len(self.otherOpinions) < (self.numSoliders - 1):
        data = queuesCommand[self.ID].get()
        if data == "attack" or data == "retreat" or data == "node down":
          self.otherOpinions.append(data) 
    self.s4 = True 
    #print("Here 4")
    #print(self.getOtherOptions())  
    return True
      
              
  def getActualOrder(self):
    return self.actualOrder
  
  def getOtherOptions(self):
    return self.otherOpinions
  
  def terminate(self):
    self.finish = True
        
  def run(self):
    
    while self.finish == False:
  
      while not self.s1 or not self.s2 or not self.s3 or not self.s4:
      
        if self.isPrimary:
          self.sendCommand()
          self.s2 = True
          self.s3 = True
          self.s4 = True
      
        elif not self.isPrimary:
          self.s1 = True
          self.getCommand()
          self.sendMessages()
          self.receiveMessages()
        
      else:
        #print("DONE ID")
        #print(self.ID)
        
        ## Make vote
        attack = 0
        retreat = 0
        node_down = 0
        for v in self.otherOpinions:
          if v == "attack":
            attack += 1
          elif v == "retreat":
            retreat += 1
          elif v == "node down":
            node_down += 1
      
        if attack > retreat and attack > node_down and not self.isPrimary:
          global votes
          votes.append("attack")
          self.vote = "attack"
        elif attack < retreat and retreat > node_down and not self.isPrimary:
          votes.append("retreat")
          self.vote = "retreat"
        elif not self.isPrimary:
          votes.append("undefined")
          self.vote = "undefined"
        
        self.finish = True
        return True
    
class MonitorService(rpyc.Service):
  
  def exposed_create_program(self, num):
    print("Received command from client: program")
    try:
      for i in range(num):
        if i == 0:
          soliders.append(solider(True, True, i, True, num))
          queuesCommand[i] = Queue()
          queuesCross[i] = Queue()
        else:
          cheater = (random.randint(0, 1)==1)
          #health = (random.randint(0, 1)==1)
          soliders.append(solider(False, cheater, i, True, num))
          queuesCommand[i] = Queue()
          queuesCross[i] = Queue()
    except:
      print("Error in running a program creation")
  
  def exposed_actual_order(self, cmd):
    print("Received command from client: %s" %(cmd))
    global soliders
    
    if len(soliders) < 3:
      #print("Too little generals in system!")
      return ["Too little generals in system!"]
    #try:
    global command
    command = cmd
    
    global votes
    votes.clear()
    
    for s in soliders:
      if not s.isPrimary: 
        s.start()
    
    for s in soliders:
      if s.isPrimary:
        s.start()
      
    for s in soliders:
        s.join()
        
    #for s in soliders:
    #    print(s.is_alive())
    
    ## Global voting and output string    
    primarities = []
    votes_ = []
    states = []
    output_str = []
    
    attack_n = 0
    retreat_n = 0
    faulty = 0
    not_consistent = 0
    not_faulty = 0
    
    
    for s in soliders:

      IDG = s.ID
      V = s.vote
      votes_.append(V)
      state = "NF" if s.state else "F"
      states.append(state)
      prim = "primary" if s.isPrimary else "secondary"
      primarities.append(prim)
      output_str.append("G%s, %s, majority=%s, state=%s, isHonest=%s" %(IDG, prim, V, state, s.isHonest))
      
      ## Global voting
      if state=="NF" and V == "attack" and prim == "secondary":
        attack_n += 1
        
      if state=="NF" and V == "retreat" and prim == "secondary":
        retreat_n += 1
        
      if state=="NF":
        not_faulty += 1
        
      if state == "F" and prim == "secondary":
        faulty += 1
        
      if V == "undefined" and prim == "secondary":
        not_consistent += 1
      
    execute = ""
    if not_faulty < 3:
      execute = "Can't make decision. Too little functional nodes"
    elif attack_n > (not_faulty-1-attack_n):
      execute = "Exceute order: attack! Non-faulty nodes in the system - %s of %s quorum suggest attack"%(attack_n, not_faulty)
      
    elif retreat_n > (not_faulty-1-retreat_n):
      execute = "Exceute order: retreat! Non-faulty nodes in the system - %s of %s quorum suggest retreat"%(retreat_n, not_faulty)
      
    else:
      execute = "Exceute order: cant decide! Faulty nodes in the system: %s, not vonsistent nodes in the system: %s"%(faulty, not_consistent)
        
    output_str.append(execute)
      
    soliders_copy = []
    for s in soliders:
      soliders_copy.append(solider(s.isPrimary, s.isHonest, s.ID, s.state, s.numSoliders))
    soliders.clear()
    soliders = [s for s in soliders_copy]
    
    return output_str
    
   #except:
   #   print("Error in running a program command attack")
   
  def exposed_set_state(self, ID, state):
    print("Received command from client: set id %s to state %s" %(ID, state))
    
    if state != "" and ID != "":
      for s in soliders:
        if s.ID == ID:
          if s.isPrimary:
            return ["Cant set primary node to be faulty"]
          else:
            if state == "Non-faulty":
              s.state = True
            elif state == "Faulty":
              s.state = False
            else:
              return ["False command"]
            
    
    return_string = []
    for s in soliders:
      return_string.append("G%s, %s, state=%s"%(s.ID,("primary" if s.isPrimary else "secondary") ,("NF" if s.state else "F")))
    return return_string
  
  def exposed_g_add(self, K):
    print("Received command from client: add new generals in amount of %i" %(K))
    
    global soliders
    
    IDs = [s.ID for s in soliders]
    
    for i in range(max(IDs)+1, (max(IDs)+K+1)):
      cheater = (random.randint(0, 1)==1)
      #health = (random.randint(0, 1)==1)
      soliders.append(solider(False, cheater, i, True, 1))
      queuesCommand[i] = Queue()
      queuesCross[i] = Queue()
    
    return_string = []  
    for s in soliders:
      s.numSoliders = len(soliders)
      return_string.append("G%s, %s"%(s.ID, "primary" if s.isPrimary else "secondary"))
      
    return return_string
  
  
  def exposed_g_kill(self, K):
    print("Received command from client: kill generals with id %i" %(K))
    
    global soliders
        
    if (len(soliders) < 1):
      return["Cant remove general, only one general in system"]
    
    soliders_copy = []
    change_primary = False
    
    for s in soliders: 
      if s.ID != int(K):
        soliders_copy.append(s)
      elif s.ID == int(K):
        
        _ = queuesCommand.pop(int(K), None)
        _ = queuesCross.pop(int(K), None)

        if s.isPrimary:
          change_primary = True
      
    soliders.clear()
    soliders = soliders_copy
    
    for s in soliders:
      s.numSoliders = len(soliders)
    
    if change_primary:
      soliders[0].isPrimary = True
    
    return_string = []  
    for s in soliders:
      s.numSoliders = len(soliders)
      return_string.append("G%s, %s"%(s.ID, "primary" if s.isPrimary else "secondary"))
      
    return return_string
    
  
 
if __name__=='__main__':
 
 t=ThreadedServer(MonitorService, port=18812)
 t.start()
  
  

      
  
