from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel 
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
import sys
import json
        
class Main(QMainWindow):
    def __init__(self):
        super(Main, self).__init__()
        loadUi("main.ui", self)

        # Загрузка конфигурационного файла
        try: 
            with open("config.json") as file:
                config = json.load(file)
        except: QMessageBox.critical(self, "ОШИБКА", "ФАЙЛА КОНФИГУРАЦИИ НЕ СУЩЕСТВУЕТ")

        # Подключение к базе данных
        db = QSqlDatabase.addDatabase("QPSQL")
        db.setHostName(config["host"])
        db.setPort(config["port"])
        db.setDatabaseName(config["database"])
        db.setUserName(config["username"])
        db.setPassword(config["password"])

        if db.open():
            self.statusBar().showMessage('Успешное подключение к базе данных')
            print("Успешное подключение к базе данных")
        else:
            QMessageBox.critical(self, "ОШИБКА", "Ошибка подключения к базе данных.\n Рекомендуется проверить файл конфигурации")
            print("Ошибка подключения к базе данных")

        self.model = QSqlTableModel()
        self.load_table('Недвижимость')
    
        self.tableView.setModel(self.model)

        self.fill_city_combobox()
        self.fill_table_combobox()
        self.searchButton.clicked.connect(self.on_search_button_clicked)
        self.tableComboBox.activated.connect(self.on_push_button_clicked)
        self.action_2.triggered.connect(self.add_row)
        self.action_4.triggered.connect(self.save_to_database)
        self.action_3.triggered.connect(self.remove_from_database)


    def add_row(self):
        self.model.insertRow(self.model.rowCount())


    def save_to_database(self):
        lastRow = self.model.rowCount() - 1
        columnCount = self.model.columnCount()
        values = []
        columnName = []
        for column in range(columnCount):
            currentCellIndex = self.model.index(lastRow, column)
            currentValue = self.model.data(currentCellIndex, Qt.DisplayRole)
            values.append(currentValue)

        selectedValue = self.tableComboBox.currentText()
        
        for column in range(columnCount):
            columnName.append(self.model.headerData(column, Qt.Horizontal, Qt.DisplayRole))
        values_str = f"INSERT INTO {selectedValue} ({', '.join(columnName)}) VALUES ({values})"
        print(values_str)
        values_str = values_str.replace("[","")
        values_str = values_str.replace("]","")
        query = values_str
        q = QSqlQuery()
        q.prepare(query)
        result = q.exec()
        if result:
            print("Запрос выполнен успешно")
            self.statusBar().showMessage('Данные успешно добавлены!')
        else:
            QMessageBox.warning(self, "Ошибка", "Ошибка выполнения запроса: "+q.lastError().text())
        self.model.setQuery(q)
        self.load_table(selectedValue)
        
        

    def remove_from_database(self):
        selectedValue = self.tableComboBox.currentText()
        selectionModel = self.tableView.selectionModel()
        indexes = selectionModel.selectedIndexes()
        if indexes:
            currentColumn = indexes[0].column()
            currentRow = indexes[0].row()
            columnHeader = self.tableView.model().headerData(currentColumn, Qt.Horizontal)
            model = self.tableView.model()
            currentCellIndex = model.index(currentRow, currentColumn)
            currentValue = model.data(currentCellIndex, Qt.DisplayRole)

        valuestr = f"DELETE FROM {selectedValue} WHERE {columnHeader}={currentValue};"
        q = QSqlQuery()
        q.prepare(valuestr)
        result = q.exec()
        self.load_table(selectedValue)
        if result:
            print("Запрос выполнен успешно")
            self.statusBar().showMessage('Данные успешно удалены!')
        else:
            QMessageBox.warning(self, "Ошибка", "Ошибка выполнения запроса: "+q.lastError().text())

    def fill_table_combobox(self):
        # Получение списка имен таблиц из базы данных
        tables = self.model.database().tables()

        # Заполнение QComboBox значениями
        self.tableComboBox.addItems(tables)
        self.tableComboBox.setCurrentText('Недвижимость')

    def fill_city_combobox(self):
        # Запрос для получения уникальных значений столбца City
        query = "SELECT DISTINCT Город FROM Недвижимость"
        result = self.execute_query(query)

        # Заполнение QComboBox значениями
        for row in result:
            city = row[0]
            self.cityComboBox.addItem(city)

    def on_push_button_clicked(self):
         self.load_table(self.tableComboBox.currentText())

    def on_search_button_clicked(self):
        if self.tableComboBox.currentText() != 'Недвижимость':
            QMessageBox.about(self, "Внимание", "Поиск возможен только по таблице Недвижимость")
            return
        else:    
            # Получение значений из полей
            city = self.cityComboBox.currentText()
            min_s = self.minAreaLineEdit.text()
            max_s = self.maxAreaLineEdit.text()
            min_rooms = self.minRoomsLineEdit.text()
            max_rooms = self.maxRoomsLineEdit.text()
            max_price = self.maxPriceLineEdit.text()

        # Проверка на пустые поля
        if min_s == ''  or max_s == '' or min_rooms == '' or max_rooms == '' or max_price == '':
            QMessageBox.warning(self, "Внимание", "Заполните все поля.")
            return

        self.search_table(city, min_s, max_s, min_rooms, max_rooms, max_price)
   
    def load_table(self,table):
        q = QSqlQuery()
        q.prepare(f'SELECT * FROM {table}')
        q.exec_()
        self.model.setQuery(q)

    def execute_query(self, query):
        db = QSqlDatabase.database()
        query = QSqlQuery(query, db)
        result = []
        while query.next():
            row = []
            for i in range(query.record().count()):
                row.append(query.value(i))
            result.append(row)
        return result

    def search_table(self, city, min_s, max_s, min_rooms, max_rooms, max_price):
        # Запрос для поиска недвижимости с заданными параметрами
        query = f"""
                    SELECT Адресс, Город, Цена, Комнаты, Ванные_комнаты, Площадь, Описание 
                    FROM Недвижимость
                    WHERE Город = '{city}' AND Площадь BETWEEN ? AND ? AND Комнаты BETWEEN ? AND ? AND Цена <= ?
                """
        print(query)
        # Создание QSqlQuery и установка параметров
        q = QSqlQuery()
        q.prepare(query)
        q.bindValue(0, float(min_s))
        q.bindValue(1, float(max_s))
        q.bindValue(2, int(min_rooms))
        q.bindValue(3, int(max_rooms))
        q.bindValue(4, float(max_price))
     
        # Выполнение запроса
        if q.exec_():
            self.model.clear()
            self.model.setQuery(q)
            self.model.select()

            # Вывод результатов
            if self.model.rowCount() > 0:
                self.statusBar().showMessage("Успешно найдено " + str(self.model.rowCount()) + " строк")
            else:
                print("По вашим критериям ничего не найдено.")
                QMessageBox.warning(self, "Внимание", "По вашим критериям ничего не найдено.")
        else:
            print("Ошибка выполнения запроса:", q.lastError().text())
            QMessageBox.warning(self, "Ошибка", f"Ошибка выполнения запроса: {q.lastError().text()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Main()
    ui.show()
    sys.exit(app.exec_())