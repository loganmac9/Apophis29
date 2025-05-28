import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

class OvalShape:
    """
    A class to create and display an oval (ellipsoid) using Matplotlib.
    """
    
    def __init__(self, a=2.0, b=1.5, c=1.0, resolution=50):
        """
        Initialize the OvalShape with specified semi-axes lengths and resolution.
        
        Parameters:
        -----------
        a : float
            The semi-axis length in x direction (default: 2.0)
        b : float
            The semi-axis length in y direction (default: 1.5)
        c : float
            The semi-axis length in z direction (default: 1.0)
        resolution : int
            The resolution of the oval mesh (default: 50)
            Higher values create a smoother surface but require more computation
        """
        self.a = a  # x-axis radius
        self.b = b  # y-axis radius
        self.c = c  # z-axis radius
        self.resolution = resolution
        self.fig = None
        self.ax = None
        # These will hold the oval coordinates after they are generated
        self.x = None
        self.y = None
        self.z = None
    
    def generate_oval(self):
        """
        Generate the x, y, z coordinates for an oval (ellipsoid).
        
        This uses the parametric equations for an ellipsoid:
        x = a * sin(phi) * cos(theta)
        y = b * sin(phi) * sin(theta)
        z = c * cos(phi)
        
        where phi ranges from 0 to pi (latitude), and
        theta ranges from 0 to 2*pi (longitude).
        """
        # Create evenly spaced points for phi (latitude) and theta (longitude)
        phi = np.linspace(0, np.pi, self.resolution)
        theta = np.linspace(0, 2 * np.pi, self.resolution)
        
        # Create a 2D grid of phi and theta values
        phi, theta = np.meshgrid(phi, theta)
        
        # Convert from spherical to Cartesian coordinates with different scaling factors
        self.x = self.a * np.sin(phi) * np.cos(theta)
        self.y = self.b * np.sin(phi) * np.sin(theta)
        self.z = self.c * np.cos(phi)
    
    def create_plot(self):
        """
        Create a 3D plot for the oval.
        """
        # Create a new figure and a 3D axis
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Set equal aspect ratio for all axes
        self.ax.set_box_aspect([self.a/max(self.a, self.b, self.c), 
                               self.b/max(self.a, self.b, self.c), 
                               self.c/max(self.a, self.b, self.c)])
        
        # Set labels for the axes
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        # Set title
        self.ax.set_title(f'Light Grey Oval (Semi-axes: {self.a}, {self.b}, {self.c})')
    
    def plot_oval(self):
        """
        Plot the light grey oval.
        """
        # Generate the oval coordinates if not already done
        if self.x is None:
            self.generate_oval()
        
        # Create the plot if not already done
        if self.ax is None:
            self.create_plot()
            
        # Plot the oval surface
        # Use a light grey color with some transparency
        surf = self.ax.plot_surface(
            self.x, self.y, self.z,
            rstride=1, cstride=1,
            color='lightgrey',  # Using lightgrey color
            alpha=0.8,          # Slight transparency
            linewidth=0,        # No wireframe lines
            antialiased=True    # Smooth edges
        )
        
        # Set the limits of the axes to be slightly larger than the oval
        self.ax.set_xlim(-self.a * 1.1, self.a * 1.1)
        self.ax.set_ylim(-self.b * 1.1, self.b * 1.1)
        self.ax.set_zlim(-self.c * 1.1, self.c * 1.1)
    
    def show(self):
        """
        Display the plot of the oval.
        """
        # Make sure the oval is plotted
        self.plot_oval()
        
        # Show the plot
        plt.show()
    
    def save(self, filename='light_grey_oval.png'):
        """
        Save the plot to a file.
        
        Parameters:
        -----------
        filename : str
            The name of the file to save (default: 'light_grey_oval.png')
        """
        # Make sure the oval is plotted
        self.plot_oval()
        
        # Save the plot to a file
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Oval saved to {filename}")

# Example usage of the OvalShape class
if __name__ == "__main__":
    # Create an oval with semi-axes lengths 2.0, 1.5, 1.0 and resolution 100
    oval = OvalShape(a=2.0, b=1.5, c=1.0, resolution=100)
    
    # Display the oval
    oval.show()
    
    # Optionally save the oval image
    # oval.save()