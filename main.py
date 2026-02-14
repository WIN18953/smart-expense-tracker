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
        self.display_transactions()

    def update_summary(self):
        data = load_data()
        income = sum(item["amount"] for item in data if item["type"] == "income")
        expense = sum(item["amount"] for item in data if item["type"] == "expense")
        balance = income - expense

        self.ids.income_label.text = f"Income: {income}"
        self.ids.expense_label.text = f"Expense: {expense}"
        self.ids.balance_label.text = f"Balance: {balance}"

    def display_transactions(self):
        data = load_data()
        container = self.ids.transaction_list
        container.clear_widgets()

        for index, item in enumerate(data):
            text = f"{item['type']} | {item['amount']} | {item['category']}"
            from kivy.uix.button import Button

            btn = Button(
                text=text,
                size_hint_y=None,
                height=40
            )

            btn.bind(on_press=lambda instance, i=index: self.delete_transaction(i))
            container.add_widget(btn)

    def delete_transaction(self, index):
        data = load_data()
        if index < len(data):
            data.pop(index)
            save_data(data)

        self.update_summary()
        self.display_transactions()


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

    def on_enter(self):
        self.load_months()

    def load_months(self):
        data = load_data()
        months = list(set(item["date"] for item in data if item["date"] != ""))
        if months:
            self.ids.month_spinner.values = months
            self.ids.month_spinner.text = months[0]

    def filter_report(self):
        selected_month = self.ids.month_spinner.text
        data = load_data()

        filtered = [item for item in data if item["date"] == selected_month]

        income = sum(item["amount"] for item in filtered if item["type"] == "income")
        expense = sum(item["amount"] for item in filtered if item["type"] == "expense")
        balance = income - expense

        self.ids.report_income.text = f"Income: {income}"
        self.ids.report_expense.text = f"Expense: {expense}"
        self.ids.report_balance.text = f"Balance: {balance}"



class SettingScreen(Screen):
    pass


class ExpenseApp(App):
    def build(self):
        return Builder.load_file("expense.kv")


if __name__ == "__main__":
    ExpenseApp().run()
