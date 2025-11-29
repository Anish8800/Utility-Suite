import json
import os
import datetime
import uuid
from collections import defaultdict
from difflib import get_close_matches

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None  # charts optional; code will check

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.json")
EXPENSES_FILE = os.path.join(DATA_DIR, "expenses.json")

DEFAULT_CATEGORIES = [
    {"id": "cat_groceries", "name": "Groceries", "is_default": True, "budget": None},
    {"id": "cat_transport", "name": "Transportation", "is_default": True, "budget": None},
    {"id": "cat_entertainment", "name": "Entertainment", "is_default": True, "budget": None},
    {"id": "cat_utilities", "name": "Utilities", "is_default": True, "budget": None},
    {"id": "cat_rent", "name": "Rent", "is_default": True, "budget": None},
    {"id": "cat_health", "name": "Health", "is_default": True, "budget": None},
    {"id": "cat_other", "name": "Other", "is_default": True, "budget": None},
]

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

class CategoryManager:
    def __init__(self):
        ensure_data_dir()
        self.categories = load_json(CATEGORIES_FILE, DEFAULT_CATEGORIES.copy())
        # Ensure default categories are present (idempotent)
        existing_names = {c["name"].lower() for c in self.categories}
        for d in DEFAULT_CATEGORIES:
            if d["name"].lower() not in existing_names:
                self.categories.append(d)
        self._commit()

    def _commit(self):
        save_json(CATEGORIES_FILE, self.categories)

    def list_categories(self):
        return sorted(self.categories, key=lambda c: (not c.get("is_default", False), c["name"].lower()))

    def find_by_id(self, cat_id):
        for c in self.categories:
            if c["id"] == cat_id:
                return c
        return None

    def find_by_name(self, name):
        for c in self.categories:
            if c["name"].lower() == name.lower():
                return c
        return None

    def add_category(self, name, budget=None):
        if self.find_by_name(name):
            raise ValueError(f"Category '{name}' already exists.")
        new_cat = {
            "id": "cat_" + uuid.uuid4().hex[:8],
            "name": name,
            "is_default": False,
            "budget": float(budget) if budget is not None else None
        }
        self.categories.append(new_cat)
        self._commit()
        return new_cat

    def edit_category(self, cat_id, new_name=None, new_budget=None):
        c = self.find_by_id(cat_id)
        if not c:
            raise ValueError("Category ID not found.")
        if new_name:
            if any(cc["name"].lower() == new_name.lower() and cc["id"] != cat_id for cc in self.categories):
                raise ValueError("Another category with that name exists.")
            c["name"] = new_name
        if new_budget is not None:
            c["budget"] = float(new_budget) if new_budget != "" else None
        self._commit()
        return c

    def remove_category(self, cat_id):
        c = self.find_by_id(cat_id)
        if not c:
            raise ValueError("Category ID not found.")
        if c.get("is_default"):
            raise ValueError("Cannot remove a default category.")
        self.categories = [cc for cc in self.categories if cc["id"] != cat_id]
        self._commit()

    def suggest(self, text, n=5):
        names = [c["name"] for c in self.categories]
        return get_close_matches(text, names, n=n, cutoff=0.2)

