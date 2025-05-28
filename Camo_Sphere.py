import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from mpl_toolkits.mplot3d import Axes3D
from scipy.ndimage import gaussian_filter

class CamoSphere:
    """
    A class for creating and displaying a 3D sphere with a camouflage pattern
    using green, blue, and brown colors in Matplotlib.
    use: pip install scipy
    """
    
    def __init__(self, radius=1.0, resolution=50, seed=42):
        """
        Initialize the CamoSphere with the given parameters.
        
        Parameters:
        -----------
        radius : float
            The radius of the sphere (default: 1.0)
        resolution : int
            The resolution of the sphere mesh (default: 50)
            Higher values create a smoother sphere but require more processing
        seed : int
            Random seed for reproducible camo patterns (default: 42)
        """
        self.radius = radius
        self.resolution = resolution
        self.seed = seed
        self.fig = None
        self.ax = None
        # Set random seed for reproducibility
        np.random.seed(self.seed)
        
    def generate_sphere_coordinates(self):
        """
        Generate the x, y, z coordinates for a sphere using parametric equations.
        
        Returns:
        --------
        x, y, z : numpy arrays
            The 3D coordinates representing points on the sphere's surface
        """
        # Create a meshgrid of angles (phi and theta)
        # phi: goes from 0 to pi (latitude)
        # theta: goes from 0 to 2*pi (longitude)
        phi = np.linspace(0, np.pi, self.resolution)
        theta = np.linspace(0, 2 * np.pi, self.resolution)
        
        # Create a 2D meshgrid by taking the outer product of phi and theta
        phi, theta = np.meshgrid(phi, theta)
        
        # Convert from spherical coordinates to Cartesian coordinates
        x = self.radius * np.sin(phi) * np.cos(theta)
        y = self.radius * np.sin(phi) * np.sin(theta)
        z = self.radius * np.cos(phi)
        
        return x, y, z
    
    def generate_camo_pattern(self):
        """
        Generate a camouflage pattern with blending of green, blue, and brown.
        
        Returns:
        --------
        pattern : numpy array
            A 2D array representing the camo pattern colors
        """
        # Define the camo colors (RGB values)
        dark_green = to_rgb('darkgreen')    # (0.0, 0.39, 0.0)
        forest_green = to_rgb('forestgreen')  # (0.13, 0.55, 0.13)
        navy_blue = to_rgb('navy')          # (0.0, 0.0, 0.5)
        dark_brown = to_rgb('saddlebrown')  # (0.55, 0.27, 0.07)
        olive_green = to_rgb('olive')       # (0.5, 0.5, 0.0)
        
        camo_colors = [dark_green, forest_green, navy_blue, dark_brown, olive_green]
        
        # Create empty array for pattern
        pattern = np.zeros((self.resolution, self.resolution, 3))
        
        # Generate multiple noise layers for each color
        for i, color in enumerate(camo_colors):
            # Generate noise at different frequencies
            noise1 = np.random.rand(self.resolution, self.resolution)
            noise2 = np.random.rand(self.resolution//4, self.resolution//4)
            noise2 = np.repeat(np.repeat(noise2, 4, axis=0), 4, axis=1)
            
            # Apply gaussian blur to create smoother transitions
            noise1 = gaussian_filter(noise1, sigma=2.0 + i)
            noise2 = gaussian_filter(noise2, sigma=3.0)
            
            # Combine the noise layers
            combined_noise = (noise1 * 0.6 + noise2 * 0.4)
            
            # Threshold to create blob-like patterns for each color
            threshold = 0.65 + i * 0.05  # Varying thresholds for each color
            mask = combined_noise > threshold
            
            # Apply color where mask is True
            for c in range(3):  # RGB channels
                pattern[:, :, c] = np.where(mask, 
                                          color[c], 
                                          pattern[:, :, c])
        
        # Fill any remaining black areas (where no color was applied) with olive green
        black_mask = np.all(pattern == 0, axis=2)
        for c in range(3):
            pattern[:, :, c] = np.where(black_mask, 
                                      olive_green[c], 
                                      pattern[:, :, c])
            
        return pattern
    
    def plot(self, show=True):
        """
        Plot the sphere with a camouflage pattern.
        
        Parameters:
        -----------
        show : bool
            Whether to display the plot immediately (default: True)
            
        Returns:
        --------
        fig, ax : matplotlib Figure and Axes objects
            The figure and axes containing the plotted sphere
        """
        # Generate the 3D coordinates
        x, y, z = self.generate_sphere_coordinates()
        
        # Generate camouflage pattern
        camo_pattern = self.generate_camo_pattern()
        
        # Create a figure and a 3D axis
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Plot the sphere with the camo pattern
        surf = self.ax.plot_surface(x, y, z, facecolors=camo_pattern,
                                   linewidth=0, antialiased=True)
        
        # Set equal aspect ratio so the sphere looks spherical
        self.ax.set_box_aspect([1, 1, 1])
        
        # Set labels for the axes
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        # Set a title
        self.ax.set_title(f'Camouflage Sphere (Radius = {self.radius})')
        
        # Show the plot if requested
        if show:
            plt.show()
            
        return self.fig, self.ax
    
    def save(self, filename='camo_sphere.png', dpi=300):
        """
        Save the plot to a file.
        
        Parameters:
        -----------
        filename : str
            The filename to save the plot to (default: 'camo_sphere.png')
        dpi : int
            The resolution in dots per inch (default: 300)
        """
        if self.fig is None:
            # If we haven't plotted yet, do it now but don't show
            self.plot(show=False)
            
        self.fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        print(f"Camouflage sphere saved to {filename}")

# Example usage
if __name__ == "__main__":
    # Create a camouflage sphere with radius 2.0 and resolution 100
    sphere = CamoSphere(radius=2.0, resolution=100)
    
    # Plot the sphere
    sphere.plot()
    
    # Optionally save the sphere to a file
    # sphere.save()