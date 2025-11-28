from datetime import date, timedelta

d = date(2025, 12, 1)
for i in range(14):
    current = d + timedelta(days=i)
    print(f"{current.strftime('%Y-%m-%d %A')}")

# Count working days from Dec 1-14
print("\nWorking days (no holidays):")
working_days = 0
for i in range(14):
    current = d + timedelta(days=i)
    if current.weekday() < 5:  # Mon-Fri
        working_days += 1
        print(f"  {current.strftime('%Y-%m-%d %A')}")
print(f"Total: {working_days}")

# Count with Dec 10 as holiday
print("\nWorking days (with Dec 10 holiday):")
holiday = date(2025, 12, 10)
working_days_with_holiday = 0
for i in range(14):
    current = d + timedelta(days=i)
    if current.weekday() < 5 and current != holiday:
        working_days_with_holiday += 1
        print(f"  {current.strftime('%Y-%m-%d %A')}")
print(f"Total: {working_days_with_holiday}")

# Count vacation days Dec 5-6
print("\nVacation days Dec 5-6:")
vac_start = date(2025, 12, 5)
vac_end = date(2025, 12, 6)
vac_days = 0
current = vac_start
while current <= vac_end:
    if current.weekday() < 5:
        vac_days += 1
        print(f"  {current.strftime('%Y-%m-%d %A')}")
    current += timedelta(days=1)
print(f"Total vacation days: {vac_days}")
