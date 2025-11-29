import os
import json
import uuid
import datetime
from collections import defaultdict
from difflib import get_close_matches
import csv
import tempfile

# Optional libraries
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog, filedialog
except Exception:
    tk = None
try:
    import matplotlib
    matplotlib.use("Agg")  # Use non-interactive backend for file output
    import matplotlib.pyplot as plt
except Exception:
    plt = None
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
except Exception:
    canvas = None
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.json")
EXPENSES_FILE = os.path.join(DATA_DIR, "expenses.json")

DEFAULT_CATEGORIES = [
    {"id": "cat_groceries", "name": "Groceries", "is_default": True, "budget": None, "group": "Food"},
    {"id": "cat_restaurant", "name": "Restaurants", "is_default": True, "budget": None, "group": "Food"},
    {"id": "cat_transport", "name": "Transportation", "is_default": True, "budget": None, "group": "Travel"},
    {"id": "cat_entertainment", "name": "Entertainment", "is_default": True, "budget": None, "group": "Lifestyle"},
    {"id": "cat_utilities", "name": "Utilities", "is_default": True, "budget": None, "group": "Bills"},
    {"id": "cat_rent", "name": "Rent", "is_default": True, "budget": None, "group": "Housing"},
    {"id": "cat_health", "name": "Health", "is_default": True, "budget": None, "group": "Health"},
    {"id": "cat_other", "name": "Other", "is_default": True, "budget": None, "group": "Other"},
]

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

class CategoryManager:
    def __init__(self):
        ensure_dirs()
        self.categories = load_json(CATEGORIES_FILE, DEFAULT_CATEGORIES.copy())
        existing = {c["name"].lower() for c in self.categories}
        for d in DEFAULT_CATEGORIES:
            if d["name"].lower() not in existing:
                self.categories.append(d)
        self._commit()

    def _commit(self):
        save_json(CATEGORIES_FILE, self.categories)

    def list_categories(self):
        return sorted(self.categories, key=lambda c: (not c.get("is_default", False), c["name"].lower()))

    def find_by_id(self, cid):
        for c in self.categories:
            if c["id"] == cid:
                return c
        return None

    def find_by_name(self, name):
        for c in self.categories:
            if c["name"].lower() == name.lower():
                return c
        return None

    def add_category(self, name, group=None, budget=None):
        if self.find_by_name(name):
            raise ValueError("Category already exists.")
        newc = {"id": "cat_" + uuid.uuid4().hex[:8], "name": name, "is_default": False, "budget": float(budget) if budget not in (None,"") else None, "group": group or "Other"}
        self.categories.append(newc)
        self._commit()
        return newc

    def edit_category(self, cid, new_name=None, new_group=None, new_budget=None):
        c = self.find_by_id(cid)
        if not c:
            raise ValueError("Not found")
        if new_name:
            if any(cc["name"].lower() == new_name.lower() and cc["id"] != cid for cc in self.categories):
                raise ValueError("Duplicate name exists")
            c["name"] = new_name
        if new_group is not None:
            c["group"] = new_group
        if new_budget is not None:
            c["budget"] = float(new_budget) if new_budget != "" else None
        self._commit()
        return c

    def remove_category(self, cid):
        c = self.find_by_id(cid)
        if not c:
            raise ValueError("Not found")
        if c.get("is_default"):
            raise ValueError("Cannot remove default")
        self.categories = [cc for cc in self.categories if cc["id"] != cid]
        self._commit()

    def suggest(self, text, n=5):
        names = [c["name"] for c in self.categories]
        return get_close_matches(text, names, n=n, cutoff=0.2)

