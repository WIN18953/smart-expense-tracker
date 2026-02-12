from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
import json


# ---------- Database ----------
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return []


def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)


# ---------- Screens ----------
class HomeScreen(Screen):
    def on_enter(self):
        self.update_summary()

    def update_summary(self):
        data = load_data()
        income = sum(item["amount"] for item in data if item["type"] == "income")
        expense = sum(item["amount"] for item in data if item["type"] == "expense")
        balance = income - expense

        self.ids.income_label.text = f"Income: {income}"
        self.ids.expense_label.text = f"Expense: {expense}"
        self.ids.balance_label.text = f"Balance: {balance}"


class AddScreen(Screen):
    pass


class ReportScreen(Screen):
    pass


class SettingScreen(Screen):
    pass


class ExpenseApp(App):
    def build(self):
        return Builder.load_file("expense.kv")


if __name__ == "__main__":
    ExpenseApp().run()
