# Calculating the gravitational force of the Apophis asteroid
print("-----------------------------------------------------------")
print("Calculating the gravitational force of the Apophis asteroid")

class GravApop:

# From F = G(M)(m)/d^2 = ma  -->  gApop = G(MApop)/dApop^2
# ** is exponentiation

# G = Gravitational constant (m^3, kg^-1, s^-2), mass = Mass of Apophis (kg), dist = Radius of Apophis (m)

# Initialization method?
    def __init__(self,G,mass,dist):
      self.G = G
      self.mass = mass
      self.dist = dist
      self.gApop = None


    def getGrav(self):
        self.gApop = (self.G * self.mass)/(self.dist)


    def printVal(self):
        print("Gravitational Constant (G): ", self.G)
        print("Mass: ", self.mass)
        print("Radius Squared: ", self.dist)
        print("The Apophis asteroid has a gravitational influence of:\n", self.gApop, "m/s^2")

# values of MApop,dApop,G all in order
asteroid_1 = GravApop(6.67e-11, 6.1e10, 185**2)
asteroid_1.getGrav()
asteroid_1.printVal()

print("-----------------------------------------------------------")

class GravEarth:

    def __init__(self,G,mass,dist):
      self.G = G
      self.mass = mass
      self.dist = dist
      self.gEarth = None

    def getGrav(self):
      self.gEarth = (self.G * self.mass)/(self.dist)


    def printVal(self):
      print("Gravitational Constant (G): ", self.G)
      print("Mass: ", self.mass)
      print("Radius Squared: ", self.dist)
      print("The Earth has a gravitational influence of:\n", self.gEarth, "m/s^2")

# values of MApop,dApop,G all in order
earth1 = GravEarth(6.67e-11, 5.97e24, 6.37e6**2)
earth1.getGrav()
earth1.printVal()


print("-----------------------------------------------------------")

class GravMoon:

    def __init__(self,G,mass,dist):
      self.G = G
      self.mass = mass
      self.dist = dist
      self.gEarth = None

    def getGrav(self):
      self.gMoon = (self.G * self.mass)/(self.dist)


    def printVal(self):
      print("Gravitational Constant (G): ", self.G)
      print("Mass: ", self.mass)
      print("Radius Squared: ", self.dist)
      print("The Moon has a gravitational influence of:\n", self.gMoon, "m/s^2")

# values of MApop,dApop,G all in order
earth1 = GravMoon(6.67e-11, 7.346e22, 1.74e6**2)
earth1.getGrav()
earth1.printVal()


print("-----------------------------------------------------------")

class GravSun:

    def __init__(self,G,mass,dist):
      self.G = G
      self.mass = mass
      self.dist = dist
      self.gEarth = None

    def getGrav(self):
      self.gSun = (self.G * self.mass)/(self.dist)


    def printVal(self):
      print("Gravitational Constant (G): ", self.G)
      print("Mass: ", self.mass)
      print("Radius Squared: ", self.dist)
      print("The Sun has a gravitational influence of:\n", self.gSun, "m/s^2")

# values of MApop,dApop,G all in order
earth1 = GravSun(6.67e-11, 1.989e30, 6.96e8**2)
earth1.getGrav()
earth1.printVal()