from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QVBoxLayout, QTableWidget, QAbstractItemView,
    QHeaderView, QTableWidgetItem, QDialog,
    QProgressBar,
)
from pypinyin import pinyin, Style
from services.anki_connect import add_card_with_audio_bytes
from services.csv_to_flashcard import create_card

class CardCols:
    chars = "Characters"
    pnyn = "Pinyin"
    eng = "English"

class CardTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels([CardCols.chars, CardCols.pnyn, CardCols.eng])
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels([CardCols.chars, CardCols.pnyn, CardCols.eng])
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropOverwriteMode(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def insertDataRow(self, pos: int, data: list[str] = ["","",""]):
        """Takes a postion and data that supports indexing
           in the order: chars, pinyin, english
        """
        self.insertRow(pos)
        for col, item in enumerate(data):
            data = QTableWidgetItem(item).setFlags(
                Qt.ItemIsSelectable |
                Qt.ItemIsEnabled |
                Qt.ItemIsEditable |
                Qt.ItemIsDragEnabled |
                Qt.ItemIsDropEnabled
            )
            self.setItem(pos, col, QTableWidgetItem(item))

    def dropEvent(self, event):
        source_index = self.indexAt(event.position().toPoint()) 
        source_row = self.currentRow()
        target_row = source_index.row()
        if not source_index.isValid() or source_row == target_row:
            event.ignore()
            return

        row_data = []
        for col in range(self.columnCount()):
            item = self.item(source_row, col)
            row_data.append(item.text() if item else "")
        self.removeRow(source_row)
        self.insertDataRow(target_row, row_data)
        return

    def add_row(self):
        self.insertDataRow(self.rowCount())

    def remove_row(self):
        self.removeRow(self.currentRow())
        self.clearSelection()
        self.setCurrentCell(-1, -1)

    def gen_pinyin(self):
        for x in range(self.rowCount()):
            pnyn = ""
            for i in pinyin(self.item(x,0).text(),style=Style.TONE):
                pnyn += i[0]
            self.item(x,1).setText(pnyn)

class CardUploadProgress(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(250, 50)
        layout = QVBoxLayout(self)
        self.progress = QProgressBar(format="%v / %m")
        layout.addWidget(self.progress)

    def init(self, no_cards: int):
        self.value = 0
        self.progress.setValue(self.value)
        if no_cards > 0: 
            self.no_cards = no_cards
            self.progress.setRange(0, self.no_cards)
            self.show()

    def increment_progress(self):
        self.value += 1
        if self.value > self.no_cards:
            return
        self.progress.setValue(self.value)

class CardUploadWorker(QObject):
    def __init__(self, card_table: CardTable, eng_char_deck: str, char_pnyn_deck: str, tts_type: str):
        self.cancel = False
        super().__init__()
        self.ct = card_table
        self.eng_char_deck = eng_char_deck
        self.char_pnyn_deck = char_pnyn_deck
        self.tts_type = tts_type

    progress = Signal()
    finished = Signal()

    def run(self):
        no_rows = self.ct.rowCount()
        try:
            for i in range(no_rows):
                card_details = create_card(
                    [self.ct.item(i, 0).text(),self.ct.item(i, 1).text(), self.ct.item(i, 2).text()],
                    self.tts_type
                    )
                add_card_with_audio_bytes(
                    deck_name=self.eng_char_deck,
                    front=card_details["eng_to_char"]["front"], 
                    back=card_details["eng_to_char"]["back"],
                    audio_bytes=card_details["audio"],
                    filename=card_details["filename"]
                )
                # Add char to pinyin
                add_card_with_audio_bytes(
                    deck_name=self.char_pnyn_deck,
                    front=card_details["char_to_pnyn"]["front"], 
                    back=card_details["char_to_pnyn"]["back"],
                    audio_bytes=card_details["audio"],
                    filename=card_details["filename"]
                )
                self.progress.emit()
        except Exception as e:
            print(e)
            print("Failed on card:")
            print(card_details)
            self.finished.emit()
        self.finished.emit()
