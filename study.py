import flet as ft
import csv
import os
import time
import threading
from datetime import datetime, timedelta

class StudyApp:
    def __init__(self):
        self.filename = "study_data.csv"
        self.running = False
        self.start_time = None
        self.elapsed_seconds = 0

    def format_minutes_to_hrs(self, minutes):
        try:
            m = int(minutes)
            return f"{m // 60}:{m % 60:02d}"
        except: return "0:00"

    def calculate_percent_raw(self, total, correct, wrong):
        try:
            t, c, w = int(total), int(correct), int(wrong)
            if t <= 0: return 0.0
            return ((c * 3) - w) / (t * 3) * 100
        except: return 0.0

    def main(self, page: ft.Page):
        page.title = "دستیار مطالعه هوشمند"
        page.rtl = True
        page.theme_mode = ft.ThemeMode.LIGHT
        # تنظیمات فونت برای اندروید اصلاح شد
        page.theme = ft.Theme(font_family="sans-serif")
        page.scroll = ft.ScrollMode.AUTO

        # ورودی‌ها
        sub_input = ft.TextField(label="نام درس", width=250)
        coeff_input = ft.TextField(label="ضریب", value="1", width=70, text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER)
        time_input = ft.TextField(label="زمان (دقیقه)", width=120, text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER)
        tot_input = ft.TextField(label="کل تست", value="0", width=80, keyboard_type=ft.KeyboardType.NUMBER)
        cor_input = ft.TextField(label="صحیح", value="0", width=80, keyboard_type=ft.KeyboardType.NUMBER)
        wro_input = ft.TextField(label="غلط", value="0", width=80, keyboard_type=ft.KeyboardType.NUMBER)
        
        timer_text = ft.Text("00:00:00", size=50, color="red", weight="bold")
        log_column = ft.Column(spacing=10)

        def timer_thread():
            while self.running:
                try:
                    self.elapsed_seconds = int(time.time() - self.start_time)
                    h, m, s = self.elapsed_seconds // 3600, (self.elapsed_seconds % 3600) // 60, self.elapsed_seconds % 60
                    timer_text.value = f"{h:02d}:{m:02d}:{s:02d}"
                    page.update()
                    time.sleep(1)
                except: break

        def start_study(e):
            if not sub_input.value:
                page.snack_bar = ft.SnackBar(ft.Text("نام درس را وارد کنید"))
                page.snack_bar.open = True
                page.update()
                return
            self.running = True
            self.start_time = time.time()
            btn_start.disabled = True
            btn_stop.disabled = False
            page.update()
            thread = threading.Thread(target=timer_thread, daemon=True)
            thread.start()

        def stop_study(e):
            self.running = False
            btn_start.disabled = False
            btn_stop.disabled = True
            time_input.value = str(max(1, self.elapsed_seconds // 60))
            page.update()

        btn_start = ft.ElevatedButton("شروع مطالعه", on_click=start_study, bgcolor="green", color="white")
        btn_stop = ft.ElevatedButton("توقف تایمر", on_click=stop_study, bgcolor="red", color="white", disabled=True)

        def save_data(e):
            try:
                # تبدیل صریح ورودی‌ها به عدد برای جلوگیری از ارور مقایسه
                s = str(sub_input.value)
                coef = float(coeff_input.value or 1)
                d = int(time_input.value or 0)
                t = int(tot_input.value or 0)
                c = int(cor_input.value or 0)
                w = int(wro_input.value or 0)
                
                date_str = datetime.now().strftime("%Y-%m-%d")
                with open(self.filename, mode='a', newline='', encoding='utf-16') as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerow([date_str, datetime.now().strftime("%H:%M"), s, d, t, c, w, coef])
                
                load_logs()
                # ریست کردن فیلدها
                sub_input.value = ""
                time_input.value = "0"
                tot_input.value = "0"
                cor_input.value = "0"
                wro_input.value = "0"
                coeff_input.value = "1"
                timer_text.value = "00:00:00"
                page.snack_bar = ft.SnackBar(ft.Text("با موفقیت ثبت شد ✅"))
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"خطا در ذخیره سازی!"))
                page.snack_bar.open = True
                page.update()

        def load_logs():
            log_column.controls.clear()
            if os.path.exists(self.filename):
                with open(self.filename, mode='r', encoding='utf-16') as f:
                    rows = list(csv.reader(f, delimiter='\t'))
                    for r in reversed(rows):
                        if len(r) >= 7:
                            p = self.calculate_percent_raw(r[4], r[5], r[6])
                            p_str = f"منفی {abs(p):.1f}%" if p < 0 else f"{p:.1f}%"
                            t_fmt = self.format_minutes_to_hrs(r[3])
                            log_column.controls.append(ft.Container(
                                content=ft.Column([
                                    ft.Text(f"تاریخ: {r[0]}", size=11, color="grey700"),
                                    ft.Text(f"درس: {r[2]} ({t_fmt}) | درصد: {p_str}", size=14, weight="w500"),
                                ], spacing=2),
                                bgcolor="blue50", padding=10, border_radius=8))
            page.update()

        def show_report(days):
            limit = datetime.now() - timedelta(days=days)
            summary = {}
            if os.path.exists(self.filename):
                with open(self.filename, mode='r', encoding='utf-16') as f:
                    for r in csv.reader(f, delimiter='\t'):
                        try:
                            if datetime.strptime(r[0], "%Y-%m-%d") >= limit:
                                sub, dur, tot, c, w = r[2], int(r[3]), int(r[4]), int(r[5]), int(r[6])
                                coef = float(r[7]) if len(r) > 7 else 1.0
                                if sub not in summary: summary[sub] = {'t':0, 'tot':0, 'c':0, 'w':0, 'coef': coef}
                                summary[sub]['t'] += dur
                                summary[sub]['tot'] += tot
                                summary[sub]['c'] += c
                                summary[sub]['w'] += w
                        except: continue

            report_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400, spacing=10)
            for sub, d in sorted(summary.items(), key=lambda x: x[1]['t'], reverse=True):
                p = self.calculate_percent_raw(d['tot'], d['c'], d['w'])
                weighted_score = p * d['coef']
                p_str = f"منفی {abs(p):.1f}%" if p < 0 else f"{p:.1f}%"
                report_list.controls.append(ft.Container(
                    content=ft.Column([
                        ft.Text(f"درس: {sub} (ضریب: {d['coef']})", weight="bold", size=16),
                        ft.Text(f"زمان کل: {self.format_minutes_to_hrs(d['t'])} | درصد: {p_str}"),
                        ft.Text(f"نمره وزنی: {weighted_score:.1f}", color="blue", weight="bold")
                    ], spacing=2), padding=10, border=ft.border.all(1, "grey300"), border_radius=10))

            dlg = ft.AlertDialog(
                title=ft.Text(f"گزارش {days} روزه"),
                content=ft.Container(content=report_list, width=400),
                actions=[ft.TextButton("بستن", on_click=lambda _: setattr(dlg, "open", False) or page.update())]
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        page.add(ft.Column([
            ft.Text("دستیار مطالعه و تست", size=25, weight="bold", color="blue"),
            timer_text, 
            ft.Row([btn_start, btn_stop], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Row([sub_input, coeff_input], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([time_input, ft.Text("دقیقه")], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([tot_input, cor_input, wro_input], alignment=ft.MainAxisAlignment.CENTER),
            ft.ElevatedButton("ذخیره اطلاعات", on_click=save_data, bgcolor="blue", color="white", width=200, height=45),
            ft.Row([
                ft.ElevatedButton("گزارش ۷ روزه", on_click=lambda _: show_report(7)), 
                ft.ElevatedButton("گزارش ۳۰ روزه", on_click=lambda _: show_report(30))
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text("آخرین فعالیت‌ها", weight="bold"),
            log_column
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        load_logs()

if __name__ == "__main__":
    ft.app(target=StudyApp().main)

