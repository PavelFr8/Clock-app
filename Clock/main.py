import sqlite3
import sys
import os

from PyQt5 import uic, QtMultimedia, QtCore
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QTableWidgetItem, QDialog, QCheckBox

from datetime import datetime
import pytz

# Словарь с часовыми поясами
ZONES = {
    'Нью Йорк': 'America/New_York',
    'Лондон': 'Europe/London',
    'Сидней': 'Australia/Sydney',
    'Берлин': 'Europe/Berlin',
    'Москва': 'Europe/Moscow',
    'Минск': 'Europe/Minsk',
    'Варшава': 'Europe/Warsaw',
    'Дубай': 'Asia/Dubai',
    'Каир': 'Africa/Cairo',
    'Бангкок': 'Asia/Bangkok',
    'Токио': 'Asia/Tokyo',
    'Буэнос-Айрес': 'America/Argentina/Buenos_Aires',
    'Детройт': 'America/Detroit',
    'Гавана': 'America/Havana',
    'Чита': 'Asia/Chita',
    'Новосибирск': 'Asia/Novosibirsk',
    'Осло': 'Europe/Oslo'
}

# Словарь с музыкальными файлами по умолчанию для будильников
MUSIC = {
    'Прошу тебя': 'music/sound1.wav',
    'Будильник': 'music/sound2.wav',
    'Гармония': 'music/sound3.wav',
    'Бомбический': 'music/sound4.wav',
    'Автоугон': 'music/sound5.wav',
    'Дзынь': 'music/sound6.wav',
    'Своя мелодия': ''
}


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller создает временную папку в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



class AlarmClockDailog(QDialog):
    def __init__(self):
        super(AlarmClockDailog, self).__init__()
        uic.loadUi(resource_path('ui/dialog.ui'), self)

        self.musicbox.addItems(MUSIC.keys())
        self.musicbox.activated.connect(self.music_file)
        self.buttonBox.accepted.connect(self.accept)

    def music_file(self):
        """
        _summary_: Метод для выбора пользовательской музыкальной мелодии.
        """
        if self.sender().currentText() == 'Своя мелодия':
            fname = QFileDialog.getOpenFileName(
                self, 'Выбрать картинку', '',
                'Мелодия (*.mp3);;Мелодия (*.wav)')[0]
            MUSIC[self.sender().currentText()] = fname

    def accept(self):
        """
        _summary_: Метод для обработки нажатия кнопки "Принять" в диалоговом окне.
        """

        def insert_varible_into_table(nm, dt, mus, val=False):
            """
            _summary_: Метод для вставки данных в базу данных.

            Args:
                nm (str): Название будильника.
                dt (str): Дата и время будильника.
                mus (str): Музыка будильника.
                val (bool): Значение, по умолчанию False.
            """
            sqlite_connection = sqlite3.connect('db/db.db')
            cursor = sqlite_connection.cursor()

            # Добавить в базу данных полученные из диалога параметры нового будильника
            sqlite_insert_with_param = """
                                          INSERT INTO Alarms
                                          (name, date, music, value)
                                          VALUES (?, ?, ?, ?);
                                       """

            data_tuple = (nm, dt, mus, val)
            cursor.execute(sqlite_insert_with_param, data_tuple)
            sqlite_connection.commit()
            cursor.close()
            sqlite_connection.close()

        nm = self.nameEdit.text()

        if self.musicbox.currentText() == 'Своя мелодия':
            mus = MUSIC['Своя мелодия']
        else:
            mus = self.musicbox.currentText()

        dt = self.timeEdit.time().toString()
        if nm == '':
            nm = 'Будильник'

        insert_varible_into_table(nm, dt, mus)
        self.close()