class ExpenseManager:
    def __init__(self, catman: CategoryManager):
        ensure_dirs()
        self.catman = catman
        self.expenses = load_json(EXPENSES_FILE, [])
        # Normalize dates to ISO strings stored; internal operations can parse
        for e in self.expenses:
            if isinstance(e.get("date"), str):
                try:
                    # keep ISO
                    pass
                except Exception:
                    e["date"] = datetime.datetime.now().isoformat()
        self._commit()

    def _commit(self):
        save_json(EXPENSES_FILE, self.expenses)

    def add_expense(self, amount, date, category_id, description="", recurring=False):
        if not self.catman.find_by_id(category_id):
            raise ValueError("Invalid category")
        try:
            amount = float(amount)
        except:
            raise ValueError("Invalid amount")
        if isinstance(date, datetime.datetime):
            date_iso = date.isoformat()
        elif isinstance(date, str):
            # assume ISO or YYYY-MM-DD
            try:
                _ = datetime.datetime.fromisoformat(date)
                date_iso = date
            except:
                date_iso = datetime.datetime.now().isoformat()
        else:
            date_iso = datetime.datetime.now().isoformat()
        exp = {
            "id": "exp_" + uuid.uuid4().hex[:10],
            "amount": amount,
            "date": date_iso,
            "category_id": category_id,
            "description": description,
            "recurring": bool(recurring)
        }
        self.expenses.append(exp)
        self._commit()
        # budget checks
        cat = self.catman.find_by_id(category_id)
        if cat and cat.get("budget") is not None:
            total = self.total_for_category(category_id)
            perc = (total/cat["budget"]*100) if cat["budget"] else 0
            if perc >= 100:
                print(f"🚨 Budget exceeded for {cat['name']}. Spent {total:.2f} / {cat['budget']:.2f}")
            elif perc >= 80:
                print(f"⚠ Approaching budget for {cat['name']}: {perc:.1f}% used.")
        return exp

    def list_expenses(self, start_date=None, end_date=None, category_id=None, group=None):
        results = []
        sd = None; ed = None
        if start_date:
            if isinstance(start_date, str):
                sd = datetime.datetime.fromisoformat(start_date)
            else:
                sd = start_date
        if end_date:
            if isinstance(end_date, str):
                ed = datetime.datetime.fromisoformat(end_date)
            else:
                ed = end_date
        for e in self.expenses:
            edate = datetime.datetime.fromisoformat(e["date"])
            if sd and edate < sd:
                continue
            if ed and edate > ed:
                continue
            if category_id and e["category_id"] != category_id:
                continue
            if group:
                cat = self.catman.find_by_id(e["category_id"])
                if not cat or cat.get("group") != group:
                    continue
            results.append(e.copy())
        results.sort(key=lambda x: x["date"], reverse=True)
        return results

    def total_for_category(self, cid):
        total = 0.0
        for e in self.expenses:
            if e["category_id"] == cid:
                total += float(e["amount"])
        return total

    def summary_by_category(self):
        sums = defaultdict(float); counts = defaultdict(int)
        for e in self.expenses:
            cid = e["category_id"]
            sums[cid] += float(e["amount"])
            counts[cid] += 1
        cats = []
        grand = sum(sums.values())
        for c in self.catman.list_categories():
            cid = c["id"]
            total = sums.get(cid, 0.0)
            cnt = counts.get(cid, 0)
            avg = (total/cnt) if cnt else 0.0
            cats.append({
                "id": cid, "name": c["name"], "total": total, "count": cnt, "average": avg, "budget": c.get("budget"), "group": c.get("group"),
                "percent_of_total": (total/grand*100) if grand>0 else 0.0
            })
        cats.sort(key=lambda x: x["total"], reverse=True)
        return {"grand_total": grand, "categories": cats}

    def category_with_highest(self):
        cats = self.summary_by_category()["categories"]
        return max(cats, key=lambda x: x["total"]) if cats else None

    def category_with_lowest(self):
        cats = self.summary_by_category()["categories"]
        return min(cats, key=lambda x: x["total"]) if cats else None

    def export_csv(self, filename):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID","Amount","Date","Category","Description","Recurring"])
            for e in self.expenses:
                cat = self.catman.find_by_id(e["category_id"])
                writer.writerow([e["id"], e["amount"], e["date"], cat["name"] if cat else "Unknown", e.get("description",""), e.get("recurring",False)])

    def recurring_rollover(self, months=1):
        # Create copies of recurring expenses shifted by 'months'
        added = []
        for e in list(self.expenses):
            if e.get("recurring"):
                orig_date = datetime.datetime.fromisoformat(e["date"])
                # naive month add
                month = orig_date.month -1 + months
                year = orig_date.year + month//12
                month = month%12 +1
                day = min(orig_date.day, 28)
                new_date = datetime.datetime(year, month, day, orig_date.hour, orig_date.minute)
                newe = e.copy()
                newe["id"] = "exp_" + uuid.uuid4().hex[:10]
                newe["date"] = new_date.isoformat()
                self.expenses.append(newe)
                added.append(newe)
        if added:
            self._commit()
        return added

    def plot_category_totals(self, outfile):
        if plt is None:
            raise RuntimeError("matplotlib missing")
        summary = self.summary_by_category()["categories"]
        names = [c["name"] for c in summary if c["total"]>0]
        totals = [c["total"] for c in summary if c["total"]>0]
        if not names:
            raise ValueError("No data")
        fig, ax = plt.subplots()
        ax.bar(names, totals)
        ax.set_title("Spending by Category")
        ax.set_ylabel("Amount")
        ax.set_xticklabels(names, rotation=45, ha="right")
        plt.tight_layout()
        fig.savefig(outfile)
        plt.close(fig)
        return outfile

    def pie_chart(self, outfile):
        if plt is None:
            raise RuntimeError("matplotlib missing")
        summary = self.summary_by_category()["categories"]
        names = [c["name"] for c in summary if c["total"]>0]
        totals = [c["total"] for c in summary if c["total"]>0]
        if not names:
            raise ValueError("No data")
        fig, ax = plt.subplots()
        ax.pie(totals, labels=names, autopct="%1.1f%%")
        ax.set_title("Spending Distribution by Category")
        plt.tight_layout()
        fig.savefig(outfile)
        plt.close(fig)
        return outfile

    def generate_monthly_pdf_report(self, year, month, outfile):
        if canvas is None:
            raise RuntimeError("reportlab missing")
        # filter expenses for that month
        sd = datetime.datetime(year, month, 1)
        if month==12:
            ed = datetime.datetime(year+1,1,1)
        else:
            ed = datetime.datetime(year, month+1,1)
        items = self.list_expenses(start_date=sd, end_date=ed)
        summary = defaultdict(float)
        for e in items:
            cid = e["category_id"]
            summary[cid] += float(e["amount"])
        c = canvas.Canvas(outfile, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawString(20*mm, height-20*mm, f"Monthly Expense Report - {year}-{month:02d}")
        c.setFont("Helvetica", 10)
        c.drawString(20*mm, height-25*mm, f"Generated: {datetime.datetime.now().isoformat()}")
        # table header
        y = height-35*mm
        c.drawString(20*mm, y, "Category")
        c.drawString(100*mm, y, "Total")
        y -= 6*mm
        grand = 0.0
        for cid, amt in sorted(summary.items(), key=lambda x: x[1], reverse=True):
            cat = self.catman.find_by_id(cid)
            name = cat["name"] if cat else "Unknown"
            c.drawString(20*mm, y, name)
            c.drawRightString(120*mm, y, f"{amt:.2f}")
            y -= 6*mm
            grand += amt
            if y < 20*mm:
                c.showPage()
                y = height-20*mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20*mm, y-4*mm, f"Grand Total: {grand:.2f}")
        c.save()
        return outfile

