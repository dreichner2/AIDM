"""
app_qt.py

Refactored GUI wizard for the AI-DM application using PySide6 instead of Tkinter.
Requires: PySide6, requests, python-socketio, Pillow (for image resizing, if desired).
"""

import sys
import random
import queue
import requests
import socketio

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QLineEdit, QMessageBox, QPlainTextEdit,
    QDialog, QFormLayout, QDialogButtonBox,
)
from PySide6.QtGui import QFont, QTextCursor  # Added QTextCursor here
from PySide6.QtCore import Qt, QTimer

# Global fonts used for a slight fantasy feel (fallback if not installed)
HEADER_FONT = QFont("Papyrus, MedievalSharp, UnifrakturMaguntia, Luminari, Fantasy", 24, QFont.Bold)
LABEL_FONT  = QFont("Papyrus, MedievalSharp, UnifrakturMaguntia, Luminari, Fantasy", 12)
BUTTON_FONT = QFont("Papyrus, MedievalSharp, UnifrakturMaguntia, Luminari, Fantasy", 11, QFont.Bold)
INPUT_FONT  = QFont("Papyrus, MedievalSharp, UnifrakturMaguntia, Luminari, Fantasy", 11)

from aidm_client.app import AIDMWizardApp
from aidm_client.pages.base_page import BasePage
from aidm_client.pages.server_page import ServerPage
from aidm_client.pages.campaign_page import CampaignPage
from aidm_client.pages.session_page import SessionPage
from aidm_client.pages.player_page import PlayerPage
from aidm_client.pages.chat_page import ChatPage
from aidm_client.dialogs.campaign_dialogs import CampaignCreateDialog
from aidm_client.dialogs.player_dialogs import PlayerCreateDialog

def main():
    """
    Main entry point for the application.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = AIDMWizardApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