# Используйте resource_path для загрузки .ui файлов
class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        uic.loadUi(resource_path('ui/clock.ui'), self)
        # ваш код
        self.alarm_list = []

        # Будильник
        self.connection = sqlite3.connect(resource_path('db/db.db'))

        self.add_button.clicked.connect(self.dialog)
        self.del_button.clicked.connect(self.remove)

        self.tableWidget.setColumnWidth(0, 220)
        self.tableWidget.setColumnWidth(1, 150)
        self.tableWidget.setColumnWidth(2, 300)
        self.tableWidget.setColumnWidth(3, 218)
        self.select_data()

        self.glob_timer = QTimer()
        self.glob_timer.timeout.connect(self.update_glob_timer)
        self.glob_time = QTime()
        self.glob_timer.start()

        # Мировые часы
        self.choosebox.addItems(ZONES.keys())

        curr_timer = QTimer(self)
        curr_timer.timeout.connect(self.update_curr_timer)
        curr_timer.start(1000)
        self.update_curr_timer()

        new_timer = QTimer(self)
        new_timer.timeout.connect(self.world_time)
        new_timer.start(1000)
        self.last_text = ''
        self.world_time()

        # Секундомер
        for button in self.buttonGroup1.buttons():
            button.clicked.connect(self.seconder)

        self.secer = QTimer()
        self.secer.timeout.connect(self.update_seconder)
        self.n = 1

        # Таймер
        for button in self.buttonGroup2.buttons():
            button.clicked.connect(self.time_setter)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.comboBox.addItems(MUSIC.keys())
        self.comboBox.activated.connect(self.musicbox)

    def remove(self):
        """
        _summary_: Метод для удаления выбранного будильника.
        """
        if self.tableWidget.rowCount() > 0 and self.tableWidget.currentRow() >= 0:
            # Получить данные в выбранной строке таблицы.
            currentRow = self.tableWidget.currentRow()
            name = self.tableWidget.item(currentRow, 0).text()
            date = self.tableWidget.item(currentRow, 1).text()
            muz = self.tableWidget.item(currentRow, 2).text()

            # Удалить будильник с этим индексом из базы данных и из списка `alarm_list`.
            if (date, muz) in self.alarm_list:
                self.alarm_list.remove((date, muz))
            self.tableWidget.removeRow(currentRow)
            cur = self.connection.cursor()

            com = """
                      DELETE FROM Alarms 
                      WHERE (name, date, music) = (?, ?, ?); 
                  """

            cur.execute(com, (name, date, muz))
            self.connection.commit()
            # Обновить отображение таблицы.
            self.select_data()

    def dialog(self):
        """
        _summary_: Метод для открытия диалогового окна создания нового будильника.
        """
        # Сохраняем значение последнего элемента
        query1 = """
                    SELECT DISTINCT name, date, music, value FROM Alarms 
                    WHERE ID=(SELECT MAX(id) FROM Alarms)
                 """
        res1 = self.connection.cursor().execute(query1).fetchall()

        # Открыть диалоговое окно.
        dlg = AlarmClockDailog()
        dlg.exec()

        query2 = """
                    SELECT DISTINCT name, date, music, value FROM Alarms 
                    WHERE ID=(SELECT MAX(id) FROM Alarms)
                 """
        res2 = self.connection.cursor().execute(query2).fetchall()

        # Удалить дублированные данные будильника в базе даннных, если был добавден новый будидьник.
        if res1 != res2:
            cur = self.connection.cursor()

            cur.execute("""
                            DELETE FROM Alarms 
                            WHERE ID=(SELECT MAX(id) FROM Alarms)
                        """)

            self.connection.commit()
            # Обновить отображение таблицы.
            self.select_data()

    def select_data(self):
        """
        _summary_: Метод для извлечения данных о будильниках из базы данных и отображения их в таблице.
        """
        # Получить данные о всех будильниках из базы данных.
        query = 'SELECT DISTINCT name, date, music, value FROM Alarms'
        res = self.connection.cursor().execute(query).fetchall()
        self.alarm_list = []
        # Заполним размеры таблиц.
        self.tableWidget.setRowCount(0)
        # Заполняем таблицу элементами.
        for i, row in enumerate(res):
            self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)

            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(row[2])))
            checkbox = QCheckBox()

            # Состояние чекбоксов в зависимости от данных из базы данных
            if int(row[-1]) == 0:
                self.tableWidget.setCellWidget(i, 3, checkbox)
                checkbox.stateChanged.connect(self.value_check)

            if int(row[-1]) == 2:
                checkbox.setChecked(True)
                self.tableWidget.setCellWidget(i, 3, checkbox)
                self.alarm_list.append((row[1], row[2]))
                checkbox.stateChanged.connect(self.value_check)

    def value_check(self, val):
        """
        _summary_: Метод для обработки изменения состояния флажка в таблице для активации/деактивации будильника.

        Args:
            val (int): Значение состояния флажка (0 - деактивировать, 2 - активировать).
        """
        cur = self.connection.cursor()
        row = self.tableWidget.currentRow()
        name = self.tableWidget.item(row, 0).text()
        date = self.tableWidget.item(row, 1).text()
        muz = self.tableWidget.item(row, 2).text()
        itm = (date, muz)

        # Обновить состояние активации/деактивации выбранного будильника в базе данных.
        if val == 2:
            com = """
                      update Alarms
                      set value = 2
                      WHERE (name, date, music) = (?, ?, ?); 
                  """
            self.alarm_list.append(itm)
        if val == 0:
            com = """
                      update Alarms
                      set value = 0
                      WHERE (name, date, music) = (?, ?, ?); 
                  """
            if itm in self.alarm_list:
                self.alarm_list.remove(itm)

        cur.execute(com, (name, date, muz))
        self.connection.commit()

    def load_mp3(self, filename):
        """
        _summary_: Метод для загрузки музыкального файла для воспроизведения.

        Args:
            filename (str): Путь к файлу с музыкой.
        """
        media = QtCore.QUrl.fromLocalFile(filename)
        content = QtMultimedia.QMediaContent(media)
        self.player = QtMultimedia.QMediaPlayer()
        self.player.setMedia(content)

    def musicbox(self):
        """
        _summary_: Метод для выбора пользовательской музыкальной мелодии.
        """
        if self.sender().currentText() == 'Своя мелодия':
            fname = QFileDialog.getOpenFileName(
                self, 'Выбрать картинку', '',
                'Мелодия (*.mp3);;Мелодия (*.wav)')[0]
            MUSIC[self.sender().currentText()] = fname

    def world_time(self):
        """
        _summary_: Метод для отображения текущего времени в выбранном пользователем городе в выбранном часовом поясе на
        отдельном дисплее.
        """
        # Получить выбранный часовой пояс.
        zone = pytz.timezone(ZONES[self.choosebox.currentText()])
        curr_time = datetime.now(zone).strftime("%H:%M")
        curr_time = curr_time.split(':')
        h = int(curr_time[0])
        m = int(curr_time[1])
        time = QTime(h, m)
        text = time.toString('hh:mm')

        if ':' in self.last_text:
            text = text[:2] + ' ' + text[3:]
        if text[0] == '0':
            text = text[1:]

        # Отобразить текущее время в выбранном часовом поясе.
        self.new_lcd.display(text)
        self.last_text = text

    def update_curr_timer(self):
        """
        _summary_: Метод для обновления значения текущего времени и отображения на экране.
        """
        # Получить текущее время.
        time = QTime.currentTime()
        text = time.toString('hh:mm')
        if (time.second() % 2) == 0:
            text = text[:2] + ' ' + text[3:]
        if text[0] == '0':
            text = text[1:]

        # Отобразить текущее время.
        self.cur_lcd.display(text)

    def seconder(self):
        """
        _summary_: Метод для управления секундомером (запуск, остановка, сброс, фиксация времени).
        """
        button = self.sender()
        button_text = button.text()
        # Определить действие в зависимости от текущего состояния секундомера.
        if button_text == 'Старт':
            # Запуск секундомера.
            self.secer.start(100)
            self.start_sec_button.setText('Стоп')
            self.stop_sec_button.setText('Флаг')

        if button_text == 'Сброс':
            # Остановка секундомера, очистка поля с флажками.
            self.secer.stop()
            self.lcd.display('0')
            self.n = 1
            self.flags.setText('')

        if button_text == 'Стоп':
            # Только остановка секундомера.
            self.secer.stop()
            self.start_sec_button.setText('Старт')
            self.stop_sec_button.setText('Сброс')

        if button_text == 'Флаг':
            # Добавление текущего значения секундомера в поле для флажков.
            self.flags.setText(f'{self.flags.text()} \n{self.n}. {round(self.lcd.value(), ndigits=2)}')
            self.n += 1

            if len(self.flags.text().split('\n')) > 9:
                self.flags.setText(self.flags.text().split('\n')[-1])

    def update_seconder(self):
        """
        _summary_: Метод для обновления значения секундомера и отображения на экране.
        """
        times = round(self.lcd.value() + 0.1, ndigits=2)
        self.lcd.display(times)

    def time_setter(self):
        """
        _summary_: Метод для установки и управления таймером (запуск, остановка, сброс).
        """
        button = self.sender()
        button_text = button.text()
        # Определить действие в зависимости от текущего состояния таймера.
        if button_text == 'Старт':
            # Получить значене часов, минут и секунд.
            h = int(self.hours.text())
            m = int(self.minutes.text())
            s = int(self.seconds.text()) + 1

            # Проверка, что значения не превышают возможное значение времени.
            if h > 23:
                h = 23
                self.hours.setValue(23)
            if m > 59:
                m = 59
                self.minutes.setValue(59)
            if s > 59:
                s = 59
                self.seconds.setValue(59)

            if h == 0 and m != 0 and s != 0:
                h = 00
            if h == 0 and m == 0 and s != 0:
                h, m = 00, 00
            if h == 0 and m == 0 and s == 0:
                h, m, s = 00, 00, 1
            self.time = QTime(h, m, s)

            # Запуск таймера.
            self.timer.start(1000)
            self.start_button.setText('Стоп')

        if button_text == 'Продолжить':
            # Запуск таймер после его остановки
            self.timer.start(1000)
            self.start_button.setText('Стоп')

        if button_text == 'Сброс':
            # Сброс значения таймера.
            self.timer.stop()
            self.taimer.setText('00:00:00')
            self.start_button.setText('Старт')

        if button_text == 'Стоп':
            # Остановка таймера
            self.timer.stop()
            self.start_button.setText('Продолжить')

    def update_timer(self):
        """
         _summary_: Метод для обновления значения таймера и отображения на экране, а также воспроизведения музыки по
         истечении времени.
        """
        # Обновить значение таймера и отобразить его на экране.
        self.time = self.time.addSecs(-1)
        self.taimer.setText(self.time.toString("hh:mm:ss"))

        # Если время таймера истекло, воспроизвести музыку.
        if self.time.toString("hh:mm:ss") == '00:00:00':
            self.timer.stop()
            self.load_mp3(MUSIC[self.comboBox.currentText()])
            if MUSIC[self.comboBox.currentText()] == '':
                self.load_mp3('music/angry_developer.wav')
            self.player.play()
            self.comboBox.clear()
            self.comboBox.addItems(MUSIC.keys())
            self.start_button.setText('Старт')

    def update_glob_timer(self):
        """
        _summary_: Метод для обновления глобального таймера, который отслеживает будильники и воспроизводит музыку.
        """
        tmp = datetime.now().strftime('%H:%M').split(':')
        self.glob_time = QTime(int(tmp[0]), int(tmp[1]), 0)
        sp = [elem[0] for elem in self.alarm_list]
        curr_time = str(self.glob_time.toString())

        if curr_time in sp:
            ind = sp.index(curr_time)
            muz = self.alarm_list[ind][1]
            self.alarm_list.remove((curr_time, muz))
            if 'C:' in muz:
                self.load_mp3(muz)
            else:
                self.load_mp3(MUSIC[muz])
            if muz == '':
                self.load_mp3('music/angry_developer.wav')
            self.player.play()


# Функция для отображения исключений
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Window()
    form.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())


