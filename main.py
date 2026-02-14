from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
import json
from datetime import datetime
import matplotlib.pyplot as plt
import io
from kivy.core.image import Image as CoreImage

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
        """ดึงรายการเดือน/ปี ที่มีทั้งหมดจากฐานข้อมูล"""
        data = load_data()
        months = set()
        
        for item in data:
            date_str = item.get("date", "")
            # รองรับ format DD/MM/YYYY
            parts = date_str.split('/')
            if len(parts) == 3:
                month_year = f"{parts[1]}/{parts[2]}" # เก็บเป็น MM/YYYY
                months.add(month_year)
        
        # เรียงลำดับเดือน (ล่าสุดขึ้นก่อน)
        sorted_months = sorted(list(months), reverse=True)
        
        # อัปเดต Spinner (ถ้ามี widget ชื่อ month_filter)
        if "month_filter" in self.ids:
            current_selection = self.ids.month_filter.text
            self.ids.month_filter.values = ["All Time"] + sorted_months
            # ถ้าค่าที่เลือกอยู่เดิมไม่มีในลิสต์ใหม่ ให้รีเซ็ตเป็น All Time
            if current_selection not in self.ids.month_filter.values:
                self.ids.month_filter.text = "All Time"

    def filter_data_by_month(self):
        """คัดกรองข้อมูลตามเดือนที่เลือก"""
        data = load_data()
        
        # เช็คว่ามี Spinner หรือไม่ (กัน Error)
        if "month_filter" not in self.ids:
            return data

        selected_month = self.ids.month_filter.text
        
        if selected_month == "All Time":
            return data
            
        filtered_data = []
        for item in data:
            date_str = item.get("date", "")
            parts = date_str.split('/')
            if len(parts) == 3:
                item_month_year = f"{parts[1]}/{parts[2]}"
                if item_month_year == selected_month:
                    filtered_data.append(item)
                    
        return filtered_data

    def refresh(self, *args):
        # 1. กรองข้อมูลก่อน
        filtered_data = self.filter_data_by_month()
        
        # 2. ส่งข้อมูลที่กรองแล้วไป update UI
        self.update_summary(filtered_data)
        self.display_transactions(filtered_data)

    def update_summary(self, data):
        income = sum(item["amount"] for item in data if item.get("type") == "income")
        expense = sum(item["amount"] for item in data if item.get("type") == "expense")
        balance = income - expense

        if "income_label" in self.ids:
            self.ids.income_label.text = f"{income:,.2f}"
        if "expense_label" in self.ids:
            self.ids.expense_label.text = f"{expense:,.2f}"
        if "balance_label" in self.ids:
            self.ids.balance_label.text = f"{balance:,.2f}"

    def display_transactions(self, data):
        container = self.ids.get("transaction_list")
        if not container:
            return

        container.clear_widgets()
        # ใช้ data ที่ส่งเข้ามา (ซึ่งถูกกรองแล้ว) แทนการโหลดใหม่
        
        # แสดงผลแบบย้อนกลับ (รายการล่าสุดอยู่บน)
        for index, item in enumerate(reversed(data)):
            # คำนวณ index จริงใน database (สำหรับการลบ)
            # หมายเหตุ: การลบขณะกรองอาจซับซ้อน นี่เป็นวิธีเบื้องต้น
            real_index = len(data) - 1 - index 

            note = item.get('note', '')
            date = item.get('date', '')
            t_type = item.get('type', '')
            amount = item.get('amount', 0)
            category = item.get('category', '')
            
            # จัดรูปแบบข้อความให้สวยงามขึ้น
            text = f"{date} | {t_type} {amount:,.2f} | {category} | {note}"

            btn = Button(
                text=text,
                size_hint_y=None,
                height=dp(50),
                halign='left',
                valign='middle'
            )
            
            btn.text_size = (btn.width - dp(24), None)
            btn.bind(width=lambda inst, w: setattr(inst, 'text_size', (w - dp(24), None)))
            
            # ส่ง real_index ไปฟังก์ชันลบ (ระวัง: ถ้ากรองอยู่ index อาจคลาดเคลื่อนได้ 
            # แต่เพื่อให้โปรแกรมรันได้ก่อน ใช้แบบนี้ไปก่อนครับ)
            btn.bind(on_press=lambda instance, i=real_index: self.delete_transaction(i))
            container.add_widget(btn)

    def delete_transaction(self, index):
        # ข้อควรระวัง: การลบโดยใช้ index ขณะกรองข้อมูลอาจลบผิดตัวได้
        # เพื่อความปลอดภัย เบื้องต้นจะให้ลบได้เฉพาะตอนเลือก "All Time" หรือต้องแก้ระบบ ID
        if self.ids.month_filter.text != "All Time":
            print("Cannot delete while filtering (Safety feature)")
            return

        data = load_data()
        # ต้องกลับด้าน index เพราะเราแสดงผลแบบ reversed
        # รายการที่ 0 บนหน้าจอ คือรายการสุดท้ายใน list data
        actual_index = len(data) - 1 - index

        if 0 <= actual_index < len(data):
            data.pop(actual_index)
            save_data(data)
            self.refresh()

