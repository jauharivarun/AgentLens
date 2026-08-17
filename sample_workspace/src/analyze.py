import csv
from collections import defaultdict

with open('uploads/2025_sales_transactions.csv') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Q1: highest-revenue region
region_rev = defaultdict(float)
for r in rows:
    region_rev[r['Region']] += float(r['Revenue_INR'])
best_region = max(region_rev, key=region_rev.get)
print(f'Q1 Highest-revenue region: {best_region} = {region_rev[best_region]:,.2f}')
for k, v in sorted(region_rev.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v:,.2f}')

# Q2: city with highest revenue
city_rev = defaultdict(float)
for r in rows:
    city_rev[r['City']] += float(r['Revenue_INR'])
best_city = max(city_rev, key=city_rev.get)
print(f'Q2 Highest-revenue city: {best_city} = {city_rev[best_city]:,.2f}')

# Q3: quarter with highest revenue
qtr_rev = defaultdict(float)
for r in rows:
    qtr_rev[r['Quarter']] += float(r['Revenue_INR'])
best_qtr = max(qtr_rev, key=qtr_rev.get)
print(f'Q3 Highest-revenue quarter: {best_qtr} = {qtr_rev[best_qtr]:,.2f}')
for k, v in sorted(qtr_rev.items()):
    print(f'  {k}: {v:,.2f}')

# Q4: product categories
cats = sorted(set(r['Category'] for r in rows))
print(f'Q4 Product categories: {cats}')

# Q5: discount levels
discounts = sorted(set(float(r['Discount_Pct']) for r in rows))
print(f'Q5 Discount levels: {discounts}%')