from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ColorProperty, StringProperty
from kivy.utils import get_color_from_hex
import json
from datetime import datetime
import matplotlib.pyplot as plt
import io
import csv
import os
from kivy.core.image import Image as CoreImage

# ---------- Custom Widget (สำหรับแสดงใน KV) ----------
class TransactionItem(BoxLayout):
    text_content = StringProperty("")
    indicator_color = ColorProperty([1, 1, 1, 1])

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
    def on_kv_post(self, base_widget):
        self.load_month_list() 
        self.refresh()

    def on_enter(self, *args):
        self.load_month_list()
        Clock.schedule_once(lambda dt: self.refresh(), 0)

    def load_month_list(self):
        data = load_data()
        months = set()
        for item in data:
            date_str = item.get("date", "")
            parts = date_str.split('/')
            if len(parts) == 3:
                months.add(f"{parts[1]}/{parts[2]}")
        
        sorted_months = sorted(list(months), reverse=True)
        
        if "month_filter" in self.ids:
            current = self.ids.month_filter.text
            self.ids.month_filter.values = ["All Time"] + sorted_months
            if current not in self.ids.month_filter.values:
                self.ids.month_filter.text = "All Time"

    def filter_data_by_month(self):
        data = load_data()
        if "month_filter" not in self.ids: return data
        
        selected = self.ids.month_filter.text
        if selected == "All Time": return data
            
        filtered = []
        for item in data:
            d = item.get("date", "")
            parts = d.split('/')
            if len(parts) == 3:
                if f"{parts[1]}/{parts[2]}" == selected:
                    filtered.append(item)
        return filtered

    def refresh(self, *args):
        filtered_data = self.filter_data_by_month()
        self.update_summary(filtered_data)
        self.display_transactions(filtered_data)

    def update_summary(self, data):
        income = sum(item["amount"] for item in data if item.get("type") == "income")
        expense = sum(item["amount"] for item in data if item.get("type") == "expense")
        balance = income - expense

        if "income_label" in self.ids: self.ids.income_label.text = f"{income:,.2f}"
        if "expense_label" in self.ids: self.ids.expense_label.text = f"{expense:,.2f}"
        if "balance_label" in self.ids: self.ids.balance_label.text = f"{balance:,.2f}"

    def display_transactions(self, data):
        container = self.ids.get("transaction_list")
        if not container:
            return

        container.clear_widgets()
        
        for index, item in enumerate(reversed(data)):
            # ดึงข้อมูล
            note = item.get('note', '')
            date = item.get('date', '')
            t_type = item.get('type', '')
            amount = item.get('amount', 0)
            category = item.get('category', '')
            
            # จัดข้อความและสี
            if t_type == "income":
                color = get_color_from_hex('#00E676') # เขียว
                sign = "+"
            else:
                color = get_color_from_hex('#FF5252') # แดง
                sign = "-"
            
            full_text = f"{date} | {t_type} {sign}{amount:,.2f} | {category} | {note}"

            # สร้าง Widget รายการแบบสวยงาม (แทนปุ่มธรรมดา)
            item_widget = TransactionItem(
                text_content=full_text,
                indicator_color=color
            )
            container.add_widget(item_widget)

    def delete_transaction(self, index):
        # ฟีเจอร์ลบปิดไว้ก่อนชั่วคราวเพื่อให้ UI สวยงาม (ต้องทำปุ่มลบแยก)
        pass

class AddScreen(Screen):
    def save_transaction(self):
        amount_text = self.ids.amount_input.text.strip()
        note = self.ids.note_input.text.strip()
        t_type = self.ids.type_spinner.text.strip()
        category = self.ids.category_spinner.text.strip()
        date_text = self.ids.date_input.text.strip()

        if not amount_text: return
        try:
            amount = float(amount_text)
        except ValueError: return

        if not date_text:
            date_text = datetime.now().strftime("%d/%m/%Y")

        data = load_data()
        data.append({
            "amount": amount,
            "note": note,
            "type": "income" if t_type == "Income" else "expense",
            "category": category,
            "date": date_text
        })
        save_data(data)

        self.ids.amount_input.text = ""
        self.ids.note_input.text = ""
        self.ids.date_input.text = ""
        self.manager.current = "home"

class ReportScreen(Screen):
    def on_enter(self, *args):
        self.load_months()

    def load_months(self):
        data = load_data()
        months = set()
        for item in data:
            d = item.get("date", "")
            parts = d.split('/')
            if len(parts) == 3:
                months.add(f"{parts[1]}/{parts[2]}")
        
        sorted_months = sorted(list(months), reverse=True)
        if sorted_months and "month_spinner" in self.ids:
            if self.ids.month_spinner.text not in sorted_months:
                self.ids.month_spinner.values = sorted_months
                self.ids.month_spinner.text = sorted_months[0]
            else:
                self.ids.month_spinner.values = sorted_months
                self.filter_report()

    def filter_report(self):
        if "month_spinner" not in self.ids: return
        selected = self.ids.month_spinner.text
        data = load_data()
        
        filtered = []
        for item in data:
            d = item.get("date", "")
            parts = d.split('/')
            if len(parts) == 3:
                if f"{parts[1]}/{parts[2]}" == selected:
                    filtered.append(item)

        income = sum(item["amount"] for item in filtered if item.get("type") == "income")
        expense = sum(item["amount"] for item in filtered if item.get("type") == "expense")
        balance = income - expense

        if "report_income" in self.ids: self.ids.report_income.text = f"{income:,.2f}"
        if "report_expense" in self.ids: self.ids.report_expense.text = f"{expense:,.2f}"
        if "report_balance" in self.ids: self.ids.report_balance.text = f"{balance:,.2f}"

        self.generate_chart(income, expense)

    def generate_chart(self, income, expense):
        plt.clf()
        # ใช้สีดำให้เข้ากับธีม
        fig = plt.figure(figsize=(5, 4), facecolor='#121212') 
        ax = plt.gca()
        ax.set_facecolor('#121212')

        categories = ['Income', 'Expense']
        values = [income, expense]
        colors = ['#00E676', '#FF5252']

        bars = plt.bar(categories, values, color=colors, width=0.5)

        plt.title('Income vs Expense', color='white', fontsize=14, pad=20)
        plt.xticks(color='white')
        plt.yticks(color='white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#888888')
        ax.spines['left'].set_color('#888888')

        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2.0, height,
                     f'{height:,.0f}', ha='center', va='bottom', color='white')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        texture = CoreImage(buf, ext='png').texture
        self.ids.chart_image.texture = texture
        plt.close(fig)

class SettingScreen(Screen):
    def clear_data(self):
        save_data([]) 
        print("Data Cleared!")
        self.manager.current = "home"
        self.manager.get_screen('home').refresh()

    def export_data(self):
        data = load_data()
        if not data: return
        filename = "expense_export.csv"
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Type", "Category", "Amount", "Note"])
                for item in data:
                    writer.writerow([
                        item.get("date", ""), item.get("type", ""),
                        item.get("category", ""), item.get("amount", ""),
                        item.get("note", "")
                    ])
            print(f"Exported to {os.path.abspath(filename)}")
        except Exception as e:
            print(f"Error export: {e}")

class ExpenseApp(App):
    def build(self):
        pass

if __name__ == "__main__":
    try:
        open("data.json", "x", encoding="utf-8").write("[]")
    except FileExistsError:
        pass
    ExpenseApp().run()