############# Tkinter GUI #############

class ExpenseGUI:
    def __init__(self, root):
        if tk is None:
            raise RuntimeError("Tkinter not available in this environment.")
        self.root = root
        root.title("Expense Tracker - GUI")
        self.catman = CategoryManager()
        self.expman = ExpenseManager(self.catman)
        self.create_widgets()
        self.refresh_category_dropdown()

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        # Add expense form
        ttk.Label(frm, text="Add Expense", font=("Helvetica", 12, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(frm, text="Amount:").grid(row=1, column=0, sticky="e")
        self.amount_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.amount_var).grid(row=1, column=1, sticky="w")

        ttk.Label(frm, text="Date (YYYY-MM-DD):").grid(row=1, column=2, sticky="e")
        self.date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(frm, textvariable=self.date_var).grid(row=1, column=3, sticky="w")

        ttk.Label(frm, text="Category:").grid(row=2, column=0, sticky="e")
        self.category_cb = ttk.Combobox(frm, state="readonly")
        self.category_cb.grid(row=2, column=1, sticky="w")

        ttk.Button(frm, text="Add Expense", command=self.add_expense_clicked).grid(row=2, column=3, sticky="w")

        ttk.Label(frm, text="Description:").grid(row=3, column=0, sticky="e")
        self.desc_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.desc_var, width=50).grid(row=3, column=1, columnspan=3, sticky="w")

        # Expense list
        ttk.Label(frm, text="Recent Expenses", font=("Helvetica", 12, "bold")).grid(row=4, column=0, columnspan=4, sticky="w", pady=(10,0))
        self.tree = ttk.Treeview(frm, columns=("date","category","amount","desc"), show="headings", height=8)
        self.tree.heading("date", text="Date"); self.tree.heading("category", text="Category"); self.tree.heading("amount", text="Amount"); self.tree.heading("desc", text="Description")
        self.tree.grid(row=5, column=0, columnspan=4, sticky="nsew")
        self.refresh_expense_list()

        # Controls panel
        ctrl = ttk.Frame(self.root, padding=10)
        ctrl.grid(row=0, column=1, sticky="nsew")
        ttk.Button(ctrl, text="Manage Categories", command=self.open_category_window).grid(row=0, column=0, sticky="ew", pady=2)
        ttk.Button(ctrl, text="Show Charts (Bar + Pie)", command=self.show_charts).grid(row=1, column=0, sticky="ew", pady=2)
        ttk.Button(ctrl, text="Export CSV", command=self.export_csv).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Button(ctrl, text="Generate Monthly PDF", command=self.generate_pdf_dialog).grid(row=3, column=0, sticky="ew", pady=2)
        ttk.Button(ctrl, text="Recurring Rollover (next month)", command=self.recurring_rollover).grid(row=4, column=0, sticky="ew", pady=2)
        ttk.Button(ctrl, text="Summary by Category (console)", command=self.print_summary_console).grid(row=5, column=0, sticky="ew", pady=2)
        ttk.Button(ctrl, text="Quit", command=self.root.quit).grid(row=6, column=0, sticky="ew", pady=10)

    def refresh_category_dropdown(self):
        cats = self.catman.list_categories()
        self.category_map = {f"{c['name']} ({c.get('group','')})": c["id"] for c in cats}
        self.category_cb["values"] = list(self.category_map.keys())
        if self.category_map:
            self.category_cb.current(0)

    def refresh_expense_list(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        recent = self.expman.list_expenses()
        for e in recent[:50]:
            cat = self.catman.find_by_id(e["category_id"])
            cname = cat["name"] if cat else "Unknown"
            self.tree.insert("", "end", values=(e["date"][:10], cname, f"{e['amount']:.2f}", e.get("description","")))

    def add_expense_clicked(self):
        amt = self.amount_var.get().strip()
        date_s = self.date_var.get().strip()
        desc = self.desc_var.get().strip()
        cat_display = self.category_cb.get()
        if not amt:
            messagebox.showerror("Error","Amount is required")
            return
        if not cat_display or cat_display not in self.category_map:
            # try suggestions
            suggestions = self.catman.suggest(cat_display)
            if suggestions:
                use = messagebox.askyesno("Suggestion", f"Did you mean '{suggestions[0]}'?")
                if use:
                    cat = self.catman.find_by_name(suggestions[0])
                    cat_id = cat["id"]
                else:
                    messagebox.showerror("Error","Please select a valid category.")
                    return
            else:
                messagebox.showerror("Error","Please select a valid category.")
                return
        else:
            cat_id = self.category_map[cat_display]
        # parse date
        try:
            date = datetime.datetime.fromisoformat(date_s)
        except Exception:
            try:
                date = datetime.datetime.strptime(date_s, "%Y-%m-%d")
            except Exception:
                messagebox.showerror("Error","Invalid date format. Use YYYY-MM-DD")
                return
        try:
            self.expman.add_expense(amt, date, cat_id, desc, recurring=False)
            messagebox.showinfo("Success","Expense added")
            self.refresh_expense_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_category_window(self):
        win = tk.Toplevel(self.root)
        win.title("Manage Categories")
        frm = ttk.Frame(win, padding=10); frm.pack(fill="both", expand=True)
        tree = ttk.Treeview(frm, columns=("name","group","budget","id"), show="headings")
        tree.heading("name", text="Name"); tree.heading("group", text="Group"); tree.heading("budget", text="Budget"); tree.heading("id", text="ID")
        tree.pack(fill="both", expand=True)
        for c in self.catman.list_categories():
            tree.insert("", "end", values=(c["name"], c.get("group",""), c.get("budget",""), c["id"]))
        def add_cat():
            name = simpledialog.askstring("New Category","Name:", parent=win)
            if not name: return
            group = simpledialog.askstring("Group","Group (e.g., Food, Bills):", parent=win) or "Other"
            budget = simpledialog.askstring("Budget","Optional budget amount (blank for none):", parent=win)
            try:
                self.catman.add_category(name, group=group, budget=budget if budget!="" else None)
                messagebox.showinfo("Added","Category added")
                win.destroy(); self.refresh_category_dropdown()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        def edit_cat():
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0])["values"]
            cid = vals[3]
            newname = simpledialog.askstring("Edit Name","New name (blank to keep):", parent=win)
            newgroup = simpledialog.askstring("Edit Group","New group (blank to keep):", parent=win)
            newbudget = simpledialog.askstring("Edit Budget","New budget (blank to clear):", parent=win)
            try:
                self.catman.edit_category(cid, newname if newname!="" else None, newgroup if newgroup!="" else None, newbudget if newbudget!="" else None)
                messagebox.showinfo("Updated","Category updated")
                win.destroy(); self.refresh_category_dropdown()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        def remove_cat():
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0])["values"]
            cid = vals[3]
            try:
                self.catman.remove_category(cid)
                messagebox.showinfo("Removed","Category removed")
                win.destroy(); self.refresh_category_dropdown()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        btns = ttk.Frame(frm); btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Add", command=add_cat).pack(side="left", padx=4)
        ttk.Button(btns, text="Edit", command=edit_cat).pack(side="left", padx=4)
        ttk.Button(btns, text="Remove", command=remove_cat).pack(side="left", padx=4)

    def show_charts(self):
        # create charts and display saved PNGs in a new window
        bar_file = os.path.join(DATA_DIR, "category_totals.png")
        pie_file = os.path.join(DATA_DIR, "category_pie.png")
        try:
            self.expman.plot_category_totals(bar_file)
            self.expman.pie_chart(pie_file)
        except Exception as e:
            messagebox.showerror("Chart error", str(e))
            return
        win = tk.Toplevel(self.root); win.title("Charts")
        frm = ttk.Frame(win, padding=10); frm.pack(fill="both", expand=True)
        if Image and ImageTk:
            try:
                img1 = Image.open(bar_file); img1.thumbnail((600,400))
                ph1 = ImageTk.PhotoImage(img1)
                lbl1 = ttk.Label(frm, image=ph1); lbl1.image = ph1; lbl1.pack()
                img2 = Image.open(pie_file); img2.thumbnail((400,400))
                ph2 = ImageTk.PhotoImage(img2)
                lbl2 = ttk.Label(frm, image=ph2); lbl2.image = ph2; lbl2.pack()
            except Exception as e:
                ttk.Label(frm, text=f"Could not render images: {e}").pack()
        else:
            ttk.Label(frm, text=f"Charts saved to:\n{bar_file}\n{pie_file}").pack()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")], initialdir=DATA_DIR)
        if not path: return
        try:
            self.expman.export_csv(path)
            messagebox.showinfo("Exported", f"CSV exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def generate_pdf_dialog(self):
        if canvas is None:
            messagebox.showerror("Missing dependency","reportlab not installed. Install with `pip install reportlab`")
            return
        dlg = simpledialog.askstring("Monthly Report","Enter year-month (YYYY-MM), e.g. 2025-11", parent=self.root)
        if not dlg: return
        try:
            y,m = dlg.split("-")
            y = int(y); m = int(m)
        except:
            messagebox.showerror("Error","Invalid format")
            return
        outfile = os.path.join(REPORTS_DIR, f"report_{y}_{m:02d}.pdf")
        try:
            self.expman.generate_monthly_pdf_report(y,m,outfile)
            messagebox.showinfo("Report", f"Saved PDF to {outfile}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def recurring_rollover(self):
        added = self.expman.recurring_rollover(months=1)
        messagebox.showinfo("Recurring", f"Added {len(added)} recurring expenses for next month.")
        self.refresh_expense_list()

    def print_summary_console(self):
        s = self.expman.summary_by_category()
        print(f"Grand total: {s['grand_total']:.2f}")
        for c in s["categories"]:
            print(f"- {c['name']}: Total={c['total']:.2f}, Count={c['count']}, Avg={c['average']:.2f}, Percent={c['percent_of_total']:.1f}%")
        messagebox.showinfo("Summary", "Summary printed to console.")

def main():
    ensure_dirs()
    if tk is None:
        print("Tkinter not available. Run in environment with GUI support.")
        return
    root = tk.Tk()
    app = ExpenseGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
