import csv
import os
import random
from pathlib import Path


BRANDS = [
    "Apple",
    "Samsung",
    "OnePlus",
    "Xiaomi",
    "Vivo",
    "Oppo",
    "Realme",
    "Motorola",
    "Infinix",
    "Tecno",
]

REGIONS = [
    "Delhi",
    "Maharashtra",
    "Karnataka",
    "Gujarat",
    "Tamil Nadu",
    "Telangana",
    "West Bengal",
    "Uttar Pradesh",
    "Madhya Pradesh",
    "Bihar",
]

CHANNELS = ["Online", "Retail", "Wholesale"]

RAM_OPTIONS = ["4GB", "6GB", "8GB", "12GB", "16GB"]
STORAGE_OPTIONS = ["64GB", "128GB", "256GB", "512GB"]
CAMERA_OPTIONS = ["48MP", "64MP", "108MP", "200MP"]
BATTERY_OPTIONS = ["4000mAh", "4300mAh", "4500mAh", "5000mAh", "5500mAh"]
PROCESSORS = [
    "Snapdragon 695",
    "Snapdragon 7 Gen 1",
    "Snapdragon 8 Gen 1",
    "Snapdragon 8 Gen 2",
    "Dimensity 1080",
    "Dimensity 8200",
    "A15 Bionic",
    "A16 Bionic",
    "A17 Pro",
]
OS_OPTIONS = ["Android 13", "Android 14", "iOS 16", "iOS 17"]
DISPLAY_SIZES = ["6.1\"", "6.4\"", "6.7\"", "6.8\""]
YEARS = [2022, 2023, 2024, 2025]


def generate_models_per_brand(brand: str, count: int) -> list[dict]:
    rows: list[dict] = []
    for idx in range(1, count + 1):
        model = f"{brand[:3].upper()}-{100+idx}"
        ram = random.choice(RAM_OPTIONS)
        storage = random.choice(STORAGE_OPTIONS)
        camera = random.choice(CAMERA_OPTIONS)
        battery = random.choice(BATTERY_OPTIONS)
        processor = random.choice(PROCESSORS)
        os_name = random.choice([o for o in OS_OPTIONS if ("iOS" in o) == (brand == "Apple")] or OS_OPTIONS)
        display = random.choice(DISPLAY_SIZES)
        year = random.choice(YEARS)

        # Price heuristic: Apple higher, value brands lower
        base_price = {
            "Apple": 95000,
            "Samsung": 45000,
            "OnePlus": 42000,
            "Xiaomi": 25000,
            "Vivo": 23000,
            "Oppo": 24000,
            "Realme": 22000,
            "Motorola": 26000,
            "Infinix": 18000,
            "Tecno": 17000,
        }[brand]
        spec_bump = (RAM_OPTIONS.index(ram) + STORAGE_OPTIONS.index(storage)) * 1500
        price = base_price + spec_bump + random.randrange(-3000, 4000, 500)

        # Create multiple regional/channel sales rows per model
        regions = random.sample(REGIONS, k=5)
        for region in regions:
            channel = random.choice(CHANNELS)
            units = random.randint(2000, 20000)
            rows.append(
                {
                    "Brand": brand,
                    "Model": model,
                    "RAM": ram,
                    "Storage": storage,
                    "Camera": camera,
                    "Battery": battery,
                    "Processor": processor,
                    "Price": price,
                    "Units Sold": units,
                    "Region": region,
                    "Channel": channel,
                    "Year": year,
                }
            )
    return rows


def generate_dataset(models_per_brand: int = 40) -> list[dict]:
    dataset: list[dict] = []
    for brand in BRANDS:
        dataset.extend(generate_models_per_brand(brand, models_per_brand))
    return dataset


def main():
    out_dir = Path("data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "mobiles_full.csv"
    rows = generate_dataset(models_per_brand=40)
    fieldnames = [
        "Brand",
        "Model",
        "RAM",
        "Storage",
        "Camera",
        "Battery",
        "Processor",
        "Price",
        "Units Sold",
        "Region",
        "Channel",
        "Year",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()


