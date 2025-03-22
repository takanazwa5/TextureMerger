import resources_rc
from PySide6 import QtCore, QtWidgets, QtGui
from PIL import Image, ImageChops
from os import listdir

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.sourceFolderPath = ""
        self.destinationFolderPath = ""
        self.totalSteps = 0
        self.currentStep = 0

        self.app = app
        self.setWindowTitle("Texture Merger")
        self.setWindowIcon(QtGui.QIcon(":/icon.png"))
        self.setFixedSize(500, 500)

        self.sourceFolderBtn = QtWidgets.QPushButton("Set source folder...")
        self.sourceFolderBtn.pressed.connect(self.selectSourceFolder)
        self.sourceFolderLabel = ElidedLabel("No source folder selected")
        self.sourceFolderLabel.contentsRect
        self.sourceFolderLabel.setStyleSheet("color: red;")
        sourceFolderCouple = QtWidgets.QWidget()
        sourceFolderCouple.setFixedWidth(228)
        sourceFolderCoupleLayout = QtWidgets.QVBoxLayout()
        sourceFolderCoupleLayout.addWidget(self.sourceFolderBtn)
        sourceFolderCoupleLayout.addWidget(self.sourceFolderLabel, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        sourceFolderCouple.setLayout(sourceFolderCoupleLayout)

        self.destinationFolderBtn = QtWidgets.QPushButton("Set destination folder...")
        self.destinationFolderBtn.pressed.connect(self.selectDestinationFolder)
        self.destinationFolderLabel = ElidedLabel("No destination folder selected")
        self.destinationFolderLabel.setStyleSheet("color: red;")
        destinationFolderCouple = QtWidgets.QWidget()
        destinationFolderCouple.setFixedWidth(228)
        destinationFolderCoupleLayout = QtWidgets.QVBoxLayout()
        destinationFolderCoupleLayout.addWidget(self.destinationFolderBtn)
        destinationFolderCoupleLayout.addWidget(self.destinationFolderLabel, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        destinationFolderCouple.setLayout(destinationFolderCoupleLayout)

        inputGroup = QtWidgets.QGroupBox("Input")
        inputGroupLayout = QtWidgets.QHBoxLayout()
        inputGroupLayout.addWidget(sourceFolderCouple)
        inputGroupLayout.addWidget(destinationFolderCouple)
        inputGroup.setLayout(inputGroupLayout)

        self.outputFormatDropdown = QtWidgets.QComboBox()
        self.outputFormatDropdown.addItem("PNG")
        self.outputFormatDropdown.addItem("JPG")
        self.channelPackCheckbox = QtWidgets.QCheckBox("Pack ARM")
        self.combineBtn = QtWidgets.QPushButton("Merge")
        self.combineBtn.pressed.connect(self.mergeTextures)

        outputGroup = QtWidgets.QGroupBox("Output")
        outputGroupLayout = QtWidgets.QHBoxLayout()
        outputGroupLayout.addWidget(self.outputFormatDropdown)
        outputGroupLayout.addWidget(self.channelPackCheckbox)
        outputGroupLayout.addWidget(self.combineBtn)
        outputGroup.setLayout(outputGroupLayout)

        self.outputConsole = TextEdit()
        
        centralWidget = QtWidgets.QWidget()
        centralWidgetLayout = QtWidgets.QVBoxLayout()
        centralWidgetLayout.addWidget(inputGroup)
        centralWidgetLayout.addWidget(outputGroup)
        centralWidgetLayout.addWidget(self.outputConsole)
        centralWidget.setLayout(centralWidgetLayout)

        self.setCentralWidget(centralWidget)
        self.show()

    def selectSourceFolder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Set source folder...")
        if folder:
            self.sourceFolderLabel.setText(folder)
            self.sourceFolderLabel.setStyleSheet("color: white;")
            self.sourceFolderPath = folder

    def selectDestinationFolder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Set destination folder...")
        if folder:
            self.destinationFolderLabel.setText(folder)
            self.destinationFolderLabel.setStyleSheet("color: white;")
            self.destinationFolderPath = folder

    def setUIDisabled(self, value):
        self.sourceFolderBtn.setDisabled(value)
        self.destinationFolderBtn.setDisabled(value)
        self.outputFormatDropdown.setDisabled(value)
        self.channelPackCheckbox.setDisabled(value)
        self.combineBtn.setDisabled(value)

    def mergeNormals(self, textures):
        for texture in textures[1:]:
            for i in range(textures[0].size[0]):
                for j in range(textures[0].size[1]):
                    if textures[0].getpixel((i, j)) == (127, 127, 255) and not texture.getpixel((i, j)) == (127, 127, 255):
                        textures[0].putpixel((i, j), texture.getpixel((i, j)))
                self.currentStep += 1
                self.outputConsole.updateProgress(f"({int((self.currentStep / self.totalSteps) * 100)}%)")
        return textures[0]

    def mergeAO(self, textures):
        for texture in textures[1:]:
            textures[0] = ImageChops.multiply(textures[0], texture)
            self.currentStep += 1
            self.outputConsole.updateProgress(f"({int((self.currentStep / self.totalSteps) * 100)}%)")
            QtWidgets.QApplication.processEvents()
        return textures[0]

    def mergeOther(self, textures):
        for texture in textures[1:]:
            textures[0] = Image.alpha_composite(textures[0], texture)
            self.currentStep += 1
            self.outputConsole.updateProgress(f"({int((self.currentStep / self.totalSteps) * 100)}%)")
            QtWidgets.QApplication.processEvents()
        return textures[0]
    
    def packARM(self, textures):
        if "Mixed_AO" in textures:
            r = textures["Mixed_AO"].convert("L")
        else:
            r = Image.new("L", textures[list(textures.keys())[0]].size, 0)
        
        if "Roughness" in textures:
            g = textures["Roughness"].convert("L")
        else:
            g = Image.new("L", textures[list(textures.keys())[0]].size, 0)
        
        if "Metallic" in textures:
            b = textures["Metallic"].convert("L")
        else:
            b = Image.new("L", textures[list(textures.keys())[0]].size, 0)

        a = None
        if self.outputFormatDropdown.currentText().lower() == "png":
            a = textures[list(textures.keys())[0]].getchannel("A")
            return Image.merge("RGBA", (r, g, b, a))
        else:
            return Image.merge("RGB", (r, g, b))

    def mergeTextures(self):
        if not self.sourceFolderPath:
            self.outputConsole.appendError("No source folder selected")
            return
        
        if not self.destinationFolderPath:
            self.outputConsole.appendError("No destination folder selected")
            return
        
        if len(listdir(self.sourceFolderPath)) == 0:
            self.outputConsole.appendError("No files found in source folder")
            return

        self.outputConsole.append("")
        self.outputConsole.append("Starting merge...")
        self.outputConsole.append("")
        QtWidgets.QApplication.processEvents()

        self.setUIDisabled(True)
        textures = {}

        self.outputConsole.append("Files found:")
        QtWidgets.QApplication.processEvents()

        for filename in listdir(self.sourceFolderPath):
            if not (filename.endswith(".png") or filename.endswith(".jpg")):
                self.outputConsole.appendWarning(f"- {filename} (Skipping - not a texture)")
                continue

            extension = filename.rsplit(".")[-1]
            filename = filename.rstrip(f".{extension}")
            slices = filename.rsplit("_")
            id = 0
            type = ""

            if slices[-1].isdigit():
                id = int(slices[-1])
                type = slices[-2]
            else:
                type = slices[-1]
                
            type = "Base_color" if type == "color" else type
            type = "Normal_OpenGL" if type == "OpenGL" else type
            type = "Mixed_AO" if type == "AO" else type

            if not type in ["Base_color", "Normal_OpenGL", "Mixed_AO", "Roughness", "Metallic"]:
                self.outputConsole.appendWarning(f"- {filename} (Skipping - invalid filename)")
                continue

            if not type in textures:
                textures[type] = {}

            if not id in textures[type]:
                textures[type][id] = []

            textures[type][id].append(Image.open(f"{self.sourceFolderPath}/{filename}.{extension}"))

            self.outputConsole.append(f"- {filename}.{extension}")
            QtWidgets.QApplication.processEvents()

        self.outputConsole.append("")
        QtWidgets.QApplication.processEvents()

        if len(textures) == 0:
            self.outputConsole.appendError("Nothing to merge")
            self.setUIDisabled(False)
            return

        texturesForChannelPack = {}
        
        for type in textures:
            self.outputConsole.append(f"Merging {type}... (0%)")
            QtWidgets.QApplication.processEvents()

            self.totalSteps = 0
            self.currentStep = 0
            for id in textures[type]:
                n = len(textures[type][id])
                if n > 1:
                    if type == "Normal_OpenGL":
                        self.totalSteps += (n - 1) * textures[type][id][0].size[0]
                    else:
                        self.totalSteps += n - 1

            for id in textures[type]:
                if len(textures[type][id]) < 2:
                    continue
                
                result = None

                try:
                    if type == "Normal_OpenGL":
                        result = self.mergeNormals(textures[type][id])
                    elif type == "Mixed_AO":
                        result = self.mergeAO(textures[type][id])
                    else:
                        result = self.mergeOther(textures[type][id])

                    outputFormat = self.outputFormatDropdown.currentText().lower()
                    if outputFormat == "jpg":
                        result = result.convert("RGB")

                    if id == 0:
                        result.save(f"{self.destinationFolderPath}/{type}.{outputFormat}")
                    else:
                        result.save(f"{self.destinationFolderPath}/{id}_{type}.{outputFormat}")

                    if self.channelPackCheckbox.isChecked() and type in ["Mixed_AO", "Roughness", "Metallic"]:
                        if not id in texturesForChannelPack:
                            texturesForChannelPack[id] = {}

                        texturesForChannelPack[id][type] = result

                except Exception as e:
                    self.outputConsole.appendError(f"- Error: {e}")

        self.outputConsole.append("")
        QtWidgets.QApplication.processEvents()

        if self.channelPackCheckbox.isChecked():
            self.outputConsole.append("Packing ARM... (0%)")
            QtWidgets.QApplication.processEvents()

            self.totalSteps = len(texturesForChannelPack)
            self.currentStep = 0
            
            for id in texturesForChannelPack:
                try:
                    result = self.packARM(texturesForChannelPack[id])

                    if outputFormat == "jpg":
                        result = result.convert("RGB")

                    if id == 0:
                        result.save(f"{self.destinationFolderPath}/ARM.{outputFormat}")
                    else:
                        result.save(f"{self.destinationFolderPath}/{id}_ARM.{outputFormat}")

                    self.currentStep += 1
                    self.outputConsole.updateProgress(f"({int((self.currentStep / self.totalSteps) * 100)}%)")
                
                except Exception as e:
                    self.outputConsole.appendError(f"- Error: {e}")

            self.outputConsole.append("")
            QtWidgets.QApplication.processEvents()

        self.outputConsole.appendOK("Done")
        self.setUIDisabled(False)

class ElidedLabel(QtWidgets.QLabel):
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), QtCore.Qt.TextElideMode.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)

