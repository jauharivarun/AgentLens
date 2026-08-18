import csv
from collections import defaultdict

def main():
    with open('uploads/2025_sales_transactions.csv', newline='') as f:
        reader = csv.DictReader(f)
        total_rev = 0.0
        total_gp = 0.0
        region_rev = defaultdict(float)
        prod_rev = defaultdict(float)
        city_rev = defaultdict(float)
        segment_rev = defaultdict(float)
        category_rev = defaultdict(float)
        category_gp = defaultdict(float)
        for row in reader:
            rev = float(row['Revenue_INR'])
            gp = float(row['Gross_Profit_INR'])
            total_rev += rev
            total_gp += gp
            region_rev[row['Region']] += rev
            prod_rev[row['Product']] += rev
            city_rev[row['City']] += rev
            segment_rev[row['Customer_Segment']] += rev
            category_rev[row['Category']] += rev
            category_gp[row['Category']] += gp
        # results
        print(f"Total_Revenue,{total_rev}")
        print(f"Total_Gross_Profit,{total_gp}")
        top_region = max(region_rev.items(), key=lambda x: x[1])
        print(f"Top_Region,{top_region[0]},{top_region[1]}")
        top_prod = max(prod_rev.items(), key=lambda x: x[1])
        print(f"Top_Product,{top_prod[0]},{top_prod[1]}")
        top_city = max(city_rev.items(), key=lambda x: x[1])
        print(f"Top_City,{top_city[0]},{top_city[1]}")
        top_segment = max(segment_rev.items(), key=lambda x: x[1])
        print(f"Top_Segment,{top_segment[0]},{top_segment[1]}")
        # category margins
        margins = {cat: (category_gp[cat]/category_rev[cat]*100 if category_rev[cat]>0 else 0) for cat in category_rev}
        top_category = max(margins.items(), key=lambda x: x[1])
        print(f"Top_Category_Margin,{top_category[0]},{top_category[1]}")

if __name__ == '__main__':
    main()