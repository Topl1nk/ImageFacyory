# ImageFacyory
 
## User Documentation for Image Factory

### Overview

Image Factory is a node-based graphical application designed for creating and manipulating images through a modular, visual interface. Users can add, configure, and connect various nodes to build complex image processing workflows.

### Installation

1. **Download and Install Python**: Ensure Python 3.9 is installed on your system.
   - You can download Python from the official [Python website](https://www.python.org/downloads/).

2. **Install Required Packages**: Use `pip` to install the necessary Python packages.
   ```bash
   pip install PyQt5
   ```

3. **Download Image Factory**: Clone or download the repository from the provided source.

### Running the Application

1. **Navigate to the Project Directory**: Open a terminal or command prompt and navigate to the directory where the application files are located.
   ```bash
   cd path/to/ImageFactory
   ```

2. **Run the Application**: Execute the main script to launch the application.
   ```bash
   python main.py
   ```

### User Interface

#### Main Window

- **Menu Bar**: Contains options for File and Window operations.
  - **File Menu**:
    - `New Factory`: Create a new factory (workflow).
    - `New Node`: Add a new node to the canvas.
    - `Settings`: Open the settings dialog to configure application settings.
  - **Window Menu**: Toggle visibility of various dockable panels (Parameters, Canvas, Text Editor, Image Viewer).

#### Dockable Panels

- **Parameters Dock**: Displays parameters and settings for the selected node.
- **Canvas Dock**: The main working area where nodes are added and connected.
- **Text Editor Dock**: Provides a text editing area for writing and editing scripts.
- **Image Viewer Dock**: Displays the output of the image processing workflow.

### Adding and Configuring Nodes

1. **Adding a Node**:
   - Right-click on the canvas to open the context menu.
   - Select the desired node type from the menu to add it to the canvas.

2. **Configuring a Node**:
   - Select a node on the canvas to display its parameters in the Parameters Dock.
   - Adjust the parameters as needed.

3. **Connecting Nodes**:
   - Click and drag from the output point of one node to the input point of another to create a connection.

### Settings

1. **Open Settings Dialog**:
   - Go to `File` > `Settings` to open the settings dialog.

2. **Configure Scripts Folder**:
   - Use the `Browse` button to select the directory containing your custom script nodes.
   - Click `Save Settings` to apply the changes immediately.

### Troubleshooting

- **Invalid Script Directory**: Ensure the script directory set in the settings dialog contains valid Python scripts for nodes.
- **Nodes Not Loading**: If nodes do not appear in the context menu, check the console for errors and ensure the script directory is correctly configured.
- **Application Not Starting**: Verify that all dependencies are installed and that you are using the correct Python version.

### Additional Information

- **Custom Node Development**:
  - Create new node classes by subclassing `NodeBase`.
  - Place your custom node scripts in the directory specified in the settings.
  
- **Styling**:
  - The application supports custom stylesheets. Edit `style.qss` to change the appearance of the application.

### Example Workflow

1. **Start the Application**: Run `main.py` to open the main window.
2. **Add Nodes**: Right-click on the canvas and add the desired nodes.
3. **Connect Nodes**: Drag connections between nodes to build your workflow.
4. **Configure Nodes**: Select each node and adjust its parameters in the Parameters Dock.
5. **View Output**: Use the Image Viewer Dock to see the results of your image processing workflow.

For more detailed information and advanced usage, please refer to the source code and included comments.

### Contact and Support

For issues, suggestions, or contributions, please contact the developer or create an issue in the project's repository.

[![Mutable.ai Auto Wiki](https://img.shields.io/badge/Auto_Wiki-Mutable.ai-blue)](https://wiki.mutable.ai/ollama/ollama)