class TextEdit(QtWidgets.QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        
    def appendError(self, text):
        self.setFontWeight(QtGui.QFont.Weight.Bold)
        self.setTextColor(QtGui.QColor("red"))
        self.append(text)
        self.setTextColor(QtGui.QColor("white"))
        self.setFontWeight(QtGui.QFont.Weight.Normal)
        QtWidgets.QApplication.processEvents()

    def appendWarning(self, text):
        self.setFontWeight(QtGui.QFont.Weight.Bold)
        self.setTextColor(QtGui.QColor("yellow"))
        self.append(text)
        self.setTextColor(QtGui.QColor("white"))
        self.setFontWeight(QtGui.QFont.Weight.Normal)
        QtWidgets.QApplication.processEvents()

    def appendOK(self, text):
        self.setFontWeight(QtGui.QFont.Weight.Bold)
        self.setTextColor(QtGui.QColor("green"))
        self.append(text)
        self.setTextColor(QtGui.QColor("white"))
        self.setFontWeight(QtGui.QFont.Weight.Normal)
        QtWidgets.QApplication.processEvents()

    def updateProgress(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.PreviousWord, QtGui.QTextCursor.MoveMode.KeepAnchor, 3)
        cursor.removeSelectedText()
        cursor.insertText(text)
        QtWidgets.QApplication.processEvents()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MainWindow(app)
    app.exec()

