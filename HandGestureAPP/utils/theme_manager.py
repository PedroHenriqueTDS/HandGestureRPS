class ThemeManager:
    @staticmethod
    def get_dark_theme() -> str:
        return """
        QMainWindow {
            background-color: #0b0f19;
            color: #e2e8f0;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QMenuBar {
            background-color: #111827;
            color: #00e5ff;
            border-bottom: 1px solid #1f2937;
            padding: 4px;
            font-size: 14px;
        }
        
        QMenuBar::item {
            background: transparent;
            padding: 8px 16px;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background-color: #1f2937;
            color: #00e5ff;
        }
        
        QPushButton {
            background-color: #111827;
            color: #00e5ff;
            border: 2px solid #00e5ff;
            border-radius: 8px;
            padding: 10px 20px;
            font: bold 14px 'Segoe UI';
            min-width: 140px;
        }
        
        QPushButton:hover {
            background-color: #00e5ff;
            color: #000000;
        }
        
        QPushButton:pressed {
            background-color: #00b8cc;
            border-color: #00b8cc;
            color: #000000;
        }
        
        QPushButton:disabled {
            background-color: #1f2937;
            color: #4b5563;
            border-color: #374151;
        }
        
        QLabel {
            color: #e2e8f0;
            background: transparent;
        }
        
        QDialog {
            background-color: #0b0f19;
            border: 1px solid #1f2937;
            border-radius: 12px;
        }
        
        QGroupBox {
            font: bold 16px 'Segoe UI';
            color: #00e5ff;
            border: 2px solid #1f2937;
            border-radius: 10px;
            margin-top: 15px;
            padding-top: 20px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
            background-color: #0b0f19;
        }
        
        QLabel#CameraFeed {
            border: 2px dashed #00e5ff;
            border-radius: 12px;
            background-color: #000000;
        }
        
        QSlider::groove:horizontal {
            height: 6px;
            background: #1f2937;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: #00e5ff;
            border: none;
            width: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #ffffff;
        }
        
        QComboBox, QSpinBox {
            background-color: #111827;
            color: #00e5ff;
            border: 1px solid #374151;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 14px;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QCheckBox {
            color: #e2e8f0;
            font-size: 14px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid #374151;
            background-color: #111827;
        }
        
        QCheckBox::indicator:checked {
            background-color: #00e5ff;
            border-color: #00e5ff;
        }
        """
