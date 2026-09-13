import polars as pl
from PySide6.QtCore import QTimer, Qt, QObject, Signal, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow,QWidget,
    QVBoxLayout, QHBoxLayout, QComboBox, 
    QFileDialog, QPushButton, QRadioButton,
    QLabel
)

from services.anki_connect import get_anki_decks
from services.csv_to_flashcard import tts_func_map
from components.card import CardCols, CardTable, CardUploadProgress, CardUploadWorker

EMPTY_DECK = "-"

class InitAnkiConnectWorker(QObject):
    connected = Signal(object)

    def run(self):
        try:
            decks = get_anki_decks()
            self.connected.emit(decks)
        except ConnectionError as e:
            self.connected.emit(None)
            print(e)

class MFCAMainWindow(QMainWindow):
    decks = [EMPTY_DECK]
    ac_cnctd = False
    def __init__(self):
        super().__init__()
        self.eng_char_deck = self.char_pnyn_deck = self.decks[0]
        self.setWindowTitle("")
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setAlignment(Qt.AlignTop)

        tts_row, self.tts_box = self.create_tts_select("Select Text to Speech Option: ")
        self.tts_box.currentTextChanged.connect(self.set_eng_char_deck)

        eng_char_row, self.eng_char_box = self.create_deck_select("English to Characters: ")
        self.eng_char_box.currentTextChanged.connect(self.set_eng_char_deck)

        char_pnyn_row, self.char_pnyn_box = self.create_deck_select("Characters to Pinyin: ")
        self.char_pnyn_box.currentTextChanged.connect(self.set_char_pnyn_deck)
        self.init_anki()

        self.file_button = QPushButton("Open File")
        self.file_button.clicked.connect(self.openFileDialog)

        self.add_cards_button = QPushButton("Add New Cards")
        self.add_cards_button.clicked.connect(self.add_cards)
        self.card_table = CardTable()

        self.card_upload_prog = CardUploadProgress(self)

        layout.addLayout(self.create_ac_status())
        layout.addLayout(tts_row)
        layout.addLayout(eng_char_row)
        layout.addLayout(char_pnyn_row)
        layout.addWidget(self.file_button)
        layout.addWidget(self.add_cards_button)
        layout.addWidget(self.card_table)
        layout.addLayout(self.create_table_buttons())

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def init_anki(self):
        self.anki_thread = QThread()
        self.anki_worker = InitAnkiConnectWorker()

        self.anki_worker.moveToThread(self.anki_thread)

        self.anki_thread.started.connect(self.anki_worker.run)
        self.anki_worker.connected.connect(self.anki_handle_connected)

        self.anki_thread.finished.connect(self.anki_thread.deleteLater)
        self.anki_thread.finished.connect(self._card_upload_cleanup)
        self.anki_thread.start()

    def anki_handle_connected(self, event):
        self.ac_cnctd = not not event
        if self.ac_cnctd:
            self.decks = [EMPTY_DECK, *event]
            self.eng_char_box.clear()
            self.eng_char_box.addItems(self.decks)
            self.char_pnyn_box.clear()
            self.char_pnyn_box.addItems(self.decks)
            self.set_ac_style()

        self.anki_thread.quit()
        self.anki_worker.deleteLater()
        
    def set_eng_char_deck(self, text: str):
        self.eng_char_deck = text
        QTimer.singleShot(0, self.eng_char_box.hidePopup)

    def set_tts_type(self, text: str):
        self.tts_type = text
        QTimer.singleShot(0, self.tts_box.hidePopup)
    
    def set_char_pnyn_deck(self, text: str):
        self.char_pnyn_deck = text
        QTimer.singleShot(0, self.char_pnyn_box.hidePopup)

    def openFileDialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Open File")

        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)

        if file_dialog.exec():
            file = file_dialog.selectedFiles()[0]
            raw_cards = pl.read_csv(file)
            cols = [col.lower().title() for col in raw_cards.columns]
            char_pos = cols.index(CardCols.chars)
            pinyin_pos = cols.index(CardCols.pnyn)
            eng_pos = cols.index(CardCols.eng)
            for card_row in raw_cards.iter_rows():
                row_pos = self.card_table.rowCount()
                self.card_table.insertDataRow(
                    row_pos,
                    [card_row[char_pos],card_row[pinyin_pos], card_row[eng_pos]]
                )

    def add_cards(self):
        ct = self.card_table
        no_rows = ct.rowCount()
        if no_rows == 0:
            return
        
        self.card_upload_prog.init(no_rows)

        self.anki_thread = QThread()
        self.anki_worker = CardUploadWorker(ct, self.eng_char_deck, self.char_pnyn_deck, self.tts_type)

        self.anki_worker.moveToThread(self.anki_thread)

        self.anki_thread.started.connect(self.anki_worker.run)
        self.anki_worker.progress.connect(self.card_upload_prog.increment_progress)

        self.anki_worker.finished.connect(self.anki_thread.quit)
        self.anki_worker.finished.connect(self.anki_worker.deleteLater)

        self.anki_thread.finished.connect(self.anki_thread.deleteLater)
        self.anki_thread.finished.connect(self.card_upload_prog.close)

        self.anki_thread.start()

    def _card_upload_cleanup(self):
        self.anki_worker = None
        self.anki_thread = None

    def create_ac_status(self) -> QHBoxLayout: 
        row = QHBoxLayout()
        ac_status_text = QLabel("Anki Connect Status: ")
        self.ac_status = QRadioButton(self)
        self.ac_status.setDisabled(True)
        refresh_button = QPushButton()
        refresh_button.setIcon(QIcon.fromTheme("view-refresh"))

        def refresh_event():
            if self.anki_thread or self.anki_worker:
                return
            self.init_anki()
            self.set_ac_style()
        refresh_button.clicked.connect(refresh_event)
        
        row.addStretch() # pushes radio to the right
        row.addWidget(ac_status_text)
        row.addWidget(self.ac_status)
        row.addWidget(refresh_button)
        self.set_ac_style()
        return row

    def set_ac_style(self):
        colour = "green" if self.ac_cnctd else "red"
        self.ac_status.setStyleSheet("""
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border-radius: 7px;""" +
                f"background-color: {colour};" + "}"
        )

    def create_tts_select(self, label_text: str):
        row = QHBoxLayout()
        label = QLabel(label_text)
        box = QComboBox(self)
        box.addItems(list(tts_func_map.keys()))
        row.addWidget(label)
        row.addWidget(box)
        return row, box

    def create_deck_select(self, label_text: str):
        row = QHBoxLayout()
        label = QLabel(label_text)
        box = QComboBox(self)
        box.addItems(self.decks)
        row.addWidget(label)
        row.addWidget(box)
        return row, box

    def create_table_buttons(self):
        buttons = QHBoxLayout()
        add_row = QPushButton("add_row")
        add_row.clicked.connect(self.card_table.add_row)
        gen_pnyn = QPushButton("Generate Pinyin")
        gen_pnyn.clicked.connect(self.card_table.gen_pinyin)
        remove_row = QPushButton("remove_row")
        remove_row.clicked.connect(self.card_table.remove_row)
        buttons.addWidget(add_row)
        buttons.addWidget(gen_pnyn)
        buttons.addWidget(remove_row)
        return buttons

app = QApplication()
window = MFCAMainWindow()
window.show()
window.resize(500,500)
app.exec()