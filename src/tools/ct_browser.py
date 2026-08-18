"""CT file browser and decoder for FluidSim 4.2."""
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QSplitter, QTextEdit, QStackedWidget, QFileDialog, QMessageBox,
    QLabel, QProgressBar, QPushButton, QComboBox, QGroupBox, QFormLayout,
    QLineEdit
)
from PySide6.QtCore import Qt, QThread, QSize, Signal
from PySide6.QtGui import QColor

# Analyze directory structure to categorize .ct files
def analyze_ct_structure(root_dir):
    """Scan the FluidSim 4.2 directory and categorize .ct files"""
    categories = {
        'Grafcet': [],      # hydraulic/sym/Grafcet
        'Digital': [],      # hydraulic/sym/Digital
        'D': [],            # hydraulic/sym/dde
        'Misc': [],         # hydraulic/sym/misc
        'Main Circuits': [], # hydraulic/ct files
        'Pneumatic Circuits': [], # pneumatic/ct files
        'Unknown': []       # others
    }
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Determine category based on path
        rel_path = os.path.relpath(dirpath, root_dir)
        
        for f in filenames:
            if f.lower().endswith('.ct'):
                full_path = os.path.join(dirpath, f)
                rel_to_root = os.path.relpath(full_path, root_dir)
                
                # Determine category
                if 'Grafcet' in rel_path:
                    categories['Grafcet'].append(rel_to_root)
                elif 'Digital' in rel_path:
                    categories['Digital'].append(rel_to_root)
                elif 'dde' in rel_path:
                    categories['D'].append(rel_to_root)
                elif 'misc' in rel_path:
                    categories['Misc'].append(rel_to_root)
                elif rel_path.startswith('Hydraulic/ct'):
                    categories['Main Circuits'].append(rel_to_root)
                elif rel_path.startswith('Pneumatic/ct'):
                    categories['Pneumatic Circuits'].append(rel_to_root)
                else:
                    categories['Unknown'].append(rel_to_root)
    
    return categories

class CTDecoder:
    """Decode .ct files using multiple methods"""
    
    def __init__(self):
        self.headers = {}
        self.known_patterns = {
            'grafcet': b'n3\xc0\xa6!\xce0\xe8',
            'demo': b'>luB?V\xda\xaf',
            'frames': b'\x93\x03\x0c\x00@D1EM@',
            'symbol': b'\x7f\x89C\xf8z!',
        }
    
    def detect_format(self, data):
        """Detect which .ct format this is"""
        if len(data) < 4:
            return None
        
        first_bytes = data[:16]
        
        for fmt_name, pattern in self.known_patterns.items():
            if first_bytes[:len(pattern)] == pattern:
                return fmt_name
        
        # Check by header
        if data[:4] == b'\x7f\x89C\xf8':
            return 'symbol'
        elif data[:4] == b'\x93\x03\x0c\x00':
            return 'frames'
        elif data[:8] == b'>luB?V\xda\xaf':
            return 'demo'
        elif data[:8] == b'n3\xc0\xa6!\xce0\xe8':
            return 'grafcet'
        
        return 'unknown'
    
    def decode_format(self, data, fmt):
        """Decode based on format"""
        if fmt == 'grafcet' or fmt == 'demo':
            return self._decode_grafcet_demo(data)
        elif fmt == 'frames':
            return self._decode_frames(data)
        elif fmt == 'symbol':
            return self._decode_symbol(data)
        else:
            return self._decode_unknown(data)
    
    def _decode_grafcet_demo(self, data):
        """Decode Grafcet/Demo format (binary RLE-like)"""
        # Skip 8-byte header
        data = data[8:]
        
        out = bytearray()
        i = 0
        while i < len(data):
            b = data[i]
            
            # Look for high-byte runs (0x80-0xBF)
            if 0x80 <= b <= 0xBF and i + 2 < len(data):
                # count = (b & 0x3F) + 1
                count = (b & 0x3F) + 1
                # literal character from next byte
                run = data[i + 2]
                # Repeat count times
                out.extend([run] * count)
                i += 3
            else:
                out.append(b)
                i += 1
        
        return out
    
    def _decode_frames(self, data):
        """Decode Frames.bin format"""
        # Frames.bin appears to be structured binary with strings embedded
        # Try to extract any readable ASCII strings
        out = bytearray()
        i = 0
        while i < len(data):
            # Look for printable sequences
            if 32 <= data[i] <= 126 or data[i] in (10, 13, 9):
                j = i
                while j < len(data) and (32 <= data[j] <= 126 or data[j] in (10, 13, 9)):
                    j += 1
                
                # For short strings, include them
                if j - i <= 100:
                    out.extend(data[i:j])
                i = j
            else:
                i += 1
        
        return out
    
    def _decode_symbol(self, data):
        """Decode Symbol format (tar-like structure)"""
        # Symbol files might be tar archives with component data
        # For now, extract printable strings
        out = bytearray()
        i = 0
        while i < len(data):
            if 32 <= data[i] <= 126:
                j = i
                while j < len(data) and (32 <= data[j] <= 126 or data[j] in (10, 13)):
                    j += 1
                
                # Include strings that look like component info
                if j - i >= 4:
                    out.extend(data[i:j])
                i = j
            else:
                i += 1
        
        return out
    
    def _decode_unknown(self, data):
        """Generic decoding for unknown formats"""
        # Try multiple approaches
        
        # First try high-byte RLE
        out = bytearray()
        i = 0
        while i < len(data):
            b = data[i]
            
            if 0x80 <= b <= 0xBF and i + 2 < len(data):
                count = (b & 0x3F) + 1
                run = data[i + 2]
                out.extend([run] * count)
                i += 3
            else:
                out.append(b)
                i += 1
        
        # Check if result is readable
        printable_count = sum(32 <= c <= 126 for c in out)
        if printable_count / max(1, len(out)) > 0.3:
            return out
        
        # If not readable, try extracting strings
        strings_out = bytearray()
        i = 0
        while i < len(data):
            if 32 <= data[i] <= 126:
                j = i
                while j < len(data) and (32 <= data[j] <= 126 or data[j] in (10, 13)):
                    j += 1
                
                if j - i >= 4:
                    strings_out.extend(data[i:j])
                i = j
            else:
                i += 1
        
        return strings_out

