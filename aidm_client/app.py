import sys
import os
import subprocess
from pathlib import Path
from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PySide6.QtGui import QFontDatabase

from install_fonts import check_first_run, mark_first_run_complete

class AIDMWizardApp(QMainWindow):
    """
    Main application window that manages a QStackedWidget of pages:
    1. ServerPage
    2. CampaignPage
    3. SessionPage
    4. PlayerPage
    5. ChatPage
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI-DM Wizard (SocketIO)")
        self.setMinimumSize(880, 640)

        if check_first_run():
            self.run_first_time_setup()
            mark_first_run_complete()
            
        self.load_embedded_fonts()

        # Add this debug code to help determine ideal image size
        screen = QtWidgets.QApplication.primaryScreen()
        print(f"Screen size: {screen.size().width()}x{screen.size().height()}")
        print(f"Screen physical DPI: {screen.physicalDotsPerInch()}")
        print(f"Screen logical DPI: {screen.logicalDotsPerInch()}")

        # Get absolute path to background image using correct folder structure
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to scripts folder, then to main AI-DM folder, then into assets
        bg_path = os.path.abspath(os.path.join(current_dir, "..", "assets", "background.jpg"))
        bg_path = bg_path.replace("\\", "/")  # Convert to forward slashes for Qt

        # Debug print to verify path
        print(f"Loading background image from: {bg_path}")

        # Verify image file exists
        if not os.path.exists(bg_path):
            print(f"Warning: Background image not found at {bg_path}")
            # Set a fallback background color
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2B2B2B;
                }
            """)
        else:
            # Set background image with absolute path and improved CSS
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-image: url("{bg_path}");
                    background-repeat: no-repeat;
                    background-position: center center;
                    background-attachment: fixed;
                    /* Change to 'contain' to show full image, or keep 'cover' to fill */
                    background-size: contain;
                }}
                /* Apply the background to the central widget with the same properties */
                QStackedWidget {{
                    background-image: url("{bg_path}");
                    background-repeat: no-repeat;
                    background-position: center center;
                    background-attachment: fixed;
                    background-size: contain;
                    /* Add a dark semi-transparent overlay to improve text readability */
                    background-color: rgba(0, 0, 0, 0.5);
                }}
                QLabel, QCheckBox, QRadioButton, QGroupBox {{
                    color: #FFFFFF;
                    font-size: 12px;
                }}
                QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {{
                    background-color: rgba(255, 255, 255, 0.9);
                    color: #000000;
                    border: 1px solid #666666;
                    border-radius: 3px;
                }}
                QPushButton {{
                    background-color: rgba(68, 68, 68, 0.8);
                    color: #FFFFFF;
                    border: 1px solid #666666;
                    border-radius: 3px;
                    padding: 5px 10px;
                }}
                QPushButton:hover {{
                    background-color: rgba(102, 102, 102, 0.8);
                }}
            """)

        # Global state shared across wizard pages
        self.server_url = None
        self.campaign_id = None
        self.world_id = None
        self.session_id = None
        self.player_id = None

        # Central widget: a QStackedWidget that holds all "pages"
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        # Create pages
        self.pages = {}
        self.pages["ServerPage"]   = ServerPage(self)
        self.pages["CampaignPage"] = CampaignPage(self)
        self.pages["SessionPage"]  = SessionPage(self)
        self.pages["PlayerPage"]   = PlayerPage(self)
        self.pages["ChatPage"]     = ChatPage(self)

        # Add them to the stacked widget
        for name, page_widget in self.pages.items():
            self.central_stack.addWidget(page_widget)

        # Show first page
        self.show_frame("ServerPage")

    def show_frame(self, page_name: str):
        """Switch the QStackedWidget to the page with the given name."""
        widget = self.pages.get(page_name)
        if widget:
            self.central_stack.setCurrentWidget(widget)
            # If the page has on_enter, call it
            if hasattr(widget, "on_enter"):
                widget.on_enter()

    def run_first_time_setup(self):
        try:
            install_script = Path(__file__).parent / "install_fonts.py"
            subprocess.run([
                sys.executable, 
                str(install_script.resolve())
            ], check=True)
            
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(
                None,
                "First Run Setup Failed",
                f"Could not install medieval fonts:\n{e}\n"
                "The app will use system fonts instead.",
                QMessageBox.Ok
            )
            
    def load_embedded_fonts(self):
        font_dir = Path(__file__).parent.parent / "assets" / "fonts"
        loaded = []
        
        for font in ["MedievalSharp-Regular.ttf", "UnifrakturMaguntia-Regular.ttf"]:
            font_path = str(font_dir / font)
            if QFontDatabase.addApplicationFont(font_path) != -1:
                loaded.append(font)
                
        if not loaded:
            print("Warning: Could not load embedded medieval fonts")
