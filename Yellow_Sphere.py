import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

class YellowSphere:
    """
    A class to create and display a yellow sphere using Matplotlib.
    make sure to use: pip install matplotlib numpy
    Example animation: https://www.youtube.com/watch?v=IOkre4dEEUU
    """
    
    def __init__(self, radius=1.0, resolution=50):
        """
        Initialize the YellowSphere with specified radius and resolution.
        
        Parameters:
        -----------
        radius : float
            The radius of the sphere (default: 1.0)
        resolution : int
            The resolution of the sphere mesh (default: 50)
            Higher values create a smoother sphere but require more computation
        """
        self.radius = radius
        self.resolution = resolution
        self.fig = None
        self.ax = None
        # These will hold the sphere coordinates after they are generated
        self.x = None
        self.y = None
        self.z = None
    
    def generate_sphere(self):
        """
        Generate the x, y, z coordinates for a sphere.
        
        This uses the parametric equations for a sphere:
        x = radius * sin(phi) * cos(theta)
        y = radius * sin(phi) * sin(theta)
        z = radius * cos(phi)
        
        where phi ranges from 0 to pi (latitude), and
        theta ranges from 0 to 2*pi (longitude).
        """
        # Create evenly spaced points for phi (latitude) and theta (longitude)
        phi = np.linspace(0, np.pi, self.resolution)
        theta = np.linspace(0, 2 * np.pi, self.resolution)
        
        # Create a 2D grid of phi and theta values
        phi, theta = np.meshgrid(phi, theta)
        
        # Convert from spherical to Cartesian coordinates
        self.x = self.radius * np.sin(phi) * np.cos(theta)
        self.y = self.radius * np.sin(phi) * np.sin(theta)
        self.z = self.radius * np.cos(phi)
    
    def create_plot(self):
        """
        Create a 3D plot for the sphere.
        """
        # Create a new figure and a 3D axis
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Set equal aspect ratio for all axes
        self.ax.set_box_aspect([1, 1, 1])
        
        # Set labels for the axes
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        # Set title
        self.ax.set_title(f'Yellow Sphere (Radius = {self.radius})')
    
    def plot_sphere(self):
        """
        Plot the yellow sphere.
        """
        # Generate the sphere coordinates if not already done
        if self.x is None:
            self.generate_sphere()
        
        # Create the plot if not already done
        if self.ax is None:
            self.create_plot()
            
        # Plot the sphere surface
        # Use a yellow color (facecolor) with some transparency (alpha)
        # 'rstride' and 'cstride' control the density of the mesh
        surf = self.ax.plot_surface(
            self.x, self.y, self.z,
            rstride=1, cstride=1,
            color='yellow',  # Set color to yellow
            alpha=0.8,       # Slight transparency
            linewidth=0,     # No wireframe lines
            antialiased=True # Smooth edges
        )
        
        # Set the limits of the axes to be slightly larger than the sphere
        limit = self.radius * 1.1
        self.ax.set_xlim(-limit, limit)
        self.ax.set_ylim(-limit, limit)
        self.ax.set_zlim(-limit, limit)
    
    def show(self):
        """
        Display the plot of the yellow sphere.
        """
        # Make sure the sphere is plotted
        self.plot_sphere()
        
        # Show the plot
        plt.show()
    
    def save(self, filename='yellow_sphere.png'):
        """
        Save the plot to a file.
        
        Parameters:
        -----------
        filename : str
            The name of the file to save (default: 'yellow_sphere.png')
        """
        # Make sure the sphere is plotted
        self.plot_sphere()
        
        # Save the plot to a file
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Sphere saved to {filename}")

# Example usage of the YellowSphere class
if __name__ == "__main__":
    # Create a YellowSphere with radius 2.0 and resolution 100
    sphere = YellowSphere(radius=2.0, resolution=100)
    
    # Display the sphere
    sphere.show()
    
    # Optionally save the sphere image
    # sphere.save()