class CTBrowser(QWidget):
    """Browser widget for FluidSim 4.2 .ct files"""

    def __init__(self):
        super().__init__()
        from src.tools.ct_import import detect_fluidsim_root
        self.ct_root = detect_fluidsim_root()
        if self.ct_root is None:
            self.ct_root = Path.home() / "Downloads" / "FluidSim 4.2"
        self.decoder = CTDecoder()
        self.setup_ui()
        self.load_ct_structure()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Control panel
        control_panel = QGroupBox("Controls")
        control_layout = QHBoxLayout()
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(['All', 'Grafcet', 'Digital', 'D', 'Misc',
                                     'Main Circuits', 'Pneumatic Circuits', 'Unknown'])
        self.category_combo.currentTextChanged.connect(self.filter_by_category)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search files...")
        self.search_edit.textChanged.connect(self.filter_files)
        
        control_layout.addWidget(QLabel("Category:"))
        control_layout.addWidget(self.category_combo)
        control_layout.addWidget(self.search_edit)
        
        control_panel.setLayout(control_layout)
        layout.addWidget(control_panel)
        
        # Main content area with tree and preview
        content_splitter = QSplitter(Qt.Horizontal)
        
        # File tree
        tree_group = QGroupBox("File Tree")
        tree_layout = QVBoxLayout()
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["File Explorer"])
        self.tree_widget.itemClicked.connect(self.on_file_selected)
        self.tree_widget.itemDoubleClicked.connect(self.on_file_double_clicked)
        tree_layout.addWidget(self.tree_widget)
        tree_group.setLayout(tree_layout)
        
        # Preview area
        preview_group = QGroupBox("File Content")
        preview_layout = QVBoxLayout()
        
        # Header info
        info_layout = QHBoxLayout()
        self.file_info_label = QLabel("No file selected")
        info_layout.addWidget(self.file_info_label)
        
        preview_layout.addLayout(info_layout)
        
        # Decoder selector
        decoder_layout = QHBoxLayout()
        decoder_layout.addWidget(QLabel("Decoder:"))
        self.decoder_combo = QComboBox()
        self.decoder_combo.addItems(['Auto', 'Grafcet/Demo', 'Frames', 'Symbol', 'Unknown'])
        decoder_layout.addWidget(self.decoder_combo)
        decoder_layout.addStretch()
        preview_layout.addLayout(decoder_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        preview_layout.addWidget(self.progress_bar)
        
        # Preview text
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Decoded Content")
        self.save_button.clicked.connect(self.save_decoded_content)
        action_layout.addWidget(self.save_button)
        
        preview_layout.addLayout(action_layout)
        preview_group.setLayout(preview_layout)
        
        # Add to splitter
        content_splitter.addWidget(tree_group)
        content_splitter.addWidget(preview_group)
        content_splitter.setSizes([300, 500])
        layout.addWidget(content_splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Initialize with all files
        self.all_files = []
        self.current_category = 'All'
        self.current_search = ''
    
    def load_ct_structure(self):
        """Load and organize the .ct file structure"""
        if not os.path.isdir(self.ct_root):
            self.status_label.setText(
                f"FluidSim 4.2 not found at {self.ct_root} — install it or "
                f"place the folder in ~/Downloads/FluidSim 4.2")
            self.tree_widget.clear()
            self.all_files = []
            return
        self.status_label.setText("Scanning directory structure...")
        
        categories = analyze_ct_structure(self.ct_root)
        
        # Clear existing tree
        self.tree_widget.clear()
        self.all_files = []
        
        # Add root item
        root_item = QTreeWidgetItem(self.tree_widget, ["FluidSim 4.2 (.ct files)"])
        self.tree_widget.addTopLevelItem(root_item)
        
        # Add category items
        for category in categories:
            if len(categories[category]) > 0:
                cat_item = QTreeWidgetItem(root_item, [category + f" ({len(categories[category])})"])
                
                # Add files to category
                for rel_path in sorted(categories[category]):
                    file_item = QTreeWidgetItem(cat_item, [rel_path])
                    
                    # Store data for later use
                    file_item.setData(0, Qt.UserRole, rel_path)
                    self.all_files.append({
                        'rel_path': rel_path,
                        'category': category,
                        'full_path': os.path.join(self.ct_root, rel_path)
                    })
                
                cat_item.setExpanded(category in ['Grafcet', 'Digital', 'D', 'Misc'])
        
        # Store categories for filtering
        self.categories = categories
        
        self.status_label.setText(f"Loaded {len(self.all_files)} .ct files")
        self.filter_files()
    
    def filter_files(self, search_text=''):
        """Filter files by category and search text"""
        self.current_search = search_text
        self.display_filtered_files()
    
    def filter_by_category(self, category):
        """Filter by category"""
        self.current_category = category
        self.display_filtered_files()
    
    def display_filtered_files(self):
        """Display filtered files in the tree"""
        # Clear existing tree
        self.tree_widget.clear()
        
        # Add root item
        root_item = QTreeWidgetItem(self.tree_widget, ["FluidSim 4.2 (.ct files)"])
        self.tree_widget.addTopLevelItem(root_item)
        
        # Process files based on filters
        filtered_files = []
        for file_info in self.all_files:
            # Apply category filter
            if self.current_category != 'All' and file_info['category'] != self.current_category:
                continue
            
            # Apply search filter
            if self.current_search:
                if self.current_search.lower() not in file_info['rel_path'].lower():
                    continue
            
            filtered_files.append(file_info)
        
        # Add to categories
        files_by_category = {}
        for file_info in filtered_files:
            if file_info['category'] not in files_by_category:
                files_by_category[file_info['category']] = []
            files_by_category[file_info['category']].append(file_info)
        
        # Add to tree
        for category in sorted(files_by_category.keys()):
            cat_item = QTreeWidgetItem(root_item, [category + f" ({len(files_by_category[category])})"])
            
            for file_info in sorted(files_by_category[category], key=lambda x: x['rel_path']):
                file_item = QTreeWidgetItem(cat_item, [file_info['rel_path']])
                file_item.setData(0, Qt.UserRole, file_info['rel_path'])
                file_item.setData(1, Qt.UserRole, file_info['full_path'])
            
            cat_item.setExpanded(category in ['Grafcet', 'Digital', 'D', 'Misc'])
        
        self.status_label.setText(f"Showing {len(filtered_files)} of {len(self.all_files)} files")
    
    def on_file_selected(self, item, column):
        """Handle file selection"""
        # Show file info
        rel_path = item.data(0, Qt.UserRole)
        if rel_path:
            self.file_info_label.setText(rel_path)
            
            # Decode content
            full_path = item.data(1, Qt.UserRole)
            if full_path:
                self.decode_and_display(full_path)
    
    def on_file_double_clicked(self, item, column):
        """Handle file double-click - open in external viewer if possible"""
        rel_path = item.data(0, Qt.UserRole)
        if rel_path:
            full_path = item.data(1, Qt.UserRole)
            if full_path and os.path.exists(full_path):
                # Try to open with appropriate application based on file size/content
                try:
                    # Show preview instead for now
                    self.decode_and_display(full_path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
    
    def decode_and_display(self, file_path):
        """Decode file content and display it"""
        self.status_label.setText(f"Decoding {os.path.basename(file_path)}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            self.progress_bar.setValue(50)
            
            # Detect format
            fmt = self.decoder.detect_format(data)
            self.status_label.setText(f"Detected format: {fmt}")
            
            # Decode
            decoded_data = self.decoder.decode_format(data, fmt)
            
            self.progress_bar.setValue(100)
            
            # Convert to display text
            display_text = self._format_display_content(file_path, data, decoded_data, fmt)
            
            # Update UI
            self.preview_text.setPlainText(display_text)
            
            # Set decoder combo
            index = ['Auto', 'Grafcet/Demo', 'Frames', 'Symbol', 'Unknown'].index(
                self.decoder_combo.currentText()
            )
            self.decoder_combo.setCurrentIndex(index)
            
            self.status_label.setText(f"Decoded {len(decoded_data)} bytes, {len(display_text)} display chars")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to decode file: {str(e)}")
            self.status_label.setText("Error decoding file")
        
        finally:
            self.progress_bar.setVisible(False)
    
    def _format_display_content(self, file_path, raw_data, decoded_data, fmt):
        """Format decoded content for display"""
        lines = []
        
        # Header information
        lines.append(f"File: {os.path.relpath(file_path, self.ct_root)}")
        lines.append(f"Size: {len(raw_data)} bytes")
        lines.append(f"Format: {fmt}")
        lines.append(f"Decoded: {len(decoded_data)} bytes")
        lines.append("")
        
        # Try to extract readable strings
        ascii_strings = []
        for c in decoded_data:
            if 32 <= c <= 126:
                ascii_strings.append(chr(c))
            elif c in (10, 13):
                ascii_strings.append('\n')
            else:
                ascii_strings.append('.')
        
        display = ''.join(ascii_strings)
        
        # Show if there's meaningful content
        printable_chars = sum(32 <= c <= 126 for c in decoded_data)
        if printable_chars / max(1, len(decoded_data)) > 0.1:
            lines.append("=== Decoded Content (first 2000 chars) ===")
            lines.append(display[:2000])
            lines.append("")
        
        # Always show hex dump of first 64 bytes
        lines.append("=== Hex Dump (first 64 bytes) ===")
        hex_lines = []
        for i in range(0, min(64, len(raw_data)), 16):
            hex_str = ' '.join(f'{b:02x}' for b in raw_data[i:i+16])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw_data[i:i+16])
            hex_lines.append(f"{i:04x}: {hex_str:<48} {ascii_str}")
        
        lines.extend(hex_lines)
        
        return '\n'.join(lines)
    
    def save_decoded_content(self):
        """Save decoded content to file"""
        if not self.preview_text.toPlainText():
            QMessageBox.warning(self, "Warning", "No content to save")
            return
        
        # Get file path
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Decoded Content", str(Path.home()),
            "Text Files (*.txt);;All Files (*)"
        )
        
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(self.preview_text.toPlainText())
                
                QMessageBox.information(self, "Success", f"Content saved to {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {str(e)}")

# Main application
class CTApplication(QWidget):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("FluidSim 4.2 .ct File Browser & Decoder")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # Create browser widget
        self.browser = CTBrowser()
        layout.addWidget(self.browser)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication([])
    window = CTApplication()
    window.setWindowTitle("FluidSim 4.2 .ct Browser")
    window.resize(1200, 800)
    window.show()
    
    app.exec()
