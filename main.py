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

    def save_transaction(self):
        amount_text = self.ids.amount_input.text
        note = self.ids.note_input.text
        t_type = self.ids.type_spinner.text
        category = self.ids.category_spinner.text
        date = self.ids.date_input.text

        # ตรวจสอบว่าใส่จำนวนเงินไหม
        if amount_text == "":
            return

        amount = float(amount_text)

        data = load_data()

        data.append({
            "amount": amount,
            "note": note,
            "type": "income" if t_type == "Income" else "expense",
            "category": category,
            "date": date
        })

        save_data(data)

        # เคลียร์ช่องกรอก
        self.ids.amount_input.text = ""
        self.ids.note_input.text = ""

        # กลับหน้า home
        self.manager.current = "home"



class ReportScreen(Screen):
    pass


class SettingScreen(Screen):
    pass


class ExpenseApp(App):
    def build(self):
        return Builder.load_file("expense.kv")


if __name__ == "__main__":
    ExpenseApp().run()
