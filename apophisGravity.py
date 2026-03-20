# Calculating the gravitational force of the Apophis asteroid
print("-----------------------------------------------------------")
print("Calculating the gravitational force of the Apophis asteroid")

class GravApop:

# From F = G(M)(m)/d^2 = ma  -->  gApop = G(MApop)/dApop^2
# ** is exponentiation

# G = Gravitational constant (m^3, kg^-1, s^-2), mass = Mass of Apophis (kg), dist = Radius of Apophis (m)

# Initialization method?
    def __init__(self,gConst,mass,dist,config,logger):
        self.config = config
        self.logger = logger
        self.gConst = gConst
        self.mass = mass
        self.dist = dist
        self.gApop = None
    def getGrav(self):
        self.gApop = (self.gConst * self.mass)/(self.dist)
        self.logger.info(f"Gravitational Force Of Apophis Calculated At: {self.gApop}")
    def printVal(self):
        print("Gravitational Constant (G): ", self.gConst)
        print("Mass: ", self.mass)
        print("Radius Squared: ", self.dist)
        print("The Apophis asteroid has a gravitational influence of:\n", self.gApop, "m/s^2")
class GravEarth:

    def __init__(self,gConst,mass,dist,config,logger):
      self.config = config
      self.logger = logger
      self.gConst = gConst
      self.mass = mass
      self.dist = dist
      self.gEarth = None
    def getGrav(self):
      self.gEarth = (self.gConst * self.mass)/(self.dist)
      self.logger.info(f"Gravitational Force Of Earth Calculated At: {self.gEarth}")
    def printVal(self):
      print("Gravitational Constant (G): ", self.gConst)
      print("Mass: ", self.mass)
      print("Radius Squared: ", self.dist)
      print("The Earth has a gravitational influence of:\n", self.gEarth, "m/s^2")
class GravMoon:

    def __init__(self,gConst,mass,dist,config,logger):
      self.config = config
      self.logger = logger
      self.gConst = gConst
      self.mass = mass
      self.dist = dist
      self.gMoon = None
    def getGrav(self):
      self.gMoon = (self.gConst * self.mass)/(self.dist)
      self.logger.info(f"Gravitational Force Of Moon Calculated At: {self.gMoon}")
    def printVal(self):
      print("Gravitational Constant (G): ", self.gConst)
      print("Mass: ", self.mass)
      print("Radius Squared: ", self.dist)
      print("The Moon has a gravitational influence of:\n", self.gMoon, "m/s^2")
class GravSun:

    def __init__(self,gConst,mass,dist,config,logger):
      self.config = config
      self.logger = logger
      self.gConst = gConst
      self.mass = mass
      self.dist = dist
      self.gSun = None
    def getGrav(self):
      self.gSun = (self.gConst * self.mass)/(self.dist)
      self.logger.info(f"Gravitational Force Of Sun Calculated At: {self.gSun}")
    def printVal(self):
      print("Gravitational Constant (G): ", self.gConst)
      print("Mass: ", self.mass)
      print("Radius Squared: ", self.dist)
      print("The Sun has a gravitational influence of:\n", self.gSun, "m/s^2")