class AddScreen(Screen):
    def save_transaction(self):
        amount_text = self.ids.amount_input.text.strip()
        note = self.ids.note_input.text.strip()
        t_type = self.ids.type_spinner.text.strip()
        category = self.ids.category_spinner.text.strip()
        date_text = self.ids.date_input.text.strip()

        if not amount_text:
            return
        try:
            amount = float(amount_text)
        except ValueError:
            return

        # ถ้าไม่ได้กรอกวันที่ ให้ใส่วันที่ปัจจุบัน
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

        # เคลียร์ช่องกรอก
        self.ids.amount_input.text = ""
        self.ids.note_input.text = ""
        self.ids.date_input.text = ""

        # กลับหน้า home
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
            self.ids.month_spinner.values = sorted_months
            # เลือกเดือนล่าสุดอัตโนมัติ และเรียก filter_report
            if self.ids.month_spinner.text not in sorted_months:
                self.ids.month_spinner.text = sorted_months[0]
            else:
                self.filter_report()

    def filter_report(self):
        if "month_spinner" not in self.ids:
            return

        selected_month = self.ids.month_spinner.text
        data = load_data()
        
        # 1. กรองข้อมูล
        filtered = []
        for item in data:
            d = item.get("date", "")
            parts = d.split('/')
            if len(parts) == 3:
                if f"{parts[1]}/{parts[2]}" == selected_month:
                    filtered.append(item)

        # 2. คำนวณยอด
        income = sum(item["amount"] for item in filtered if item.get("type") == "income")
        expense = sum(item["amount"] for item in filtered if item.get("type") == "expense")
        balance = income - expense

        # 3. อัปเดตตารางตัวเลข
        if "report_income" in self.ids:
            self.ids.report_income.text = f"{income:,.2f}"
        if "report_expense" in self.ids:
            self.ids.report_expense.text = f"{expense:,.2f}"
        if "report_balance" in self.ids:
            self.ids.report_balance.text = f"{balance:,.2f}"

        # 4. สร้างกราฟ
        self.generate_chart(income, expense)

    def generate_chart(self, income, expense):
        # ตั้งค่าสีและธีมให้เข้ากับแอป (Dark Theme)
        plt.clf() # เคลียร์กราฟเก่า
        fig = plt.figure(figsize=(5, 4), facecolor='#121212') # พื้นหลังนอกกราฟ
        ax = plt.gca()
        ax.set_facecolor('#121212') # พื้นหลังในกราฟ

        # ข้อมูลกราฟ
        categories = ['Income', 'Expense']
        values = [income, expense]
        colors = ['#00E676', '#FF5252'] # เขียว, แดง

        # วาดกราฟแท่ง
        bars = plt.bar(categories, values, color=colors, width=0.5)

        # ปรับแต่งตัวหนังสือ
        plt.title('Income vs Expense', color='white', fontsize=14, pad=20)
        plt.xticks(color='white')
        plt.yticks(color='white')
        
        # ลบเส้นขอบกราฟเพื่อให้ดูมินิมอล
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#444444')
        ax.spines['left'].set_color('#444444')

        # ใส่ตัวเลขบนแท่งกราฟ
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2.0, height,
                     f'{height:,.0f}',
                     ha='center', va='bottom', color='white')

        # แปลงกราฟเป็นรูปภาพเพื่อส่งให้ Kivy
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight') # เซฟลง Memory
        buf.seek(0)
        
        # โหลดเข้า Image Widget
        texture = CoreImage(buf, ext='png').texture
        self.ids.chart_image.texture = texture
        
        plt.close(fig) # ปิดกราฟเพื่อคืน Ram

class SettingScreen(Screen):
    pass

class ExpenseApp(App):
    def build(self):
        pass
if __name__ == "__main__":
    try:
        open("data.json", "x", encoding="utf-8").write("[]")
    except FileExistsError:
        pass
    ExpenseApp().run()