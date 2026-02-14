from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.button import Button
import json

# ---------- Database ----------
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- Screens ----------
class HomeScreen(Screen):
    # เรียกครั้งแรกหลังจาก kv ของหน้า Home ถูก apply ครบแล้ว -> ids พร้อมแน่นอน
    def on_kv_post(self, base_widget):
        self.refresh()

    # เวลา "กลับเข้า" หน้านี้ ให้ดีเลย์ 0 เฟรม เพื่อรอ layout คำนวณขนาดเสร็จ
    def on_enter(self, *args):
        Clock.schedule_once(lambda dt: self.refresh(), 0)

    # รวมงานอัปเดตไว้ที่เดียว
    def refresh(self):
        self.update_summary()
        self.display_transactions()

    def update_summary(self):
        data = load_data()
        income = sum(item["amount"] for item in data if item.get("type") == "income")
        expense = sum(item["amount"] for item in data if item.get("type") == "expense")
        balance = income - expense

        # --- แก้ไขตรงนี้ ---
        # ใส่แค่ตัวเลข (และจัดฟอร์แมตใส่ลูกน้ำด้วย {:,.2f})
        if "income_label" in self.ids:
            self.ids.income_label.text = f"{income:,.2f}"
        if "expense_label" in self.ids:
            self.ids.expense_label.text = f"{expense:,.2f}"
        if "balance_label" in self.ids:
            self.ids.balance_label.text = f"{balance:,.2f}"

    def display_transactions(self):
        container = self.ids.get("transaction_list")
        if not container:
            return

        container.clear_widgets()
        data = load_data()

        for index, item in enumerate(data):
            text = f"{item.get('type','')}  {item.get('amount','')}  {item.get('category','')}"
            btn = Button(
                text=text,
                size_hint_y=None,
                height=dp(40),
                halign='left',
                valign='middle'
            )
            # ให้ข้อความชิดซ้ายและไม่ล้นเมื่อปรับขนาดหน้าต่าง
            btn.text_size = (btn.width - dp(24), None)
            btn.bind(width=lambda inst, w: setattr(inst, 'text_size', (w - dp(24), None)))

            btn.bind(on_press=lambda instance, i=index: self.delete_transaction(i))
            container.add_widget(btn)

    def delete_transaction(self, index):
        data = load_data()
        if 0 <= index < len(data):
            data.pop(index)
            save_data(data)
            self.refresh()

class AddScreen(Screen):
    def save_transaction(self):
        amount_text = self.ids.amount_input.text.strip()
        note = self.ids.note_input.text.strip()
        t_type = self.ids.type_spinner.text.strip()   # "Income" หรือ "Expense"
        category = self.ids.category_spinner.text.strip()
        date = self.ids.date_input.text.strip()       # เช่น "2026-02" หรือ "2026-02-14"

        if not amount_text:
            return
        try:
            amount = float(amount_text)
        except ValueError:
            return

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
    def on_enter(self, *args):
        self.load_months()

    def load_months(self):
        data = load_data()
        # unique เดือน/วันที่มีข้อมูล และไม่เป็นค่าว่าง
        months = sorted({item.get("date") for item in data if item.get("date")})
        if months and self.ids.get("month_spinner"):
            self.ids.month_spinner.values = months
            self.ids.month_spinner.text = months[0]

    def filter_report(self):
        selected_month = self.ids.month_spinner.text
        data = load_data()
        filtered = [item for item in data if item.get("date") == selected_month]
        income = sum(item["amount"] for item in filtered if item.get("type") == "income")
        expense = sum(item["amount"] for item in filtered if item.get("type") == "expense")
        balance = income - expense

        if self.ids.get("report_income"):
            self.ids.report_income.text = f"Income: {income}"
        if self.ids.get("report_expense"):
            self.ids.report_expense.text = f"Expense: {expense}"
        if self.ids.get("report_balance"):
            self.ids.report_balance.text = f"Balance: {balance}"

class SettingScreen(Screen):
    pass

class ExpenseApp(App):
    def build(self):
        pass

if __name__ == "__main__":
    # สร้างไฟล์ data.json เริ่มต้นถ้ายังไม่มี
    try:
        open("data.json", "x", encoding="utf-8").write("[]")
    except FileExistsError:
        pass
    ExpenseApp().run()