class ExpenseManager:
    def __init__(self, category_manager: CategoryManager):
        ensure_data_dir()
        self.catman = category_manager
        self.expenses = load_json(EXPENSES_FILE, [])
        # normalize dates
        for e in self.expenses:
            if isinstance(e.get("date"), str):
                try:
                    e["date"] = datetime.datetime.fromisoformat(e["date"])
                except Exception:
                    e["date"] = datetime.datetime.now()
        self._commit()

    def _commit(self):
        # convert datetime to isoformat strings for JSON
        serializable = []
        for e in self.expenses:
            copy = e.copy()
            if isinstance(copy.get("date"), datetime.datetime):
                copy["date"] = copy["date"].isoformat()
            serializable.append(copy)
        save_json(EXPENSES_FILE, serializable)

    def add_expense(self, amount, date, category_id, description=""):
        if not self.catman.find_by_id(category_id):
            raise ValueError("Invalid category selected.")
        try:
            amount = float(amount)
        except ValueError:
            raise ValueError("Amount must be a number.")
        if isinstance(date, str):
            date = datetime.datetime.fromisoformat(date)
        expense = {
            "id": "exp_" + uuid.uuid4().hex[:10],
            "amount": amount,
            "date": date,
            "category_id": category_id,
            "description": description
        }
        self.expenses.append(expense)
        self._commit()
        # budget alert
        cat = self.catman.find_by_id(category_id)
        if cat and cat.get("budget") is not None:
            total = self.total_for_category(category_id)
            if total > cat["budget"]:
                print(f"ALERT: You have exceeded the budget for category '{cat['name']}'. Budget: {cat['budget']}, Current total: {total:.2f}")
        return expense

    def list_expenses(self, start_date=None, end_date=None, category_id=None):
        results = []
        for e in self.expenses:
            edate = e["date"]
            if isinstance(edate, str):
                try:
                    edate = datetime.datetime.fromisoformat(edate)
                except Exception:
                    edate = datetime.datetime.now()
            if start_date and edate < start_date:
                continue
            if end_date and edate > end_date:
                continue
            if category_id and e["category_id"] != category_id:
                continue
            results.append(e.copy())
        # sort by date desc
        results.sort(key=lambda x: x["date"], reverse=True)
        return results

    def total_for_category(self, category_id):
        total = 0.0
        for e in self.expenses:
            if e["category_id"] == category_id:
                amt = e["amount"]
                total += float(amt)
        return total

    def summary_by_category(self):
        sums = defaultdict(float)
        counts = defaultdict(int)
        for e in self.expenses:
            cid = e["category_id"]
            sums[cid] += float(e["amount"])
            counts[cid] += 1
        categories = []
        grand_total = sum(sums.values())
        for c in self.catman.list_categories():
            cid = c["id"]
            total = sums.get(cid, 0.0)
            cnt = counts.get(cid, 0)
            avg = (total / cnt) if cnt > 0 else 0.0
            categories.append({
                "id": cid,
                "name": c["name"],
                "total": total,
                "count": cnt,
                "average": avg,
                "budget": c.get("budget"),
                "percent_of_total": (total / grand_total * 100) if grand_total > 0 else 0.0
            })
        # sort by total desc
        categories.sort(key=lambda x: x["total"], reverse=True)
        return {"grand_total": grand_total, "categories": categories}

    def category_with_highest(self):
        summary = self.summary_by_category()["categories"]
        if not summary:
            return None
        return max(summary, key=lambda x: x["total"])

    def category_with_lowest(self):
        summary = self.summary_by_category()["categories"]
        if not summary:
            return None
        return min(summary, key=lambda x: x["total"])

    def visualize_category_totals(self, output_path="category_totals.png"):
        if plt is None:
            raise RuntimeError("matplotlib is not available in this environment.")
        summary = self.summary_by_category()["categories"]
        names = [c["name"] for c in summary if c["total"] > 0]
        totals = [c["total"] for c in summary if c["total"] > 0]
        if not names:
            raise ValueError("No data to plot.")
        fig, ax = plt.subplots()
        ax.bar(names, totals)
        ax.set_title("Spending by Category")
        ax.set_ylabel("Amount")
        ax.set_xticklabels(names, rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path

    def pie_chart(self, output_path="category_pie.png"):
        if plt is None:
            raise RuntimeError("matplotlib is not available in this environment.")
        summary = self.summary_by_category()["categories"]
        names = [c["name"] for c in summary if c["total"] > 0]
        totals = [c["total"] for c in summary if c["total"] > 0]
        if not names:
            raise ValueError("No data to plot.")
        fig, ax = plt.subplots()
        ax.pie(totals, labels=names, autopct="%1.1f%%")
        ax.set_title("Spending Distribution by Category")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path
    
    def pie_chart(self, output_path="category_pie.png"):
        if plt is None:
            raise RuntimeError("matplotlib is not available in this environment.")
        summary = self.summary_by_category()["categories"]
        names = [c["name"] for c in summary if c["total"] > 0]
        totals = [c["total"] for c in summary if c["total"] > 0]
        if not names:
            raise ValueError("No data to plot.")
        fig, ax = plt.subplots()
        ax.pie(totals, labels=names, autopct="%1.1f%%")
        ax.set_title("Spending Distribution by Category")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path

    def export_to_excel(self, path: str):
        import pandas as pd
        df = pd.DataFrame([{
            "id": e["id"],
            "date": e["date"].strftime("%Y-%m-%d") if isinstance(e["date"], datetime.datetime) else str(e["date"]),
            "amount": e["amount"],
            "description": e.get("description", ""),
            "category": self.catman.find_by_id(e["category_id"])["name"] if self.catman.find_by_id(e["category_id"]) else "Unknown"
        } for e in self.expenses])
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Expenses")
        return path
    
def parse_date_input(text):
    text = text.strip().lower()
    if text in ("", "today"):
        return datetime.datetime.now()
    try:
        # try ISO
        return datetime.datetime.fromisoformat(text)
    except Exception:
        # try common formats
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(text, fmt)
            except Exception:
                pass
    raise ValueError("Unrecognized date format. Use YYYY-MM-DD or leave blank for today.")

def print_expense(e, catman):
    date = e["date"]
    if isinstance(date, str):
        try:
            date = datetime.datetime.fromisoformat(date)
        except Exception:
            date = date
    cid = e["category_id"]
    cat = catman.find_by_id(cid)
    print(f"- ID: {e['id']} | {date.strftime('%Y-%m-%d %H:%M')} | {cat['name'] if cat else 'Unknown'} | {e['amount']:.2f} | {e.get('description','')}")

def cli_main():
    catman = CategoryManager()
    expman = ExpenseManager(catman)

    MENU = """
Expense Tracker - Menu
1. List categories
2. Add category
3. Edit category
4. Remove category
5. Add expense
6. List expenses
7. Summary by category
8. Show highest/lowest category
9. Visualize category totals (PNG)
10. Set / Clear budget for a category
11. Export to Excel (.xlsx)
0. Exit
Enter choice: """

    while True:
        choice = input(MENU).strip()
        if choice == "1":
            print("Categories:")
            for c in catman.list_categories():
                print(f"- ID: {c['id']} | Name: {c['name']} | Budget: {c.get('budget')}")
        elif choice == "2":
            name = input("New category name: ").strip()
            if not name:
                print("Name cannot be empty.")
                continue
            suggestions = catman.suggest(name)
            if suggestions:
                print("Did you mean one of these existing categories? ", suggestions)
            budget = input("Optional budget (amount) - leave blank for none: ").strip()
            try:
                newc = catman.add_category(name, budget if budget != "" else None)
                print("Added category:", newc)
            except Exception as e:
                print("Error adding category:", e)
        elif choice == "3":
            cid = input("Category ID to edit: ").strip()
            new_name = input("New name (leave blank to keep): ").strip()
            new_budget = input("New budget (leave blank to clear / keep blank): ").strip()
            try:
                updated = catman.edit_category(cid, new_name if new_name != "" else None, new_budget if new_budget != "" else None)
                print("Updated:", updated)
            except Exception as e:
                print("Error editing category:", e)
        elif choice == "4":
            cid = input("Category ID to remove: ").strip()
            try:
                catman.remove_category(cid)
                print("Category removed.")
            except Exception as e:
                print("Error removing category:", e)
        elif choice == "5":
            amount = input("Amount: ").strip()
            date_in = input("Date (YYYY-MM-DD) or leave blank for today: ").strip()
            try:
                date = parse_date_input(date_in) if date_in != "" else datetime.datetime.now()
            except Exception as e:
                print("Invalid date:", e)
                continue
            print("Choose a category by typing its name (partial allowed) or ID:")
            for c in catman.list_categories():
                print(f"- {c['id']} : {c['name']}")
            cat_input = input("Category name or ID: ").strip()
            chosen = None
            # if input matches ID
            if catman.find_by_id(cat_input):
                chosen = cat_input
            else:
                # try exact name
                f = catman.find_by_name(cat_input)
                if f:
                    chosen = f["id"]
                else:
                    # suggestions
                    suggestions = catman.suggest(cat_input)
                    if suggestions:
                        print("Suggestions:", suggestions)
                        # try to pick first match by name
                        matched = catman.find_by_name(suggestions[0])
                        if matched:
                            chosen = matched["id"]
                    else:
                        print("No matching category found.")
            if not chosen:
                print("Could not resolve category. Aborting adding expense.")
                continue
            desc = input("Description (optional): ").strip()
            try:
                exp = expman.add_expense(amount, date, chosen, desc)
                print("Added expense:")
                print_expense(exp, catman)
            except Exception as e:
                print("Error adding expense:", e)
        elif choice == "6":
            cfilter = input("Filter by category ID (leave blank for all): ").strip()
            sdate = input("Start date (YYYY-MM-DD) or leave blank: ").strip()
            edate = input("End date (YYYY-MM-DD) or leave blank: ").strip()
            try:
                sd = parse_date_input(sdate) if sdate != "" else None
                ed = parse_date_input(edate) if edate != "" else None
            except Exception as e:
                print("Invalid date:", e)
                continue
            results = expman.list_expenses(start_date=sd, end_date=ed, category_id=cfilter if cfilter != "" else None)
            if not results:
                print("No expenses found.")
            for e in results:
                print_expense(e, catman)
        elif choice == "7":
            summary = expman.summary_by_category()
            print(f"Grand total: {summary['grand_total']:.2f}")
            for c in summary["categories"]:
                print(f"- {c['name']}: Total={c['total']:.2f}, Count={c['count']}, Avg={c['average']:.2f}, Percent={c['percent_of_total']:.1f}%, Budget={c.get('budget')}")
        elif choice == "8":
            high = expman.category_with_highest()
            low = expman.category_with_lowest()
            if high:
                print("Highest:", high["name"], f"Total={high['total']:.2f}")
            if low:
                print("Lowest:", low["name"], f"Total={low['total']:.2f}")
        elif choice == "9":
            out = input("Output filename (e.g. cat_totals.png) or leave blank for default: ").strip()
            out = out if out != "" else "category_totals.png"
            try:
                path = expman.visualize_category_totals(output_path=os.path.join(DATA_DIR, out))
                print("Saved bar chart to:", path)
                p2 = expman.pie_chart(output_path=os.path.join(DATA_DIR, "category_pie.png"))
                print("Saved pie chart to:", p2)
            except Exception as e:
                print("Visualization error:", e)
        elif choice == "10":
            print("Set or clear budget for a category. Current categories:")
            for c in catman.list_categories():
                print(f"- ID: {c['id']} | {c['name']} | Budget: {c.get('budget')}")
            cid = input("Category ID: ").strip()
            if not catman.find_by_id(cid):
                print("Category not found.")
                continue
            b = input("New budget amount (leave blank to clear): ").strip()
            try:
                catman.edit_category(cid, None, b if b != "" else None)
                print("Budget updated.")
            except Exception as e:
                print("Error updating budget:", e)
        elif choice == "11":
                path = input("Enter Excel export path (e.g., data/expenses.xlsx): ").strip()
                expman.export_to_excel(path)
                print("Exported to Excel.")

        
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    cli_main()
